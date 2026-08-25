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

// Native temporal-scope discriminator for Trigger-1 Qwen3-0.6B cvec steering.
//
// CASES.tsv fields:
//   case_id<TAB>mode<TAB>cvec_path_or_-<TAB>il_start<TAB>il_end<TAB>
//   primary_layer_inp<TAB>downstream_layer_inp<TAB>target_code(A|B|C)<TAB>prompt_utf8_hex
//
// Modes deliberately separate intervention scope without changing the native cvec API:
//   BASELINE_SINGLE   : no cvec; whole prompt in one decode
//   BASELINE_SPLIT    : no cvec; prefix then last prompt token
//   BROADCAST_SINGLE  : cvec set before whole-prompt decode
//   BROADCAST_SPLIT   : cvec set before prefix and remains active for last token
//   LAST_TOKEN_ONLY   : prefix decoded without cvec; cvec set only before last token
//   PREFIX_ONLY       : cvec set before prefix; cleared via NULL-data API before last token
//
// The two single/split pairs quantify batch-partition drift. LAST_TOKEN_ONLY vs
// BROADCAST_SPLIT measures last-token recovery; PREFIX_ONLY tests whether prefix-wide
// intervention is itself sufficient. All active arms use the exact same cvec bytes for
// a given semantic target, layer range, model and context configuration.

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
    n = llama_tokenize(vocab, text.c_str(), static_cast<int32_t>(text.size()), tokens.data(), static_cast<int32_t>(tokens.size()), add_special, true);
    if (n < 0) throw std::runtime_error("TOKENIZE_FAILED");
    tokens.resize(static_cast<size_t>(n));
    return tokens;
}

static std::vector<llama_token> tokenize_one(const llama_vocab * vocab, const std::string & text) {
    auto v = tokenize(vocab, text, false);
    return v.size() == 1 ? v : std::vector<llama_token>{};
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
        if (a.size() == 1 && b.size() == 1 && d.size() == 1 && a[0] != b[0] && a[0] != d[0] && b[0] != d[0]) {
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
        if (!std::isfinite(row[i])) throw std::runtime_error("NONFINITE_LAYER_ACTIVATION");
        out << static_cast<double>(row[i]);
    }
    out << ']';
}

static const float * current_batch_last_row(llama_context * ctx, int32_t layer, size_t current_batch_tokens, int32_t n_embd) {
    float * base = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(layer));
    if (!base) throw std::runtime_error("LAYER_INPUT_UNAVAILABLE:" + std::to_string(layer));
    return base + (current_batch_tokens - 1) * static_cast<size_t>(n_embd);
}

static int32_t decode_tokens(llama_context * ctx, std::vector<llama_token> & tokens) {
    if (tokens.empty()) throw std::runtime_error("DECODE_TOKEN_SLICE_EMPTY");
    llama_batch batch = llama_batch_get_one(tokens.data(), static_cast<int32_t>(tokens.size()));
    return llama_decode(ctx, batch);
}

static bool is_mode(const std::string & mode) {
    return mode == "BASELINE_SINGLE" || mode == "BASELINE_SPLIT" ||
           mode == "BROADCAST_SINGLE" || mode == "BROADCAST_SPLIT" ||
           mode == "LAST_TOKEN_ONLY" || mode == "PREFIX_ONLY";
}

