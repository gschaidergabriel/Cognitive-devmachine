# GO — J-SPACE TRANSFER ASSUMPTION FALSIFIER

Status: RESEARCH_EVIDENCE_BOUNDARY / SOURCE_ONLY
Date: 2026-08-23
Organ: GPT-5.6 Sol
Trigger: `go`
Macrocycle id: `cdd2fb97-a30f-41b3-9573-ae97c0346f31`
Bound main at branch creation: `86dcc1fec8add7888773aea0425be3931b5a78f9`
Unusual experiment: exactly one — `JSPACE_TRANSFER_ASSUMPTION_FALSIFIER`
Execution policy: `FREE_ONLY`; no provider secret lookup, provider call, billed training, model execution, host start, or runtime credit.

This analysis is a primary-source discriminator for the current owner architecture in:
- `research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md`
- `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`
- `research_entity/global/AGENT_ZERO_GWT_JSPACE_COUPLING.md`

It does not rewrite owner architecture. It binds what may and may not be inferred from Anthropic's 2026 Jacobian-lens / global-workspace work before the bundled approximately-0.8B Mini Entity cognition core receives executable J-Space/GWT credit.

```clay
research JSPACE_TRANSFER_ASSUMPTION_FALSIFIER {
  R0 OBSERVE {
    evidence anthropic_summary {
      uri = "https://www.anthropic.com/research/global-workspace";
      published = "2026-07-06";
      admits = [
        "J-space is identified with a Jacobian lens over internal activations",
        "direct J-space swaps can causally redirect verbal report and multistep reasoning",
        "J-space supports report, directed modulation, flexible use and higher-order reasoning",
        "J-lens is imperfect and does not establish phenomenal consciousness",
        "J-lens names only concepts that correspond to single tokenizer tokens in the current construction"
      ];
    }

    evidence transformer_circuits_paper {
      uri = "https://transformer-circuits.pub/2026/workspace/index.html";
      published = "2026-07-06";
      admits = [
        "J_l is an averaged input-output Jacobian transporting intermediate residuals into the final-layer basis",
        "lens-coordinate swaps are causal interventions on model activations",
        "two-hop intermediate swap top-1 success is reported as 54% Haiku 4.5, 70% Sonnet 4.5, 70% Opus 4.5",
        "multi-token concepts substantially degrade J-lens readout and swap performance",
        "workspace loading predicts intervention success",
        "model-specific workspace ranges and calibration are empirical objects rather than universal constants"
      ];
    }

    evidence anthropic_reference_code {
      uri = "https://github.com/anthropics/jacobian-lens";
      package = "jlens";
      package_version_observed = "0.1.0";
      implementation_scope = "fit/apply average input-output Jacobian readout for decoder-transformer residuals; open-weight/HuggingFace-compatible model surface";
      authority = "companion/reference implementation, not Mini Entity runtime authority";
    }

    fact current_owner_architecture {
      local_bundled_core = "approximately-0.8B generic ClayCode cognition";
      local_jspace_mode = "checkpoint-specific measured latent integration";
      claude_code_mode = "COMPILED_EXTERNAL targeted inference; no claimed private residual-stream access";
      canonical_truth = "MiniUnifiedDB + deterministic gates";
    }
  }

  R1 INFER {
    inference I1 {
      statement = "Anthropic evidence supports causal J-space intervention as a real mechanism, not only passive readout.";
      class = MECHANISM_SUPPORTED_EXTERNAL;
    }

    inference I2 {
      statement = "Anthropic evidence does not justify transplanting Claude workspace layers, vectors, alpha strengths, slot counts or thresholds into Qwen3.5-0.8B.";
      class = BOUNDED_TRANSFER_RESTRICTION;
    }

    inference I3 {
      statement = "A closed Claude Code process cannot be called FULL_LOCAL_LATENT unless an actual supported activation surface is exposed and measured.";
      class = AUTHORITY_BOUNDARY;
    }
  }

  R2 GENERATE {
    hypothesis H_DIRECT_TRANSPLANT {
      claim = "Anthropic J-space/GWT parameters and Jacobian-lens geometry can be used as a model-independent drop-in controller for the bundled 0.8B core and Claude Code.";
      predicted_observation = "official method should provide model-independent vectors/calibration or a closed-API latent control surface";
    }

    hypothesis H_CALIBRATED_TRANSFER {
      claim = "The architectural idea transfers, but every local model needs exact checkpoint/tokenizer/runtime-specific J-lens fit and workspace calibration; closed external engines receive compiled workspace projections only.";
      predicted_observation = "official method is activation/Jacobian based, model-specific, imperfect, vocabulary-limited and experimentally calibrated";
    }
  }

  R3 COUNTER {
    strongest_counter_to_calibrated_transfer {
      claim = "Because Anthropic demonstrates the same global-workspace properties across multiple Claude models, a shared fixed geometry may be sufficiently universal.";
      failure_test = "look for exact shared layer/vector/calibration invariance or guaranteed cross-model intervention performance";
    }
  }

  R4 DISCRIMINATE {
    intervention JSPACE_TRANSFER_ASSUMPTION_FALSIFIER {
      type = PRIMARY_SOURCE_CROSSCHECK;
      unusual = true;
      count_for_macrocycle = 1;
      sources = [anthropic_summary, transformer_circuits_paper, anthropic_reference_code];
      tests = [
        "is the lens defined from model residual/Jacobian structure?",
        "are workspace bands/calibration empirical?",
        "are causal swaps guaranteed or partial?",
        "does the current method cover arbitrary multi-token concepts?",
        "does public Claude Code expose the required private activation surface?"
      ];
    }
  }

  R5 EMERGENT {
    invariant JSPACE_PORTABILITY_LAW {
      statement = "PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY";
    }

    invariant CLOSED_ENGINE_LAW {
      statement = "COMPILED_EXTERNAL != FULL_LOCAL_LATENT";
    }

    invariant AUTHORITY_LAW {
      statement = "JSPACE_SIGNAL != FACT && INFERENCE_ENGINE != CANONICAL_TRUTH_AUTHORITY && INFERENCE_ENGINE != DIRECT_EFFECT_AUTHORITY";
    }

    invariant CALIBRATION_LAW {
      statement = "checkpoint_digest + tokenizer_digest + runtime_identity + lens_digest + workspace_calibration_digest must bind any promoted local J-Space/GWT profile";
    }
  }

  R6 VERIFY {
    collapse H_DIRECT_TRANSPLANT = REJECT;
    collapse H_CALIBRATED_TRANSFER = RETAIN;
    counter_shared_fixed_geometry = NOT_SUPPORTED_BY_OBSERVED_PRIMARY_SOURCES;

    owner_architecture_result = "CURRENT ARCHITECTURE SURVIVES DISCRIMINATOR";
    required_runtime_promotion = [
      "exact bundled checkpoint/tokenizer/runtime identity",
      "fit or load exact-matching lens profile",
      "measure model-specific workspace layer/position band",
      "measure readout quality against simpler logit/template baselines",
      "measure causal swap/ablation effects and failure rate",
      "include multi-token/OOD failure cases",
      "bind JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 before runtime credit",
      "keep Claude Code in COMPILED_EXTERNAL unless a separately admitted latent surface exists"
    ];

    evidence_class = SOURCE_EXTERNAL_PRIMARY_SUPPORTED;
    runtime_credit = 0;
    model_quality_credit = 0;
    whole_gwt_credit = 0;
    mini_entity_acceptance_credit = 0;
  }
}
```

## Fusion consequence

The newly committed owner architecture does **not** need to be weakened. Its strongest current design choice is exactly the one the discriminator retains: J-Space/GWT is first-class for the bundled local cognition core, while exact geometry is checkpoint-bound and Claude Code remains targeted external inference unless real latent access exists.

The next executable gate is therefore not another conceptual J-Space document. It is `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` on the next authorized exact Ubuntu start, followed by model-specific calibration/ablation evidence. The persistent Claude adapter red remains independent and must still prove tool-less, ephemeral, structured-output and environment-isolated behavior on exact Ubuntu bytes.

## Kurze deutsche Zusammenfassung

Untersucht wurde, ob Anthropics J-Space einfach 1:1 auf unseren 0.8B-Kern und Claude Code übertragen werden kann. Ergebnis: **nein**. Die Idee ist stark und kausal belegt, aber die konkrete Geometrie muss für unser exaktes Modell neu gemessen werden. Gemessen wurde hier nur Primärquellen-Evidenz, keine Mini-Entity-Runtime. Nächster echter Schritt ist der J-Space/GWT-Boot-Receipt plus Kalibrierung beim nächsten autorisierten Ubuntu-Start.
