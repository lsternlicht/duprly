import unittest
from unittest.mock import patch

from click.testing import CliRunner

from duprly.cli import cli


class BrowseRatingHistoryCommandTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("duprly.commands.browse.fetch_rating_history")
    def test_browse_rating_history_json(self, fetch_rating_history):
        fetch_rating_history.return_value = {
            "dupr_id": "6886613721",
            "type_requested": "both",
            "types_fetched": ["singles", "doubles"],
            "start_date": "2025-02-21",
            "end_date": "2026-02-21",
            "histories": {"singles": [{"date": "2026-01-01"}], "doubles": [{"date": "2026-01-02"}]},
            "counts": {"singles": 1, "doubles": 1},
            "persisted": {"singles": {"inserted": 1, "deleted": 0}, "doubles": {"inserted": 1, "deleted": 0}},
        }

        result = self.runner.invoke(
            cli,
            [
                "--json",
                "--no-interactive",
                "browse",
                "rating-history",
                "6886613721",
                "--type",
                "both",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"dupr_id": "6886613721"', result.output)
        self.assertIn('"type_requested": "both"', result.output)
        fetch_rating_history.assert_called_once()

    @patch("duprly.commands.browse.fetch_rating_history")
    def test_browse_rating_history_non_json(self, fetch_rating_history):
        fetch_rating_history.return_value = {
            "dupr_id": "6886613721",
            "type_requested": "doubles",
            "types_fetched": ["doubles"],
            "start_date": "2025-12-14",
            "end_date": "2026-02-21",
            "histories": {"doubles": [{"date": "2026-01-02"}]},
            "counts": {"doubles": 1},
            "persisted": {"doubles": {"inserted": 1, "deleted": 0}},
        }

        result = self.runner.invoke(
            cli,
            [
                "--no-interactive",
                "browse",
                "rating-history",
                "6886613721",
                "--type",
                "doubles",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Rating History", result.output)
        self.assertIn("doubles", result.output)


if __name__ == "__main__":
    unittest.main()
