#include "llama.h"
#include "llama-ext.h"
#include "ggml-backend.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Trigger-1 native Qwen3 cvec discriminator with last-token positional scope.
//
// CASES.tsv:
//   case_id<TAB>control<TAB>cvec_path_or_-<TAB>il_start<TAB>il_end<TAB>
//   primary_layer_inp<TAB>downstream_layer_inp<TAB>prompt_utf8_hex
//
// Critical semantics:
//   * tokenize the full prompt exactly once;
//   * decode tokens[0:-1] with no cvec installed;
//   * only after prefill, install cvec;
//   * decode tokens[-1] as a one-token batch;
//   * capture the current one-token layer-input rows and logits.
//
// This removes the old multi-token-prefill broadcast confound. It does NOT claim
// numerical/mechanistic identity with PyTorch; it gives native Q8 its own
// position-scoped causal witness.

static std::string hex_decode(const std::string & hex) {
    if (hex.size() % 2 != 0) throw std::runtime_error("PROMPT_HEX_ODD_LENGTH");
    std::string out;
    out.reserve(hex.size() / 2);
    for (size_t i = 0; i < hex.size(); i += 2) {
        unsigned value = 0;
        std::istringstream ss(hex.substr(i, 2));
        ss >> std::hex >> value;
        if (ss.fail()) throw std::runtime_error("PROMPT_HEX_INVALID");
        out.push_back(static_cast<char>(value));
    }
    return out;
}

static std::vector<float> read_f32(const std::string & path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in) throw std::runtime_error("CVEC_FILE_OPEN_FAILED:" + path);
    const std::streamsize size = in.tellg();
    if (size < 0 || size % static_cast<std::streamsize>(sizeof(float)) != 0) {
        throw std::runtime_error("CVEC_FILE_SIZE_INVALID:" + path);
    }
    in.seekg(0, std::ios::beg);
    std::vector<float> data(static_cast<size_t>(size) / sizeof(float));
    if (size && !in.read(reinterpret_cast<char *>(data.data()), size)) {
        throw std::runtime_error("CVEC_FILE_READ_FAILED:" + path);
    }
    return data;
}

static std::vector<llama_token> tokenize(const llama_vocab * vocab, const std::string & text, bool add_special) {
    int32_t n = llama_tokenize(vocab, text.c_str(), static_cast<int32_t>(text.size()), nullptr, 0, add_special, true);
    if (n >= 0) throw std::runtime_error("TOKENIZE_SIZE_PROBE_DID_NOT_RETURN_NEGATIVE_REQUIRED_SIZE");
    std::vector<llama_token> tokens(static_cast<size_t>(-n));
    n = llama_tokenize(vocab, text.c_str(), static_cast<int32_t>(text.size()),
                       tokens.data(), static_cast<int32_t>(tokens.size()), add_special, true);
    if (n < 0) throw std::runtime_error("TOKENIZE_FAILED");
    tokens.resize(static_cast<size_t>(n));
    return tokens;
}

static std::vector<llama_token> tokenize_one(const llama_vocab * vocab, const std::string & text) {
    auto v = tokenize(vocab, text, false);
    if (v.size() != 1) return {};
    return v;
}

struct TokenTriplet {
    llama_token a, b, c;
    std::string a_text, b_text, c_text;
};

static TokenTriplet resolve_triplet(const llama_vocab * vocab) {
    const std::vector<std::vector<std::string>> candidates = {
        {"A", "B", "C"}, {" A", " B", " C"}, {"1", "2", "3"},
    };
    for (const auto & c : candidates) {
        auto a = tokenize_one(vocab, c[0]);
        auto b = tokenize_one(vocab, c[1]);
        auto d = tokenize_one(vocab, c[2]);
        if (a.size() == 1 && b.size() == 1 && d.size() == 1 &&
            a[0] != b[0] && a[0] != d[0] && b[0] != d[0]) {
            return {a[0], b[0], d[0], c[0], c[1], c[2]};
        }
    }
    throw std::runtime_error("NO_DISTINCT_SINGLE_TOKEN_ABC_TRIPLET");
}

static std::vector<std::string> split_tabs(const std::string & line) {
    std::vector<std::string> parts;
    size_t start = 0;
    while (true) {
        const size_t pos = line.find('\t', start);
        if (pos == std::string::npos) {
            parts.push_back(line.substr(start));
            break;
        }
        parts.push_back(line.substr(start, pos - start));
        start = pos + 1;
    }
    return parts;
}

static void json_string(std::ostream & out, const std::string & s) {
    out << '"';
    for (unsigned char ch : s) {
        switch (ch) {
            case '"': out << "\\\""; break;
            case '\\': out << "\\\\"; break;
            case '\b': out << "\\b"; break;
            case '\f': out << "\\f"; break;
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (ch < 0x20) {
                    const char * digits = "0123456789abcdef";
                    out << "\\u00" << digits[(ch >> 4) & 0xf] << digits[ch & 0xf];
                } else out << static_cast<char>(ch);
        }
    }
    out << '"';
}

