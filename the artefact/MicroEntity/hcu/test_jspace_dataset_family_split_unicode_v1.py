import unicodedata
import unittest

from jspace_dataset_family_split_v1 import JSpaceDatasetFamilySplitError, split_for_family


class FamilySplitUnicodeFenceTests(unittest.TestCase):
    def test_nfc_family_id_remains_admitted_and_deterministic(self):
        family = "episode:naïve"
        self.assertEqual(unicodedata.normalize("NFC", family), family)
        self.assertEqual(split_for_family(family), split_for_family(family))

    def test_canonically_equivalent_nfd_alias_fails_closed(self):
        family_nfc = "episode:naïve"
        family_nfd = unicodedata.normalize("NFD", family_nfc)
        self.assertNotEqual(family_nfc, family_nfd)
        self.assertEqual(unicodedata.normalize("NFC", family_nfd), family_nfc)
        split_for_family(family_nfc)
        with self.assertRaisesRegex(JSpaceDatasetFamilySplitError, "trace_family_id:NFC_REQUIRED"):
            split_for_family(family_nfd)


if __name__ == "__main__":
    unittest.main()
