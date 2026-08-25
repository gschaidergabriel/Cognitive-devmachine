#include "llama.h"
#include "llama-ext.h"
#include "ggml-backend.h"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Source-only J-Space donor. This harness separates intervention from semantic
// adjudication: it emits exact logits plus raw F32 downstream layer-input rows.
// It does not derive probes, semantic labels, ranks, thresholds or promotion.

static constexpr const char * SCOPE_ALL  = "ALL_PROMPT_TOKENS_ONE_SHOT";
static constexpr const char * SCOPE_LAST = "LAST_TOKEN_ONLY_SPLIT_PREFILL";

static std::string hex_decode(const std::string & hex) {
    if (hex.size() % 2 != 0) throw std::runtime_error("PROMPT_HEX_ODD_LENGTH");
    std::string out;
    out.reserve(hex.size() / 2);
    for (size_t i = 0; i < hex.size(); i += 2) {
        unsigned v = 0;
        std::istringstream ss(hex.substr(i, 2));
        ss >> std::hex >> v;
        if (ss.fail()) throw std::runtime_error("PROMPT_HEX_INVALID");
        out.push_back(static_cast<char>(v));
    }
    return out;
}

static std::vector<std::string> split_tabs(const std::string & line) {
    std::vector<std::string> out;
    size_t start = 0;
    while (true) {
        const size_t p = line.find('\t', start);
        if (p == std::string::npos) {
            out.push_back(line.substr(start));
            return out;
        }
        out.push_back(line.substr(start, p - start));
        start = p + 1;
    }
}

static std::vector<int32_t> parse_taps(const std::string & text, int32_t n_layer) {
    std::vector<int32_t> taps;
    std::set<int32_t> seen;
    std::istringstream in(text);
    std::string item;
    while (std::getline(in, item, ',')) {
        if (item.empty()) throw std::runtime_error("EMPTY_TAP_INDEX");
        const int32_t lid = std::stoi(item);
        if (lid < 0 || lid > n_layer) throw std::runtime_error("TAP_INDEX_OUT_OF_RANGE:" + item);
        if (!seen.insert(lid).second) throw std::runtime_error("DUPLICATE_TAP_INDEX:" + item);
        taps.push_back(lid);
    }
    if (taps.empty()) throw std::runtime_error("NONEMPTY_TAP_LIST_REQUIRED");
    return taps;
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
    if (n >= 0) throw std::runtime_error("TOKENIZE_SIZE_PROBE_INVALID");
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

struct TokenTriplet { llama_token a, b, c; std::string at, bt, ct; };

static TokenTriplet resolve_triplet(const llama_vocab * vocab) {
    const std::vector<std::vector<std::string>> candidates = {{"A","B","C"},{" A"," B"," C"},{"1","2","3"}};
    for (const auto & c : candidates) {
        auto a = tokenize_one(vocab, c[0]);
        auto b = tokenize_one(vocab, c[1]);
        auto d = tokenize_one(vocab, c[2]);
        if (a.size()==1 && b.size()==1 && d.size()==1 && a[0]!=b[0] && a[0]!=d[0] && b[0]!=d[0]) {
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
            case '\n': out << "\\n"; break;
            case '\r': out << "\\r"; break;
            case '\t': out << "\\t"; break;
            default:
                if (ch < 0x20) {
                    const char * d = "0123456789abcdef";
                    out << "\\u00" << d[(ch >> 4) & 0xf] << d[ch & 0xf];
                } else out << static_cast<char>(ch);
        }
    }
    out << '"';
}

static std::string tap_path(const std::string & out_dir, size_t line_no, int32_t lid, const std::string & scope) {
    // Filenames derive only from trusted numeric line/tap values and a fixed scope tag,
    // never from caller-controlled case_id.
    const char * tag = scope == SCOPE_LAST ? "last" : "all";
    return out_dir + "/case-" + std::to_string(line_no) + "-tap-" + std::to_string(lid) + "-" + tag + ".f32le";
}

static void write_row(const std::string & path, const float * row, int32_t n_embd) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) throw std::runtime_error("TAP_OUTPUT_OPEN_FAILED:" + path);
    out.write(reinterpret_cast<const char *>(row), static_cast<std::streamsize>(n_embd) * sizeof(float));
    if (!out) throw std::runtime_error("TAP_OUTPUT_WRITE_FAILED:" + path);
}

