#include "llama.h"
#include "llama-ext.h"
#include "ggml-backend.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Exact-purpose native Qwen3/llama.cpp observation harness for Trigger-1.
//
// CASES.tsv fields:
//   case_id<TAB>cvec_path_or_-<TAB>il_start<TAB>il_end<TAB>primary_layer_inp<TAB>downstream_layer_inp_or_-1<TAB>prompt_utf8_hex
//
// The harness deliberately exports *layer inputs*. In the pinned Qwen3 graph,
// build_cvec(cur, il) runs after layer il and the result becomes inpL for il+1.
// Therefore a cvec applied at il=20 is observed immediately at layer-input 21.
// A later layer-input (for example 24) can be captured simultaneously as a
// nonterminal downstream-transport endpoint.
//
// Output is JSONL. Activation rows are emitted in native F32 values as arrays.
// Hashing/provenance binding is performed by the Python orchestration layer so
// this small C++ harness has no crypto dependency.

static std::string hex_decode(const std::string & hex) {
    if (hex.size() % 2 != 0) {
        throw std::runtime_error("PROMPT_HEX_ODD_LENGTH");
    }
    std::string out;
    out.reserve(hex.size() / 2);
    for (size_t i = 0; i < hex.size(); i += 2) {
        unsigned value = 0;
        std::istringstream ss(hex.substr(i, 2));
        ss >> std::hex >> value;
        if (ss.fail()) {
            throw std::runtime_error("PROMPT_HEX_INVALID");
        }
        out.push_back(static_cast<char>(value));
    }
    return out;
}

static std::vector<float> read_f32(const std::string & path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in) {
        throw std::runtime_error("CVEC_FILE_OPEN_FAILED:" + path);
    }
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
        vocab, text.c_str(), static_cast<int32_t>(text.size()),
        nullptr, 0, add_special, true
    );
    if (n >= 0) {
        throw std::runtime_error("TOKENIZE_SIZE_PROBE_DID_NOT_RETURN_NEGATIVE_REQUIRED_SIZE");
    }
    std::vector<llama_token> tokens(static_cast<size_t>(-n));
    n = llama_tokenize(
        vocab, text.c_str(), static_cast<int32_t>(text.size()),
        tokens.data(), static_cast<int32_t>(tokens.size()),
        add_special, true
    );
    if (n < 0) {
        throw std::runtime_error("TOKENIZE_FAILED");
    }
    tokens.resize(static_cast<size_t>(n));
    return tokens;
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
        if (i) {
            out << ',';
        }
        const float value = row[i];
        if (!std::isfinite(value)) {
            throw std::runtime_error("NONFINITE_LAYER_ACTIVATION");
        }
        out << static_cast<double>(value);
    }
    out << ']';
}

