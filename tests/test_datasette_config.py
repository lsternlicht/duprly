import unittest

from duprly.datasette_config import build_datasette_metadata


class DatasetteConfigTests(unittest.TestCase):
    def test_build_datasette_metadata_contains_expected_queries(self):
        metadata = build_datasette_metadata("dupr")

        self.assertEqual(metadata["title"], "DUPR Pickleball Analytics")
        self.assertIn("databases", metadata)
        self.assertIn("dupr", metadata["databases"])

        queries = metadata["databases"]["dupr"]["queries"]
        expected_queries = {
            "player_directory",
            "club_directory",
            "player_rating_over_time",
            "player_rating_summary",
            "player_recent_form",
            "player_partner_breakdown",
            "player_opponent_breakdown",
            "club_top_risers",
            "club_rating_snapshot",
            "players_needing_more_data",
        }
        self.assertTrue(expected_queries.issubset(set(queries.keys())))

        for name in expected_queries:
            self.assertTrue(queries[name]["hide_sql"])
            self.assertIn("sql", queries[name])
            self.assertIsInstance(queries[name]["params"], list)

    def test_trend_query_is_chart_friendly(self):
        metadata = build_datasette_metadata("dupr")
        trend_sql = metadata["databases"]["dupr"]["queries"]["player_rating_over_time"]["sql"]
        self.assertIn("rating_date", trend_sql)
        self.assertIn("rating", trend_sql)
        self.assertIn("rating_type", trend_sql)
        self.assertIn("DOUBLES", trend_sql)
        self.assertIn("partner_name", trend_sql)
        self.assertIn("opponents", trend_sql)
        self.assertIn("score", trend_sql)
        self.assertIn("created_date", trend_sql)
        self.assertIn("modified_date", trend_sql)
        self.assertIn("event_title", trend_sql)
        self.assertIn("location", trend_sql)
        self.assertIn("player_latest_rating", trend_sql)
        self.assertIn("player_latest_rating_date", trend_sql)
        self.assertIn("score_admin_changed", trend_sql)
        self.assertIn("resolution_method", trend_sql)
        self.assertIn("rating_change", trend_sql)
        self.assertIn("reliability_score", trend_sql)
        self.assertIn("partner_tooltip_json", trend_sql)
        self.assertIn("opponents_tooltip_json", trend_sql)

    def test_directory_queries_use_name_and_id_filters(self):
        metadata = build_datasette_metadata("dupr")
        player_sql = metadata["databases"]["dupr"]["queries"]["player_directory"]["sql"]
        club_sql = metadata["databases"]["dupr"]["queries"]["club_directory"]["sql"]
        self.assertIn("v_player_directory", player_sql)
        self.assertIn("player_full_name", player_sql)
        self.assertIn("player_dupr_id", player_sql)
        self.assertIn("v_club_directory", club_sql)
        self.assertIn("club_name", club_sql)
        self.assertIn("club_id", club_sql)


if __name__ == "__main__":
    unittest.main()
