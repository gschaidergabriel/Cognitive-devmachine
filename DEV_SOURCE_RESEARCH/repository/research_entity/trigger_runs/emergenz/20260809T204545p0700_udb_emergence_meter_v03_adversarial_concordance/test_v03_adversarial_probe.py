import unittest

from v03_adversarial_probe import (
    clustered_pseudoreplication,
    hidden_path_counterexample,
    macro_selection_bias,
    redundancy_overcount,
    time_null_sensitivity,
)


class AdversarialProbeTests(unittest.TestCase):
    def test_cluster_units_change_false_positive_control(self):
        result = clustered_pseudoreplication(seeds=30, draws=99)
        self.assertGreater(result["naive_tick_false_positive_rate"], 0.40)
        self.assertLess(result["episode_cluster_false_positive_rate"], 0.20)

    def test_time_nulls_can_disagree(self):
        result = time_null_sensitivity(seeds=20, draws=99)
        self.assertGreater(result["null_model_disagreement_rate"], 0.0)

    def test_macro_search_requires_holdout(self):
        result = macro_selection_bias(seeds=10, candidate_maps=800, test_n=3000)
        self.assertGreater(result["median_selected_train_mi_bits"], result["median_heldout_mi_bits"])

    def test_duplicate_source_overcounts_pairwise_synergy(self):
        result = redundancy_overcount()
        self.assertGreater(result["naive_pairwise_sum_bits"], result["target_entropy_bits"])

    def test_hidden_path_defeats_endpoint_only_validation(self):
        result = hidden_path_counterexample()
        self.assertGreater(result["excluded_variable_intervention_mean_absolute_effect"], 0.40)


if __name__ == "__main__":
    unittest.main()