static const float * last_token_row(
    llama_context * ctx,
    int32_t layer,
    size_t n_tokens,
    int32_t n_embd
) {
    float * base = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(layer));
    if (!base) {
        throw std::runtime_error("LAYER_INPUT_UNAVAILABLE:" + std::to_string(layer));
    }
    return base + (n_tokens - 1) * static_cast<size_t>(n_embd);
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
        if (level >= GGML_LOG_LEVEL_ERROR) {
            std::fputs(text, stderr);
        }
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

    std::cout << std::setprecision(17);
    std::cout
        << "{\"schema\":\"CLAY_LLAMA_CPP_LAYER_CAPTURE_HEADER/v1\""
        << ",\"n_embd\":" << n_embd
        << ",\"n_layer\":" << n_layer
        << ",\"capture_semantics\":\"LAYER_INPUT_ROWS_N_TOKENS_X_N_EMBD\""
        << ",\"cvec_semantics\":\"CVEC_AFTER_LAYER_IL_VISIBLE_AT_LAYER_INPUT_IL_PLUS_1\"}"
        << "\n";

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
        if (line.empty()) {
            continue;
        }
        try {
            const auto parts = split_tabs(line);
            if (parts.size() != 7) {
                throw std::runtime_error("CASE_FIELD_COUNT_INVALID");
            }
            const std::string case_id = parts[0];
            const std::string cvec_path = parts[1];
            const int32_t il_start = std::stoi(parts[2]);
            const int32_t il_end = std::stoi(parts[3]);
            const int32_t primary_layer = std::stoi(parts[4]);
            const int32_t downstream_layer = std::stoi(parts[5]);
            const std::string prompt = hex_decode(parts[6]);

            if (case_id.empty()) {
                throw std::runtime_error("CASE_ID_REQUIRED");
            }
            if (primary_layer < 0 || primary_layer >= n_layer) {
                throw std::runtime_error("PRIMARY_LAYER_OUT_OF_RANGE");
            }
            if (downstream_layer >= n_layer || downstream_layer < -1) {
                throw std::runtime_error("DOWNSTREAM_LAYER_OUT_OF_RANGE");
            }
            if (downstream_layer == primary_layer) {
                throw std::runtime_error("PRIMARY_AND_DOWNSTREAM_LAYER_MUST_DIFFER_OR_DOWNSTREAM_MINUS_ONE");
            }

            llama_context_params cparams = llama_context_default_params();
            cparams.n_ctx = 256;
            cparams.n_batch = 256;
            cparams.n_ubatch = 256;
            llama_context * ctx = llama_init_from_model(model, cparams);
            if (!ctx) {
                throw std::runtime_error("CONTEXT_INIT_FAILED");
            }
            llama_set_n_threads(ctx, 2, 2);

            llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(primary_layer), true);
            if (downstream_layer >= 0) {
                llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(downstream_layer), true);
            }

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
                cvec_rc = llama_set_adapter_cvec(
                    ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end
                );
                cvec_applied = true;
                if (cvec_rc != 0) {
                    llama_free(ctx);
                    throw std::runtime_error("LLAMA_SET_ADAPTER_CVEC_FAILED:" + std::to_string(cvec_rc));
                }
            }

            std::vector<llama_token> tokens = tokenize(vocab, prompt, true);
            if (tokens.empty()) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_TOKENIZATION_EMPTY");
            }
            if (tokens.size() > static_cast<size_t>(cparams.n_batch)) {
                llama_free(ctx);
                throw std::runtime_error("PROMPT_EXCEEDS_SINGLE_UBATCH_CAPTURE_CONTRACT");
            }

            llama_batch batch = llama_batch_get_one(tokens.data(), static_cast<int32_t>(tokens.size()));
            const int32_t decode_rc = llama_decode(ctx, batch);
            if (decode_rc != 0) {
                llama_free(ctx);
                throw std::runtime_error("LLAMA_DECODE_FAILED:" + std::to_string(decode_rc));
            }
            llama_synchronize(ctx);

            const float * primary = last_token_row(ctx, primary_layer, tokens.size(), n_embd);
            const float * downstream = downstream_layer >= 0
                ? last_token_row(ctx, downstream_layer, tokens.size(), n_embd)
                : nullptr;

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_LAYER_CAPTURE_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout
                << ",\"prompt_tokens\":" << tokens.size()
                << ",\"cvec_applied\":" << (cvec_applied ? "true" : "false")
                << ",\"cvec_rc\":" << cvec_rc
                << ",\"cvec_float_count\":" << cvec_float_count
                << ",\"il_start\":" << il_start
                << ",\"il_end\":" << il_end
                << ",\"primary_layer_inp\":" << primary_layer
                << ",\"primary_l2\":" << l2_norm(primary, n_embd)
                << ",\"primary_activation\":";
            json_f32_row(std::cout, primary, n_embd);
            if (downstream) {
                std::cout
                    << ",\"downstream_layer_inp\":" << downstream_layer
                    << ",\"downstream_l2\":" << l2_norm(downstream, n_embd)
                    << ",\"downstream_activation\":";
                json_f32_row(std::cout, downstream, n_embd);
            } else {
                std::cout << ",\"downstream_layer_inp\":null,\"downstream_activation\":null";
            }
            std::cout << "}\n";
            llama_free(ctx);
        } catch (const std::exception & e) {
            std::cout
                << "{\"schema\":\"CLAY_LLAMA_CPP_LAYER_CAPTURE_OBSERVATION_ERROR/v1\""
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