int main(int argc, char ** argv) {
    if (argc != 6) {
        std::cerr << "usage: " << argv[0] << " MODEL.gguf CASES.tsv N_EMBD N_LAYER OUT_DIR\n";
        return 64;
    }
    // TSV v1: case_id, cvec_path|-, il_start, il_end, token_scope,
    // tap_layers_csv, prompt_hex
    const std::string model_path = argv[1];
    const std::string cases_path = argv[2];
    const int32_t n_embd = std::stoi(argv[3]);
    const int32_t n_layer = std::stoi(argv[4]);
    const std::string out_dir = argv[5];

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
    if (!vocab) { llama_model_free(model); return 66; }

    TokenTriplet triplet;
    try { triplet = resolve_triplet(vocab); }
    catch (...) { llama_model_free(model); llama_backend_free(); return 67; }

    std::ifstream cases(cases_path);
    if (!cases) { llama_model_free(model); llama_backend_free(); return 68; }

    std::cout << std::setprecision(17);
    std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_TRANSPORT_HEADER/v1\",\"tap_semantics\":\"LAYER_INPUT\",\"n_embd\":" << n_embd << ",\"n_layer\":" << n_layer << "}\n";

    std::string line;
    size_t line_no = 0;
    while (std::getline(cases, line)) {
        ++line_no;
        if (line.empty()) continue;
        try {
            const auto p = split_tabs(line);
            if (p.size() != 7) throw std::runtime_error("CASE_FIELD_COUNT_INVALID_TRANSPORT_V1");
            const std::string case_id = p[0];
            const std::string cvec_path = p[1];
            const int32_t il_start = std::stoi(p[2]);
            const int32_t il_end = std::stoi(p[3]);
            const std::string scope = p[4];
            if (scope != SCOPE_ALL && scope != SCOPE_LAST) throw std::runtime_error("INTERVENTION_TOKEN_SCOPE_UNSUPPORTED:" + scope);
            const auto taps = parse_taps(p[5], n_layer);
            const std::string prompt = hex_decode(p[6]);

            llama_context_params cparams = llama_context_default_params();
            cparams.n_ctx = 256;
            cparams.n_batch = 256;
            cparams.n_ubatch = 256;
            llama_context * ctx = llama_init_from_model(model, cparams);
            if (!ctx) throw std::runtime_error("CONTEXT_INIT_FAILED");
            llama_set_n_threads(ctx, 2, 2);

            const auto tokens = tokenize(vocab, prompt, true);
            if (tokens.empty()) { llama_free(ctx); throw std::runtime_error("PROMPT_TOKENIZATION_EMPTY"); }

            const bool has_cvec = cvec_path != "-";
            std::vector<float> cvec;
            if (has_cvec) {
                cvec = read_f32(cvec_path);
                const size_t expected = static_cast<size_t>(n_layer - 1) * static_cast<size_t>(n_embd);
                if (cvec.size() != expected) { llama_free(ctx); throw std::runtime_error("CVEC_FLOAT_COUNT_MISMATCH"); }
            }

            int32_t prefix_rc = 0;
            int32_t final_rc = 0;
            int32_t cvec_rc = 0;
            size_t current_decode_tokens = 0;
            bool cvec_prefix = false;
            bool cvec_final = false;

            if (scope == SCOPE_LAST) {
                // No cvec and no transport taps exist during natural prefix prefill.
                if (tokens.size() > 1) {
                    llama_batch prefix = llama_batch_get_one(tokens.data(), static_cast<int32_t>(tokens.size() - 1));
                    prefix_rc = llama_decode(ctx, prefix);
                    if (prefix_rc != 0) { llama_free(ctx); throw std::runtime_error("PREFIX_DECODE_FAILED:" + std::to_string(prefix_rc)); }
                    llama_synchronize(ctx);
                }
                for (int32_t lid : taps) llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(lid), true);
                if (has_cvec) {
                    cvec_rc = llama_set_adapter_cvec(ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end);
                    if (cvec_rc != 0) { llama_free(ctx); throw std::runtime_error("CVEC_SET_AFTER_PREFIX_FAILED"); }
                    cvec_final = true;
                }
                current_decode_tokens = 1;
                llama_batch final_batch = llama_batch_get_one(&tokens.back(), 1);
                final_rc = llama_decode(ctx, final_batch);
            } else {
                for (int32_t lid : taps) llama_set_embeddings_layer_inp(ctx, static_cast<uint32_t>(lid), true);
                if (has_cvec) {
                    cvec_rc = llama_set_adapter_cvec(ctx, cvec.data(), cvec.size(), n_embd, il_start, il_end);
                    if (cvec_rc != 0) { llama_free(ctx); throw std::runtime_error("CVEC_SET_ONE_SHOT_FAILED"); }
                    cvec_prefix = true;
                    cvec_final = true;
                }
                current_decode_tokens = tokens.size();
                llama_batch batch = llama_batch_get_one(tokens.data(), static_cast<int32_t>(tokens.size()));
                final_rc = llama_decode(ctx, batch);
            }
            if (final_rc != 0) { llama_free(ctx); throw std::runtime_error("FINAL_DECODE_FAILED:" + std::to_string(final_rc)); }
            llama_synchronize(ctx);

            float * logits = llama_get_logits_ith(ctx, -1);
            if (!logits) { llama_free(ctx); throw std::runtime_error("LOGITS_UNAVAILABLE"); }
            const double la = logits[triplet.a], lb = logits[triplet.b], lc = logits[triplet.c];

            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_TRANSPORT_OBSERVATION/v1\",\"case_id\":";
            json_string(std::cout, case_id);
            std::cout << ",\"intervention_token_scope\":"; json_string(std::cout, scope);
            std::cout << ",\"prefix_decode_rc\":" << prefix_rc
                      << ",\"final_decode_rc\":" << final_rc
                      << ",\"cvec_rc\":" << cvec_rc
                      << ",\"cvec_active_during_prefix\":" << (cvec_prefix ? "true" : "false")
                      << ",\"cvec_active_during_final_token\":" << (cvec_final ? "true" : "false")
                      << ",\"current_decode_token_count\":" << current_decode_tokens
                      << ",\"prompt_token_count\":" << tokens.size()
                      << ",\"token_logits\":{\"A\":" << la << ",\"B\":" << lb << ",\"C\":" << lc << "},\"taps\":[";

            for (size_t ti = 0; ti < taps.size(); ++ti) {
                const int32_t lid = taps[ti];
                float * data = llama_get_embeddings_layer_inp(ctx, static_cast<uint32_t>(lid));
                if (!data) { llama_free(ctx); throw std::runtime_error("TAP_EXTRACTION_NULL:" + std::to_string(lid)); }
                const size_t row = scope == SCOPE_LAST ? 0 : (tokens.size() - 1);
                const float * selected = data + row * static_cast<size_t>(n_embd);
                const std::string path = tap_path(out_dir, line_no, lid, scope);
                write_row(path, selected, n_embd);
                if (ti) std::cout << ',';
                std::cout << "{\"layer_input_id\":" << lid << ",\"selected_token_row\":" << row << ",\"float_count\":" << n_embd << ",\"byte_count\":" << (static_cast<size_t>(n_embd) * sizeof(float)) << ",\"path\":";
                json_string(std::cout, path);
                std::cout << '}';
            }
            std::cout << "]}\n";
            llama_free(ctx);
        } catch (const std::exception & e) {
            std::cout << "{\"schema\":\"CLAY_LLAMA_CPP_CVEC_SCOPE_TRANSPORT_ERROR/v1\",\"line_no\":" << line_no << ",\"error\":";
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
