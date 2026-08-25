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

// Native token-scope discriminator for Trigger-1.
//
// CASES.tsv fields:
//   case_id<TAB>mode<TAB>cvec_path_or_-<TAB>il_start<TAB>il_end<TAB>primary_layer_inp<TAB>downstream_layer_inp<TAB>prompt_utf8_hex
//
// mode:
//   BASELINE        no cvec, full prompt in one decode
//   BROADCAST       cvec installed before the full prompt decode
//   LAST_TOKEN_ONLY prefix is decoded in a fresh context while NO cvec has ever been
//                   installed; cvec is installed only after the prefix has completed,
//                   then exactly the final prompt token is decoded.
//
// This makes the causal token scope observable rather than inferred from an API name.
// It deliberately does NOT assert that BROADCAST and LAST_TOKEN_ONLY have identical
// downstream causal effects; it provides the measurements needed to test that separately.

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

static std::vector<llama_token> tokenize(
    const llama_vocab * vocab,
    const std::string & text,
    bool add_special
) {
    int32_t n = llama_tokenize(
        vocab, text.c_str(), static_cast<int32_t>(text.size()), nullptr, 0, add_special, true
    );
    if (n >= 0) throw std::runtime_error("TOKENIZE_SIZE_PROBE_DID_NOT_RETURN_NEGATIVE_REQUIRED_SIZE");
    std::vector<llama_token> tokens(static_cast<size_t>(-n));
    n = llama_tokenize(
        vocab, text.c_str(), static_cast<int32_t>(text.size()),
        tokens.data(), static_cast<int32_t>(tokens.size()), add_special, true
    );
    if (n < 0) throw std::runtime_error("TOKENIZE_FAILED");
    tokens.resize(static_cast<size_t>(n));
    return tokens;
}

static std::vector<llama_token> tokenize_one(const llama_vocab * vocab, const std::string & text) {
    auto tokens = tokenize(vocab, text, false);
    return tokens.size() == 1 ? tokens : std::vector<llama_token>{};
}

struct TokenTriplet {
    llama_token a;
    llama_token b;
    llama_token c;
    std::string a_text;
    std::string b_text;
    std::string c_text;
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
                } else {
                    out << static_cast<char>(ch);
                }
        }
    }
    out << '"';
}

static double l2_norm(const float * row, int32_t n_embd) {
    long double sum = 0.0L;
    for (int32_t i = 0; i < n_embd; ++i) {
        const long double x = static_cast<long double>(row[i]);
        sum += x * x;
    }
    return std::sqrt(static_cast<double>(sum));
}

static void json_f32_row(std::ostream & out, const float * row, int32_t n_embd) {
    out << '[';
    for (int32_t i = 0; i < n_embd; ++i) {
        if (i) out << ',';
        const float value = row[i];
        if (!std::isfinite(value)) throw std::runtime_error("NONFINITE_LAYER_ACTIVATION");
        out << static_cast<double>(value);
    }
    out << ']';
}

static const float * captured_last_row(
    llama_context * ctx,
    int32_t layer,
    size_t rows_in_final_decode,
    int32_t n_embd
) {
    float * base = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(layer));
    if (!base) throw std::runtime_error("LAYER_INPUT_UNAVAILABLE:" + std::to_string(layer));
    if (rows_in_final_decode == 0) throw std::runtime_error("FINAL_DECODE_ROW_COUNT_ZERO");
    return base + (rows_in_final_decode - 1) * static_cast<size_t>(n_embd);
}

