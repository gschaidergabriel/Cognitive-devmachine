#include "llama.h"
#include "ggml-backend.h"

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

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
            return parts;
        }
        parts.push_back(line.substr(start, pos - start));
        start = pos + 1;
    }
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
    auto out = tokenize(vocab, text, false);
    if (out.size() != 1) return {};
    return out;
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

enum class PositionMode {
    BASELINE_FULL,
    BASELINE_SPLIT,
    BROADCAST_FULL,
    BROADCAST_SPLIT,
    LAST_TOKEN_ONLY_SPLIT,
    PREFIX_ONLY_SPLIT,
};

static PositionMode parse_mode(const std::string & value) {
    if (value == "BASELINE_FULL") return PositionMode::BASELINE_FULL;
    if (value == "BASELINE_SPLIT") return PositionMode::BASELINE_SPLIT;
    if (value == "BROADCAST_FULL") return PositionMode::BROADCAST_FULL;
    if (value == "BROADCAST_SPLIT") return PositionMode::BROADCAST_SPLIT;
    if (value == "LAST_TOKEN_ONLY_SPLIT") return PositionMode::LAST_TOKEN_ONLY_SPLIT;
    if (value == "PREFIX_ONLY_SPLIT") return PositionMode::PREFIX_ONLY_SPLIT;
    throw std::runtime_error("POSITION_MODE_INVALID:" + value);
}

static bool is_split(PositionMode mode) {
    return mode == PositionMode::BASELINE_SPLIT || mode == PositionMode::BROADCAST_SPLIT ||
           mode == PositionMode::LAST_TOKEN_ONLY_SPLIT || mode == PositionMode::PREFIX_ONLY_SPLIT;
}

static bool requires_cvec(PositionMode mode) {
    return mode == PositionMode::BROADCAST_FULL || mode == PositionMode::BROADCAST_SPLIT ||
           mode == PositionMode::LAST_TOKEN_ONLY_SPLIT || mode == PositionMode::PREFIX_ONLY_SPLIT;
}

