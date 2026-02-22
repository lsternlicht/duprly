import unittest
from unittest.mock import patch

from click.testing import CliRunner

from duprly.cli import cli


class BrowseLookupCommandTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("duprly.commands.browse.resolve_lookup_selection")
    @patch("duprly.commands.browse.lookup_with_suggestions")
    @patch("duprly.commands.browse.ensure_auth")
    def test_non_tty_player_lookup_without_download(
        self,
        _ensure_auth,
        lookup_with_suggestions,
        resolve_lookup_selection,
    ):
        lookup_with_suggestions.return_value = {"id": 7752563844, "fullName": "Aidan Bai"}
        resolve_lookup_selection.return_value = {
            "entity": "player",
            "selection": {"id": 7752563844, "fullName": "Aidan Bai"},
            "player": {"id": 7752563844, "fullName": "Aidan Bai", "ratings": {"singles": "4.3", "doubles": "5.0"}},
        }

        result = self.runner.invoke(
            cli,
            [
                "--json",
                "--no-interactive",
                "browse",
                "lookup",
                "--entity",
                "player",
                "--query",
                "aidan",
                "--no-download-matches",
                "--no-download-rating-history",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"entity": "player"', result.output)
        self.assertNotIn('"match_download"', result.output)

    @patch("duprly.commands.browse.fetch_rating_history")
    @patch("duprly.commands.browse.fetch_matches")
    @patch("duprly.commands.browse.resolve_lookup_selection")
    @patch("duprly.commands.browse.lookup_with_suggestions")
    @patch("duprly.commands.browse.ensure_auth")
    def test_player_lookup_downloads_matches_by_default_in_non_tty(
        self,
        _ensure_auth,
        lookup_with_suggestions,
        resolve_lookup_selection,
        fetch_matches,
        fetch_rating_history,
    ):
        lookup_with_suggestions.return_value = {"id": 7752563844, "fullName": "Aidan Bai"}
        resolve_lookup_selection.return_value = {
            "entity": "player",
            "selection": {"id": 7752563844, "fullName": "Aidan Bai"},
            "player": {"id": 7752563844, "fullName": "Aidan Bai", "ratings": {"singles": "4.3", "doubles": "5.0"}},
        }
        fetch_matches.return_value = {
            "dupr_id": "7752563844",
            "scope": "ALL",
            "start_date": None,
            "end_date": None,
            "match_count": 3,
            "persisted": {"inserted": 2, "skipped": 1},
            "raw_persisted": {"inserted": 3, "updated": 0, "deleted": 0},
            "snapshot_updated": True,
            "matches": [{"matchId": 1}, {"matchId": 2}, {"matchId": 3}],
        }
        fetch_rating_history.return_value = {
            "dupr_id": "7752563844",
            "type_requested": "both",
            "types_fetched": ["singles", "doubles"],
            "start_date": "2024-02-21",
            "end_date": "2026-02-21",
            "histories": {"singles": [{"date": "2026-01-01"}], "doubles": [{"date": "2026-01-01"}]},
            "counts": {"singles": 1, "doubles": 1},
            "persisted": {"singles": {"inserted": 1, "deleted": 0}, "doubles": {"inserted": 1, "deleted": 0}},
        }

        result = self.runner.invoke(
            cli,
            [
                "--json",
                "--no-interactive",
                "browse",
                "lookup",
                "--entity",
                "player",
                "--query",
                "aidan",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"match_download"', result.output)
        self.assertIn('"rating_history_download"', result.output)
        fetch_matches.assert_called_once()
        fetch_rating_history.assert_called_once()
        self.assertEqual(fetch_matches.call_args.kwargs["dupr_id"], "7752563844")
        self.assertTrue(fetch_matches.call_args.kwargs["persist"])
        self.assertEqual(fetch_rating_history.call_args.kwargs["dupr_id"], "7752563844")

    @patch("duprly.commands.browse.resolve_lookup_selection")
    @patch("duprly.commands.browse.lookup_with_suggestions")
    @patch("duprly.commands.browse.ensure_auth")
    def test_club_lookup_branch(self, _ensure_auth, lookup_with_suggestions, resolve_lookup_selection):
        lookup_with_suggestions.return_value = {"clubId": 8436164521, "clubName": "NYC Pickleball"}
        resolve_lookup_selection.return_value = {
            "entity": "club",
            "selection": {"clubId": 8436164521, "clubName": "NYC Pickleball"},
            "club": {"clubId": 8436164521, "clubName": "NYC Pickleball", "shortAddress": "New York, NY, US"},
        }

        result = self.runner.invoke(
            cli,
            [
                "--json",
                "--no-interactive",
                "browse",
                "lookup",
                "--entity",
                "club",
                "--query",
                "nyc",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"entity": "club"', result.output)
        self.assertIn('"clubId": 8436164521', result.output)

    @patch("duprly.commands.browse.lookup_with_suggestions")
    @patch("duprly.commands.browse.ensure_auth")
    def test_lookup_failure_reports_clean_click_error(self, _ensure_auth, lookup_with_suggestions):
        lookup_with_suggestions.side_effect = RuntimeError("Player search failed (HTTP 401).")

        result = self.runner.invoke(
            cli,
            [
                "--no-interactive",
                "browse",
                "lookup",
                "--entity",
                "player",
                "--query",
                "aidan",
            ],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Player search failed (HTTP 401).", result.output)

    @patch("duprly.commands.browse.fetch_rating_history")
    @patch("duprly.commands.browse.fetch_matches")
    @patch("duprly.commands.browse.resolve_lookup_selection")
    @patch("duprly.commands.browse.lookup_with_suggestions")
    @patch("duprly.commands.browse.ensure_auth")
    def test_player_lookup_skips_rating_history_when_opted_out(
        self,
        _ensure_auth,
        lookup_with_suggestions,
        resolve_lookup_selection,
        fetch_matches,
        fetch_rating_history,
    ):
        lookup_with_suggestions.return_value = {"id": 7752563844, "fullName": "Aidan Bai"}
        resolve_lookup_selection.return_value = {
            "entity": "player",
            "selection": {"id": 7752563844, "fullName": "Aidan Bai"},
            "player": {"id": 7752563844, "fullName": "Aidan Bai", "ratings": {"singles": "4.3", "doubles": "5.0"}},
        }
        fetch_matches.return_value = {
            "dupr_id": "7752563844",
            "scope": "ALL",
            "start_date": None,
            "end_date": None,
            "match_count": 1,
            "persisted": {"inserted": 1, "skipped": 0},
            "raw_persisted": {"inserted": 1, "updated": 0, "deleted": 0},
            "snapshot_updated": True,
            "matches": [{"matchId": 1}],
        }

        result = self.runner.invoke(
            cli,
            [
                "--json",
                "--no-interactive",
                "browse",
                "lookup",
                "--entity",
                "player",
                "--query",
                "aidan",
                "--no-download-rating-history",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"match_download"', result.output)
        self.assertNotIn('"rating_history_download"', result.output)
        fetch_rating_history.assert_not_called()


if __name__ == "__main__":
    unittest.main()