static bool active_mode(const std::string & mode) {
    return mode == "BROADCAST_SINGLE" || mode == "BROADCAST_SPLIT" ||
           mode == "LAST_TOKEN_ONLY" || mode == "PREFIX_ONLY";
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
    if (!model) { std::cerr << "MODEL_LOAD_FAILED\n"; return 65; }
    const llama_vocab * vocab = llama_model_get_vocab(model);
    if (!vocab) { llama_model_free(model); llama_backend_free(); return 66; }

    TokenTriplet triplet;
    try { triplet = resolve_triplet(vocab); }
    catch (const std::exception & e) {
        std::cerr << e.what() << "\n";
        llama_model_free(model); llama_backend_free(); return 67;
    }

    std::cout << std::setprecision(17);
    std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_TEMPORAL_SCOPE_HEADER/v1\","
              << "\"modes\":[\"BASELINE_SINGLE\",\"BASELINE_SPLIT\",\"BROADCAST_SINGLE\",\"BROADCAST_SPLIT\",\"LAST_TOKEN_ONLY\",\"PREFIX_ONLY\"],"
              << "\"clear_semantics\":\"llama_set_adapter_cvec_NULL_data\",\"token_ids\":{\"A\":"
              << triplet.a << ",\"B\":" << triplet.b << ",\"C\":" << triplet.c << "}}\n";

    std::ifstream cases(cases_path);
    if (!cases) { llama_model_free(model); llama_backend_free(); return 68; }
    std::string line;
    size_t line_no = 0;
    while (std::getline(cases, line)) {
        ++line_no;
        if (line.empty()) continue;
        try {
            const auto parts = split_tabs(line);
            if (parts.size() != 9) throw std::runtime_error("CASE_FIELD_COUNT_INVALID");
            const std::string case_id = parts[0];
            const std::string mode = parts[1];
            const std::string cvec_path = parts[2];
            const int32_t il_start = std::stoi(parts[3]);
            const int32_t il_end = std::stoi(parts[4]);
            const int32_t primary_layer = std::stoi(parts[5]);
            const int32_t downstream_layer = std::stoi(parts[6]);
            const std::string target_code = parts[7];
            const std::string prompt = hex_decode(parts[8]);
            if (!is_mode(mode)) throw std::runtime_error("TEMPORAL_MODE_INVALID");
            if (target_code != "A" && target_code != "B" && target_code != "C") throw std::runtime_error("TARGET_CODE_INVALID");
            if (active_mode(mode) && cvec_path == "-") throw std::runtime_error("ACTIVE_MODE_REQUIRES_CVEC");
            if (!active_mode(mode) && cvec_path != "-") throw std::runtime_error("BASELINE_MODE_FORBIDS_CVEC");
            if (primary_layer < 0 || downstream_layer < 0 || primary_layer >= n_layer || downstream_layer >= n_layer || primary_layer == downstream_layer) {
                throw std::runtime_error("CAPTURE_LAYER_INVALID");
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

            std::vector<float> cvec;
            if (active_mode(mode)) {
                cvec = read_f32(cvec_path);
                const size_t expected = static_cast<size_t>(n_layer - 1) * static_cast<size_t>(n_embd);
                if (cvec.size() != expected) { llama_free(ctx); throw std::runtime_error("CVEC_FLOAT_COUNT_MISMATCH"); }
            }
            auto set_cvec = [&]() -> int32_t {
                const int32_t rc = llama_set_adapter_cvec(ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end);
                if (rc != 0) throw std::runtime_error("LLAMA_SET_ADAPTER_CVEC_FAILED:" + std::to_string(rc));
                return rc;
            };
            auto clear_cvec = [&]() -> int32_t {
                const int32_t rc = llama_set_adapter_cvec(ctx, nullptr, 0, n_embd, il_start, il_end);
                if (rc != 0) throw std::runtime_error("LLAMA_CLEAR_ADAPTER_CVEC_FAILED:" + std::to_string(rc));
                return rc;
            };

            std::vector<llama_token> tokens = tokenize(vocab, prompt, true);
            if (tokens.size() < 2) { llama_free(ctx); throw std::runtime_error("PROMPT_REQUIRES_PREFIX_AND_LAST_TOKEN"); }
            if (tokens.size() > static_cast<size_t>(cparams.n_batch)) { llama_free(ctx); throw std::runtime_error("PROMPT_EXCEEDS_BATCH_CONTRACT"); }

            int32_t set_rc = -1;
            int32_t clear_rc = -1;
            int32_t prefix_decode_rc = -1;
            int32_t last_decode_rc = -1;
            size_t final_batch_tokens = 0;

            if (mode == "BASELINE_SINGLE" || mode == "BROADCAST_SINGLE") {
                if (mode == "BROADCAST_SINGLE") set_rc = set_cvec();
                last_decode_rc = decode_tokens(ctx, tokens);
                if (last_decode_rc != 0) throw std::runtime_error("SINGLE_DECODE_FAILED:" + std::to_string(last_decode_rc));
                final_batch_tokens = tokens.size();
            } else {
                std::vector<llama_token> prefix(tokens.begin(), tokens.end() - 1);
                std::vector<llama_token> last{tokens.back()};
                if (mode == "BROADCAST_SPLIT" || mode == "PREFIX_ONLY") set_rc = set_cvec();
                prefix_decode_rc = decode_tokens(ctx, prefix);
                if (prefix_decode_rc != 0) throw std::runtime_error("PREFIX_DECODE_FAILED:" + std::to_string(prefix_decode_rc));
                if (mode == "LAST_TOKEN_ONLY") set_rc = set_cvec();
                if (mode == "PREFIX_ONLY") clear_rc = clear_cvec();
                last_decode_rc = decode_tokens(ctx, last);
                if (last_decode_rc != 0) throw std::runtime_error("LAST_TOKEN_DECODE_FAILED:" + std::to_string(last_decode_rc));
                final_batch_tokens = 1;
            }
            llama_synchronize(ctx);

            const float * primary = current_batch_last_row(ctx, primary_layer, final_batch_tokens, n_embd);
            const float * downstream = current_batch_last_row(ctx, downstream_layer, final_batch_tokens, n_embd);
            float * logits = llama_get_logits_ith(ctx, -1);
            if (!logits) { llama_free(ctx); throw std::runtime_error("LOGITS_UNAVAILABLE"); }
            const double la = static_cast<double>(logits[triplet.a]);
            const double lb = static_cast<double>(logits[triplet.b]);
            const double lc = static_cast<double>(logits[triplet.c]);
            double target = la;
            double other1 = lb;
            double other2 = lc;
            if (target_code == "B") { target = lb; other1 = la; other2 = lc; }
            if (target_code == "C") { target = lc; other1 = la; other2 = lb; }
            const double margin = target - 0.5 * (other1 + other2);

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_TEMPORAL_SCOPE_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout << ",\"mode\":"; json_string(std::cout, mode);
            std::cout << ",\"target_code\":"; json_string(std::cout, target_code);
            std::cout << ",\"prompt_tokens\":" << tokens.size()
                      << ",\"final_batch_tokens\":" << final_batch_tokens
                      << ",\"cvec_float_count\":" << cvec.size()
                      << ",\"set_rc\":" << set_rc
                      << ",\"clear_rc\":" << clear_rc
                      << ",\"prefix_decode_rc\":" << prefix_decode_rc
                      << ",\"last_decode_rc\":" << last_decode_rc
                      << ",\"il_start\":" << il_start << ",\"il_end\":" << il_end
                      << ",\"primary_layer_inp\":" << primary_layer
                      << ",\"primary_l2\":" << l2_norm(primary, n_embd)
                      << ",\"primary_activation\":";
            json_f32_row(std::cout, primary, n_embd);
            std::cout << ",\"downstream_layer_inp\":" << downstream_layer
                      << ",\"downstream_l2\":" << l2_norm(downstream, n_embd)
                      << ",\"downstream_activation\":";
            json_f32_row(std::cout, downstream, n_embd);
            std::cout << ",\"token_logits\":{\"A\":" << la << ",\"B\":" << lb << ",\"C\":" << lc << "}"
                      << ",\"behavior_target_margin\":" << margin << "}\n";
            llama_free(ctx);
        } catch (const std::exception & e) {
            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_TEMPORAL_SCOPE_ERROR/v1\",\"line_no\":" << line_no << ",\"error\":";
            json_string(std::cout, e.what());
            std::cout << "}\n";
            llama_model_free(model); llama_backend_free(); return 70;
        }
    }
    llama_model_free(model);
    llama_backend_free();
    return 0;
}