static int32_t decode_tokens(llama_context * ctx, llama_token * data, int32_t n) {
    llama_batch batch = llama_batch_get_one(data, n);
    return llama_decode(ctx, batch);
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
        return 66;
    }

    TokenTriplet triplet;
    try {
        triplet = resolve_triplet(vocab);
    } catch (const std::exception & e) {
        std::cerr << e.what() << "\n";
        llama_model_free(model);
        return 67;
    }

    std::cout << std::setprecision(17);
    std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_CARRIER_HARNESS_HEADER/v1\",\"supported_position_modes\":["
              << "\"BASELINE_FULL\",\"BASELINE_SPLIT\",\"BROADCAST_FULL\",\"BROADCAST_SPLIT\","
              << "\"LAST_TOKEN_ONLY_SPLIT\",\"PREFIX_ONLY_SPLIT\"],\"token_ids\":{\"A\":"
              << triplet.a << ",\"B\":" << triplet.b << ",\"C\":" << triplet.c << "},\"token_texts\":{\"A\":";
    json_string(std::cout, triplet.a_text);
    std::cout << ",\"B\":"; json_string(std::cout, triplet.b_text);
    std::cout << ",\"C\":"; json_string(std::cout, triplet.c_text);
    std::cout << "}}\n";

    std::ifstream cases(cases_path);
    if (!cases) {
        std::cerr << "CASES_OPEN_FAILED\n";
        llama_model_free(model);
        return 68;
    }

    std::string line;
    size_t line_no = 0;
    while (std::getline(cases, line)) {
        ++line_no;
        if (line.empty()) continue;
        try {
            const auto parts = split_tabs(line);
            if (parts.size() != 8) throw std::runtime_error("CASE_FIELD_COUNT_INVALID_EXPECT_8");
            const std::string case_id = parts[0];
            const std::string semantic_target = parts[1];
            const std::string output_code_identity = parts[2];
            const std::string cvec_path = parts[3];
            const int32_t il_start = std::stoi(parts[4]);
            const int32_t il_end = std::stoi(parts[5]);
            const std::string mode_text = parts[6];
            const PositionMode mode = parse_mode(mode_text);
            const std::string prompt = hex_decode(parts[7]);

            if (case_id.empty()) throw std::runtime_error("CASE_ID_REQUIRED");
            if (semantic_target.empty()) throw std::runtime_error("SEMANTIC_TARGET_REQUIRED");
            if (output_code_identity != "A" && output_code_identity != "B" && output_code_identity != "C") {
                throw std::runtime_error("OUTPUT_CODE_IDENTITY_INVALID");
            }
            if (requires_cvec(mode) && cvec_path == "-") throw std::runtime_error("CVEC_REQUIRED_FOR_MODE");
            if (!requires_cvec(mode) && cvec_path != "-") throw std::runtime_error("CVEC_FORBIDDEN_FOR_BASELINE_MODE");

            llama_context_params cparams = llama_context_default_params();
            cparams.n_ctx = 256;
            cparams.n_batch = 256;
            cparams.n_ubatch = 256;
            llama_context * ctx = llama_init_from_model(model, cparams);
            if (!ctx) throw std::runtime_error("CONTEXT_INIT_FAILED");
            llama_set_n_threads(ctx, 2, 2);

            std::vector<float> cvec;
            size_t cvec_float_count = 0;
            if (requires_cvec(mode)) {
                cvec = read_f32(cvec_path);
                cvec_float_count = cvec.size();
                const size_t expected = static_cast<size_t>(n_layer - 1) * static_cast<size_t>(n_embd);
                if (cvec.size() != expected) {
                    llama_free(ctx);
                    throw std::runtime_error("CVEC_FLOAT_COUNT_MISMATCH");
                }
            }

            int32_t cvec_set_calls = 0;
            int32_t cvec_clear_calls = 0;
            auto set_cvec = [&]() {
                const int32_t rc = llama_set_adapter_cvec(ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end);
                ++cvec_set_calls;
                if (rc != 0) throw std::runtime_error("LLAMA_SET_ADAPTER_CVEC_FAILED:" + std::to_string(rc));
            };
            auto clear_cvec = [&]() {
                const int32_t rc = llama_set_adapter_cvec(ctx, nullptr, 0, n_embd, il_start, il_end);
                ++cvec_clear_calls;
                if (rc != 0) throw std::runtime_error("LLAMA_CLEAR_ADAPTER_CVEC_FAILED:" + std::to_string(rc));
            };

            std::vector<llama_token> tokens = tokenize(vocab, prompt, true);
            if (tokens.empty()) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_TOKENIZATION_EMPTY");
            }
            if (is_split(mode) && tokens.size() < 2) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_TOO_SHORT_FOR_SPLIT_MODE");
            }

            int32_t decode_calls = 0;
            const int32_t prefix_tokens = is_split(mode) ? static_cast<int32_t>(tokens.size() - 1) : 0;
            auto decode_checked = [&](llama_token * data, int32_t n) {
                const int32_t rc = decode_tokens(ctx, data, n);
                ++decode_calls;
                if (rc != 0) throw std::runtime_error("LLAMA_DECODE_FAILED:" + std::to_string(rc));
            };

            if (mode == PositionMode::BASELINE_FULL) {
                decode_checked(tokens.data(), static_cast<int32_t>(tokens.size()));
            } else if (mode == PositionMode::BROADCAST_FULL) {
                set_cvec();
                decode_checked(tokens.data(), static_cast<int32_t>(tokens.size()));
            } else if (mode == PositionMode::BASELINE_SPLIT) {
                decode_checked(tokens.data(), prefix_tokens);
                llama_synchronize(ctx);
                decode_checked(tokens.data() + prefix_tokens, 1);
            } else if (mode == PositionMode::BROADCAST_SPLIT) {
                set_cvec();
                decode_checked(tokens.data(), prefix_tokens);
                llama_synchronize(ctx);
                decode_checked(tokens.data() + prefix_tokens, 1);
            } else if (mode == PositionMode::LAST_TOKEN_ONLY_SPLIT) {
                decode_checked(tokens.data(), prefix_tokens);
                llama_synchronize(ctx);
                set_cvec();
                decode_checked(tokens.data() + prefix_tokens, 1);
            } else if (mode == PositionMode::PREFIX_ONLY_SPLIT) {
                set_cvec();
                decode_checked(tokens.data(), prefix_tokens);
                llama_synchronize(ctx);
                clear_cvec();
                decode_checked(tokens.data() + prefix_tokens, 1);
            }

            llama_synchronize(ctx);
            float * logits = llama_get_logits_ith(ctx, -1);
            if (!logits) {
                llama_free(ctx);
                throw std::runtime_error("LOGITS_UNAVAILABLE");
            }
            const double la = static_cast<double>(logits[triplet.a]);
            const double lb = static_cast<double>(logits[triplet.b]);
            const double lc = static_cast<double>(logits[triplet.c]);

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_CARRIER_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout << ",\"semantic_target\":"; json_string(std::cout, semantic_target);
            std::cout << ",\"output_code_identity\":"; json_string(std::cout, output_code_identity);
            std::cout << ",\"position_mode\":"; json_string(std::cout, mode_text);
            std::cout << ",\"batch_schedule\":";
            json_string(std::cout, is_split(mode) ? "PREFIX_THEN_LAST" : "FULL");
            std::cout << ",\"prompt_tokens\":" << tokens.size()
                      << ",\"prefix_tokens\":" << prefix_tokens
                      << ",\"decode_calls\":" << decode_calls
                      << ",\"cvec_float_count\":" << cvec_float_count
                      << ",\"cvec_set_calls\":" << cvec_set_calls
                      << ",\"cvec_clear_calls\":" << cvec_clear_calls
                      << ",\"il_start\":" << il_start << ",\"il_end\":" << il_end
                      << ",\"token_logits\":{\"A\":" << la << ",\"B\":" << lb << ",\"C\":" << lc << "}}\n";
            llama_free(ctx);
        } catch (const std::exception & e) {
            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_CARRIER_OBSERVATION_ERROR/v1\",\"line_no\":" << line_no << ",\"error\":";
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
