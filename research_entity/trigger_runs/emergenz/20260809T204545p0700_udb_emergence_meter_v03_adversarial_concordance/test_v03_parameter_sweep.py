import unittest

from v03_parameter_sweep import (
    cluster_surface,
    macro_search_curve,
    regime_common_driver,
    time_null_surface,
    time_power_surface,
)


class ParameterSweepTests(unittest.TestCase):
    def test_surface_has_requested_cells(self):
        result = time_null_surface(phis=(0.0, 0.95), sample_sizes=(120,), seeds=4, draws=19)
        self.assertEqual(len(result), 2)
        self.assertEqual({cell["phi"] for cell in result}, {0.0, 0.95})

    def test_cluster_rejects_pseudoreplication(self):
        result = cluster_surface(
            episode_counts=(12,), tick_counts=(80,), effects=(0.0,), seeds=16, draws=99
        )[0]
        self.assertGreater(
            result["tick_level_rejection_rate"],
            result["episode_cluster_rejection_rate"],
        )

    def test_macro_train_optimum_is_monotone_with_search_budget(self):
        curve = macro_search_curve(checkpoints=(1, 20, 100), seeds=8, test_n=1000)
        train = [cell["median_selected_train_mi_bits"] for cell in curve]
        self.assertEqual(train, sorted(train))

    def test_shared_regime_explains_most_apparent_information(self):
        result = regime_common_driver(seeds=8, n=300, draws=39)
        self.assertGreater(
            result["median_unconditional_lag_mi_bits"],
            result["median_regime_conditioned_lag_cmi_bits"],
        )

    def test_power_surface_retains_null_and_signal_rows(self):
        result = time_power_surface(betas=(0.0, 0.6), seeds=4, draws=19)
        self.assertEqual([cell["beta"] for cell in result], [0.0, 0.6])


if __name__ == "__main__":
    unittest.main()