static void json_f32_row(std::ostream & out, const float * row, int32_t n_embd) {
    out << '[';
    for (int32_t i = 0; i < n_embd; ++i) {
        if (i) out << ',';
        const float v = row[i];
        if (!std::isfinite(v)) throw std::runtime_error("NONFINITE_LAYER_ACTIVATION");
        out << static_cast<double>(v);
    }
    out << ']';
}

static double l2_norm(const float * row, int32_t n_embd) {
    long double sum = 0.0L;
    for (int32_t i = 0; i < n_embd; ++i) {
        const long double x = static_cast<long double>(row[i]);
        sum += x*x;
    }
    return std::sqrt(static_cast<double>(sum));
}

int main(int argc, char ** argv) {
    if (argc != 5) {
        std::cerr << "usage: " << argv[0] << " MODEL.gguf CASES.tsv N_EMBD N_LAYER\n";
        return 64;
    }
    const std::string model_path = argv[1];
    const std::string cases_path = argv[2];
    const int32_t n_embd = std::stoi(argv[3]);
    const int32_t n_layer = std::stoi(argv[4]);
    if (n_embd <= 0 || n_layer <= 1) return 64;

    llama_log_set([](enum ggml_log_level level, const char * text, void *) {
        if (level >= GGML_LOG_LEVEL_ERROR) std::fputs(text, stderr);
    }, nullptr);
    ggml_backend_load_all();
    llama_backend_init();

    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;
    llama_model * model = llama_model_load_from_file(model_path.c_str(), mparams);
    if (!model) return 65;
    const llama_vocab * vocab = llama_model_get_vocab(model);
    if (!vocab) {
        llama_model_free(model);
        llama_backend_free();
        return 66;
    }

    TokenTriplet triplet;
    try { triplet = resolve_triplet(vocab); }
    catch (const std::exception & e) {
        std::cerr << e.what() << "\n";
        llama_model_free(model);
        llama_backend_free();
        return 67;
    }

    std::cout << std::setprecision(17);
    std::cout
        << "{\"schema\":\"CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_HEADER/v1\""
        << ",\"position_scope\":\"POST_UNSTEERED_PREFILL_ORIGINAL_LAST_PROMPT_TOKEN_ONLY\""
        << ",\"token_ids\":{\"A\":" << triplet.a << ",\"B\":" << triplet.b << ",\"C\":" << triplet.c << "}"
        << ",\"token_texts\":{\"A\":";
    json_string(std::cout, triplet.a_text);
    std::cout << ",\"B\":";
    json_string(std::cout, triplet.b_text);
    std::cout << ",\"C\":";
    json_string(std::cout, triplet.c_text);
    std::cout << "}}\n";

    std::ifstream cases(cases_path);
    if (!cases) {
        llama_model_free(model);
        llama_backend_free();
        return 68;
    }

    std::string line;
    size_t line_no = 0;
    while (std::getline(cases, line)) {
        ++line_no;
        if (line.empty()) continue;
        try {
            const auto parts = split_tabs(line);
            if (parts.size() != 8) throw std::runtime_error("CASE_FIELD_COUNT_INVALID");
            const std::string case_id = parts[0];
            const std::string control = parts[1];
            const std::string cvec_path = parts[2];
            const int32_t il_start = std::stoi(parts[3]);
            const int32_t il_end = std::stoi(parts[4]);
            const int32_t primary_layer = std::stoi(parts[5]);
            const int32_t downstream_layer = std::stoi(parts[6]);
            const std::string prompt_hex = parts[7];
            const std::string prompt = hex_decode(prompt_hex);

            if (case_id.empty() || control.empty()) throw std::runtime_error("CASE_ID_AND_CONTROL_REQUIRED");
            if (primary_layer < 0 || primary_layer >= n_layer) throw std::runtime_error("PRIMARY_LAYER_OUT_OF_RANGE");
            if (downstream_layer < 0 || downstream_layer >= n_layer || downstream_layer == primary_layer) {
                throw std::runtime_error("DOWNSTREAM_LAYER_INVALID");
            }

            llama_context_params cparams = llama_context_default_params();
            cparams.n_ctx = 256;
            cparams.n_batch = 256;
            cparams.n_ubatch = 256;
            llama_context * ctx = llama_init_from_model(model, cparams);
            if (!ctx) throw std::runtime_error("CONTEXT_INIT_FAILED");
            llama_set_n_threads(ctx, 2, 2);
            llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(primary_layer), true);
            llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(downstream_layer), true);

            const std::vector<llama_token> full_tokens = tokenize(vocab, prompt, true);
            if (full_tokens.size() < 2) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_MUST_HAVE_AT_LEAST_TWO_TOKENS");
            }
            if (full_tokens.size() > static_cast<size_t>(cparams.n_batch)) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_EXCEEDS_SINGLE_PREFILL_BATCH_CONTRACT");
            }

            // Phase 1: exact original prompt prefix, explicitly before any cvec installation.
            std::vector<llama_token> prefix(full_tokens.begin(), full_tokens.end() - 1);
            llama_batch prefill_batch = llama_batch_get_one(prefix.data(), static_cast<int32_t>(prefix.size()));
            const int32_t prefill_rc = llama_decode(ctx, prefill_batch);
            if (prefill_rc != 0) {
                llama_free(ctx);
                throw std::runtime_error("PREFILL_DECODE_FAILED:" + std::to_string(prefill_rc));
            }
            llama_synchronize(ctx);

            // Phase 2: install cvec only now. The next graph contains exactly one token.
            bool cvec_applied = false;
            int32_t cvec_rc = 0;
            size_t cvec_float_count = 0;
            if (cvec_path != "-") {
                std::vector<float> cvec = read_f32(cvec_path);
                cvec_float_count = cvec.size();
                const size_t expected = static_cast<size_t>(n_layer - 1) * static_cast<size_t>(n_embd);
                if (cvec.size() != expected) {
                    llama_free(ctx);
                    throw std::runtime_error("CVEC_FLOAT_COUNT_MISMATCH");
                }
                cvec_rc = llama_set_adapter_cvec(ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end);
                cvec_applied = true;
                if (cvec_rc != 0) {
                    llama_free(ctx);
                    throw std::runtime_error("LLAMA_SET_ADAPTER_CVEC_FAILED:" + std::to_string(cvec_rc));
                }
            }

            llama_token probe = full_tokens.back();
            llama_batch probe_batch = llama_batch_get_one(&probe, 1);
            const int32_t probe_rc = llama_decode(ctx, probe_batch);
            if (probe_rc != 0) {
                llama_free(ctx);
                throw std::runtime_error("PROBE_DECODE_FAILED:" + std::to_string(probe_rc));
            }
            llama_synchronize(ctx);

            float * primary = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(primary_layer));
            float * downstream = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(downstream_layer));
            if (!primary || !downstream) {
                llama_free(ctx);
                throw std::runtime_error("LAYER_INPUT_UNAVAILABLE");
            }
            float * logits = llama_get_logits_ith(ctx, -1);
            if (!logits) {
                llama_free(ctx);
                throw std::runtime_error("LOGITS_UNAVAILABLE");
            }
            const double la = static_cast<double>(logits[triplet.a]);
            const double lb = static_cast<double>(logits[triplet.b]);
            const double lc = static_cast<double>(logits[triplet.c]);

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout << ",\"control\":";
            json_string(std::cout, control);
            std::cout << ",\"prompt_utf8_hex\":";
            json_string(std::cout, prompt_hex);
            std::cout
                << ",\"prefill_cvec_applied\":false"
                << ",\"cvec_applied\":" << (cvec_applied ? "true" : "false")
                << ",\"cvec_rc\":" << cvec_rc
                << ",\"cvec_float_count\":" << cvec_float_count
                << ",\"full_prompt_tokens\":" << full_tokens.size()
                << ",\"prefill_tokens\":" << prefix.size()
                << ",\"cvec_active_decode_n_tokens\":1"
                << ",\"probe_token_id\":" << probe
                << ",\"probe_is_original_last_prompt_token\":true"
                << ",\"intervention_position_scope\":\"POST_UNSTEERED_PREFILL_ORIGINAL_LAST_PROMPT_TOKEN_ONLY\""
                << ",\"il_start\":" << il_start
                << ",\"il_end\":" << il_end
                << ",\"primary_layer_inp\":" << primary_layer
                << ",\"primary_l2\":" << l2_norm(primary, n_embd)
                << ",\"primary_activation\":";
            json_f32_row(std::cout, primary, n_embd);
            std::cout
                << ",\"downstream_layer_inp\":" << downstream_layer
                << ",\"downstream_l2\":" << l2_norm(downstream, n_embd)
                << ",\"downstream_activation\":";
            json_f32_row(std::cout, downstream, n_embd);
            std::cout
                << ",\"token_logits\":{\"A\":" << la << ",\"B\":" << lb << ",\"C\":" << lc << "}"
                << "}\n";
            llama_free(ctx);
        } catch (const std::exception & e) {
            std::cout
                << "{\"schema\":\"CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_OBSERVATION_ERROR/v1\""
                << ",\"line_no\":" << line_no << ",\"error\":";
            json_string(std::cout, e.what());
            std::cout << "}\n";
            llama_model_free(model);
            llama_backend_free();
            return 70;
        }
    }

    llama_model_free(model);
    llama_backend_free();
    return 0;
}
