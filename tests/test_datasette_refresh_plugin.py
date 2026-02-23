import asyncio
import json
import unittest
from unittest.mock import patch

from duprly.compat_click import click

from duprly.datasette_plugins.duprly_refresh import (
    import_player,
    request_player_data,
    search_players_remote,
)


class _Req:
    def __init__(self, args):
        self.args = args


class DatasetteRefreshPluginTests(unittest.TestCase):
    def test_search_players_remote_short_query_returns_empty_hits(self):
        response = asyncio.run(search_players_remote(_Req({"q": "l"}), datasette=None))
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertEqual(body["result"]["hits"], [])

    @patch("duprly.datasette_plugins.duprly_refresh._existing_player_ids")
    @patch("duprly.datasette_plugins.duprly_refresh.search_players")
    def test_search_players_remote_returns_labeled_hits(self, search_players, existing_player_ids):
        search_players.return_value = [
            {
                "id": 8354624893,
                "fullName": "Leo Sternlicht",
                "duprId": "1NQEL7",
                "shortAddress": "Brooklyn, NY",
                "ratings": {"singles": None, "doubles": 4.999},
            },
            {
                "id": 6886613721,
                "fullName": "Example Player",
                "duprId": "OD6VL7",
                "shortAddress": "New York, NY",
                "ratings": {"singles": 4.2, "doubles": 4.8},
            },
        ]
        existing_player_ids.return_value = {8354624893}

        response = asyncio.run(search_players_remote(_Req({"q": "leo", "limit": "8"}), datasette=None))
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        hits = body["result"]["hits"]
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["label"], "Leo Sternlicht [8354624893]")
        self.assertTrue(hits[0]["already_saved"])
        self.assertFalse(hits[1]["already_saved"])

    def test_import_player_requires_numeric_dupr_id(self):
        response = asyncio.run(import_player(_Req({"dupr_id": "abc"}), datasette=None))
        self.assertEqual(response.status, 400)
        body = json.loads(response.body)
        self.assertFalse(body["ok"])

    @patch("duprly.datasette_plugins.duprly_refresh.Session")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_player")
    def test_import_player_adds_player(self, fetch_player, session_cls):
        fetch_player.return_value = {
            "id": 8354624893,
            "fullName": "Leo Sternlicht",
            "duprId": "1NQEL7",
            "ratings": {"doubles": 4.999, "singles": None},
        }
        sess = session_cls.return_value.__enter__.return_value
        sess.execute.return_value.scalar_one_or_none.return_value = None

        response = asyncio.run(import_player(_Req({"dupr_id": "8354624893"}), datasette=None))
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertTrue(body["result"]["added"])
        self.assertEqual(body["result"]["player"]["full_name"], "Leo Sternlicht")
        fetch_player.assert_called_once()

    @patch("duprly.datasette_plugins.duprly_refresh.fetch_matches")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_rating_history")
    @patch("duprly.datasette_plugins.duprly_refresh.Session")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_player")
    def test_import_player_can_sync_rating_history_and_matches(
        self,
        fetch_player,
        session_cls,
        fetch_rating_history,
        fetch_matches,
    ):
        fetch_player.return_value = {
            "id": 8354624893,
            "fullName": "Leo Sternlicht",
            "duprId": "1NQEL7",
            "ratings": {"doubles": 4.999, "singles": None},
        }
        fetch_rating_history.return_value = {
            "types_fetched": ["doubles"],
            "counts": {"doubles": 12},
            "start_date": "2025-01-01",
            "end_date": "2026-02-23",
            "persisted": {"doubles": {"inserted": 12, "deleted": 0}},
            "fallback": {"doubles": {"used": False}},
        }
        fetch_matches.return_value = {
            "scope": "ALL",
            "match_count": 7,
            "persisted": {"inserted": 3, "skipped": 4},
            "raw_persisted": {"inserted": 7, "updated": 0, "deleted": 0},
        }
        sess = session_cls.return_value.__enter__.return_value
        sess.execute.return_value.scalar_one_or_none.return_value = None

        response = asyncio.run(
            import_player(
                _Req(
                    {
                        "dupr_id": "8354624893",
                        "include_rating_history": "1",
                        "include_matches": "1",
                        "rating_type": "doubles",
                    }
                ),
                datasette=None,
            )
        )
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertIn("rating_history", body["result"])
        self.assertIn("matches", body["result"])
        fetch_rating_history.assert_called_once()
        fetch_matches.assert_called_once()

    def test_request_player_data_requires_numeric_dupr_id(self):
        response = asyncio.run(request_player_data(_Req({"dupr_id": "abc"}), datasette=None))
        self.assertEqual(response.status, 400)
        body = json.loads(response.body)
        self.assertFalse(body["ok"])

    @patch("duprly.datasette_plugins.duprly_refresh.fetch_matches")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_rating_history")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_player")
    def test_request_player_data_fetches_player_and_ratings(
        self,
        fetch_player,
        fetch_rating_history,
        fetch_matches,
    ):
        fetch_player.return_value = {"id": 8354624893, "fullName": "Leo Sternlicht", "duprId": "OD6VL7"}
        fetch_rating_history.return_value = {
            "types_fetched": ["doubles"],
            "counts": {"doubles": 25},
            "start_date": "2025-01-01",
            "end_date": "2026-02-22",
            "persisted": {"doubles": {"inserted": 25, "deleted": 0}},
        }
        fetch_matches.return_value = {
            "scope": "ALL",
            "match_count": 10,
            "persisted": {"inserted": 3, "skipped": 7},
            "raw_persisted": {"inserted": 10, "updated": 0, "deleted": 0},
        }

        response = asyncio.run(
            request_player_data(
                _Req({"dupr_id": "8354624893", "rating_type": "doubles"}),
                datasette=None,
            )
        )
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertEqual(body["result"]["dupr_id"], "8354624893")
        fetch_player.assert_called_once()
        fetch_rating_history.assert_called_once()
        fetch_matches.assert_not_called()

    @patch("duprly.datasette_plugins.duprly_refresh.fetch_matches")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_rating_history")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_player")
    def test_request_player_data_can_include_matches(
        self,
        fetch_player,
        fetch_rating_history,
        fetch_matches,
    ):
        fetch_player.return_value = {"id": 8354624893, "fullName": "Leo Sternlicht", "duprId": "OD6VL7"}
        fetch_rating_history.return_value = {"types_fetched": ["doubles"], "counts": {"doubles": 3}, "persisted": {}}
        fetch_matches.return_value = {
            "scope": "ALL",
            "match_count": 2,
            "persisted": {"inserted": 2, "skipped": 0},
            "raw_persisted": {"inserted": 2, "updated": 0, "deleted": 0},
        }

        response = asyncio.run(
            request_player_data(
                _Req({"dupr_id": "8354624893", "rating_type": "doubles", "include_matches": "1"}),
                datasette=None,
            )
        )
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertIn("matches", body["result"])
        fetch_matches.assert_called_once()

    @patch("duprly.datasette_plugins.duprly_refresh.fetch_matches")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_rating_history")
    @patch("duprly.datasette_plugins.duprly_refresh.fetch_player")
    def test_request_player_data_returns_partial_on_match_failure(
        self,
        fetch_player,
        fetch_rating_history,
        fetch_matches,
    ):
        fetch_player.return_value = {"id": 8354624893, "fullName": "Leo Sternlicht", "duprId": "OD6VL7"}
        fetch_rating_history.return_value = {"types_fetched": ["doubles"], "counts": {"doubles": 3}, "persisted": {}}
        fetch_matches.side_effect = click.ClickException("match endpoint failed")

        response = asyncio.run(
            request_player_data(
                _Req({"dupr_id": "8354624893", "rating_type": "doubles", "include_matches": "1"}),
                datasette=None,
            )
        )
        self.assertEqual(response.status, 200)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertTrue(body["partial"])
        self.assertIn("Match sync failed", body["warnings"][0])
        self.assertIn("matches_error", body["result"])


if __name__ == "__main__":
    unittest.main()