static void install_cvec(
    llama_context * ctx,
    const std::vector<float> & cvec,
    int32_t n_embd,
    int32_t il_start,
    int32_t il_end
) {
    const int32_t rc = llama_set_adapter_cvec(
        ctx, const_cast<float *>(cvec.data()), cvec.size(), n_embd, il_start, il_end
    );
    if (rc != 0) throw std::runtime_error("LLAMA_SET_ADAPTER_CVEC_FAILED:" + std::to_string(rc));
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
    if (n_embd <= 0 || n_layer <= 1) {
        std::cerr << "MODEL_DIMENSIONS_INVALID\n";
        return 64;
    }

    llama_log_set([](enum ggml_log_level level, const char * text, void *) {
        if (level >= GGML_LOG_LEVEL_ERROR) std::fputs(text, stderr);
    }, nullptr);
    ggml_backend_load_all();
    llama_backend_init();

    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 0;
    llama_model * model = llama_model_load_from_file(model_path.c_str(), mparams);
    if (!model) {
        std::cerr << "MODEL_LOAD_FAILED\n";
        return 65;
    }
    const llama_vocab * vocab = llama_model_get_vocab(model);
    if (!vocab) {
        std::cerr << "VOCAB_UNAVAILABLE\n";
        llama_model_free(model);
        llama_backend_free();
        return 66;
    }

    TokenTriplet triplet;
    try {
        triplet = resolve_triplet(vocab);
    } catch (const std::exception & e) {
        std::cerr << e.what() << "\n";
        llama_model_free(model);
        llama_backend_free();
        return 67;
    }

    std::cout << std::setprecision(17);
    std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_PROBE_HEADER/v1\",\"token_ids\":{\"A\":"
              << triplet.a << ",\"B\":" << triplet.b << ",\"C\":" << triplet.c
              << "},\"native_api\":\"llama_set_adapter_cvec\",\"scope_modes\":[\"BASELINE\",\"BROADCAST\",\"LAST_TOKEN_ONLY\"]}\n";

    std::ifstream cases(cases_path);
    if (!cases) {
        std::cerr << "CASES_OPEN_FAILED\n";
        llama_model_free(model);
        llama_backend_free();
        return 68;
    }

    std::string line;
    size_t line_no = 0;
    while (std::getline(cases, line)) {
        ++line_no;
        if (line.empty()) continue;
        llama_context * ctx = nullptr;
        try {
            const auto parts = split_tabs(line);
            if (parts.size() != 8) throw std::runtime_error("CASE_FIELD_COUNT_INVALID");
            const std::string case_id = parts[0];
            const std::string mode = parts[1];
            const std::string cvec_path = parts[2];
            const int32_t il_start = std::stoi(parts[3]);
            const int32_t il_end = std::stoi(parts[4]);
            const int32_t primary_layer = std::stoi(parts[5]);
            const int32_t downstream_layer = std::stoi(parts[6]);
            const std::string prompt = hex_decode(parts[7]);

            if (case_id.empty()) throw std::runtime_error("CASE_ID_REQUIRED");
            if (mode != "BASELINE" && mode != "BROADCAST" && mode != "LAST_TOKEN_ONLY") {
                throw std::runtime_error("MODE_INVALID:" + mode);
            }
            if (primary_layer < 0 || primary_layer >= n_layer ||
                downstream_layer < 0 || downstream_layer >= n_layer ||
                downstream_layer == primary_layer) {
                throw std::runtime_error("CAPTURE_LAYER_INVALID");
            }
            if ((mode == "BASELINE") != (cvec_path == "-")) {
                throw std::runtime_error("BASELINE_CVEC_PATH_CONTRACT_INVALID");
            }

            std::vector<float> cvec;
            if (mode != "BASELINE") {
                cvec = read_f32(cvec_path);
                const size_t expected = static_cast<size_t>(n_layer - 1) * static_cast<size_t>(n_embd);
                if (cvec.size() != expected) throw std::runtime_error("CVEC_FLOAT_COUNT_MISMATCH");
            }

            const auto tokens = tokenize(vocab, prompt, true);
            if (tokens.size() < 2) throw std::runtime_error("PROMPT_REQUIRES_AT_LEAST_TWO_TOKENS");

            llama_context_params cparams = llama_context_default_params();
            cparams.n_ctx = 256;
            cparams.n_batch = 256;
            cparams.n_ubatch = 256;
            if (tokens.size() > static_cast<size_t>(cparams.n_batch)) {
                throw std::runtime_error("PROMPT_EXCEEDS_SINGLE_UBATCH_SCOPE_CONTRACT");
            }
            ctx = llama_init_from_model(model, cparams);
            if (!ctx) throw std::runtime_error("CONTEXT_INIT_FAILED");
            llama_set_n_threads(ctx, 2, 2);
            llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(primary_layer), true);
            llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(downstream_layer), true);

            bool cvec_before_prefix = false;
            bool cvec_after_prefix = false;
            size_t prefix_decode_tokens = 0;
            size_t final_decode_tokens = 0;
            size_t rows_in_final_decode = 0;

            if (mode == "BROADCAST") {
                install_cvec(ctx, cvec, n_embd, il_start, il_end);
                cvec_before_prefix = true;
                llama_batch batch = llama_batch_get_one(
                    const_cast<llama_token *>(tokens.data()), static_cast<int32_t>(tokens.size())
                );
                const int32_t rc = llama_decode(ctx, batch);
                if (rc != 0) throw std::runtime_error("FULL_PROMPT_DECODE_FAILED:" + std::to_string(rc));
                llama_synchronize(ctx);
                prefix_decode_tokens = tokens.size() - 1;
                final_decode_tokens = 1;
                rows_in_final_decode = tokens.size();
            } else if (mode == "LAST_TOKEN_ONLY") {
                // Critical parity property: prefix is decoded in a brand-new context before
                // llama_set_adapter_cvec has ever been called on that context.
                llama_batch prefix = llama_batch_get_one(
                    const_cast<llama_token *>(tokens.data()), static_cast<int32_t>(tokens.size() - 1)
                );
                const int32_t prefix_rc = llama_decode(ctx, prefix);
                if (prefix_rc != 0) throw std::runtime_error("PREFIX_DECODE_FAILED:" + std::to_string(prefix_rc));
                llama_synchronize(ctx);
                prefix_decode_tokens = tokens.size() - 1;

                install_cvec(ctx, cvec, n_embd, il_start, il_end);
                cvec_after_prefix = true;
                llama_token last = tokens.back();
                llama_batch final_batch = llama_batch_get_one(&last, 1);
                const int32_t final_rc = llama_decode(ctx, final_batch);
                if (final_rc != 0) throw std::runtime_error("FINAL_TOKEN_DECODE_FAILED:" + std::to_string(final_rc));
                llama_synchronize(ctx);
                final_decode_tokens = 1;
                rows_in_final_decode = 1;
            } else {
                llama_batch batch = llama_batch_get_one(
                    const_cast<llama_token *>(tokens.data()), static_cast<int32_t>(tokens.size())
                );
                const int32_t rc = llama_decode(ctx, batch);
                if (rc != 0) throw std::runtime_error("BASELINE_DECODE_FAILED:" + std::to_string(rc));
                llama_synchronize(ctx);
                prefix_decode_tokens = tokens.size() - 1;
                final_decode_tokens = 1;
                rows_in_final_decode = tokens.size();
            }

            const float * primary = captured_last_row(ctx, primary_layer, rows_in_final_decode, n_embd);
            const float * downstream = captured_last_row(ctx, downstream_layer, rows_in_final_decode, n_embd);
            float * logits = llama_get_logits_ith(ctx, -1);
            if (!logits) throw std::runtime_error("LOGITS_UNAVAILABLE");

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_PROBE_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout << ",\"mode\":";
            json_string(std::cout, mode);
            std::cout
                << ",\"token_scope\":";
            json_string(std::cout,
                mode == "BROADCAST" ? "ALL_PROMPT_TOKENS" :
                mode == "LAST_TOKEN_ONLY" ? "LAST_TOKEN_DECODE_ONLY" : "NO_INTERVENTION"
            );
            std::cout
                << ",\"prompt_tokens\":" << tokens.size()
                << ",\"prefix_decode_tokens\":" << prefix_decode_tokens
                << ",\"final_decode_tokens\":" << final_decode_tokens
                << ",\"cvec_set_before_prefix\":" << (cvec_before_prefix ? "true" : "false")
                << ",\"cvec_set_after_prefix\":" << (cvec_after_prefix ? "true" : "false")
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
                << ",\"token_logits\":{\"A\":" << static_cast<double>(logits[triplet.a])
                << ",\"B\":" << static_cast<double>(logits[triplet.b])
                << ",\"C\":" << static_cast<double>(logits[triplet.c]) << "}}\n";

            llama_free(ctx);
            ctx = nullptr;
        } catch (const std::exception & e) {
            if (ctx) llama_free(ctx);
            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_PROBE_ERROR/v1\",\"line_no\":"
                      << line_no << ",\"error\":";
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
