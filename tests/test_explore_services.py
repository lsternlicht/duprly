import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from duprly.dupr_db import (
    Base,
    Match,
    MatchTeam,
    Player,
    PlayerMatchRaw,
    PlayerMetadataSnapshot,
    PlayerRatingHistory,
    Rating,
)
from duprly.explore_services import (
    export_data,
    get_match_detail,
    get_player_match_summaries,
    get_player_overview,
    get_player_rating_series,
    list_players,
    list_raw_metadata,
)


class _Runtime:
    def __init__(self, engine):
        self.engine = engine


class ExploreServicesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.runtime = _Runtime(self.engine)
        self.now = datetime.now(timezone.utc)

        with Session(self.engine) as sess:
            self.player = Player(
                dupr_id=6886613721,
                full_name="Leo Sternlicht",
                first_name="Leo",
                last_name="Sternlicht",
                gender="M",
                age=35,
                image_url=None,
                email="leo@example.com",
                phone="+123456789",
                club_id=7735643894,
            )
            self.player.rating = Rating(
                singles=4.321,
                singles_verified=4.31,
                is_singles_provisional=False,
                doubles=4.689,
                doubles_verified=4.67,
                is_doubles_provisional=False,
            )

            partner = Player(
                dupr_id=6228848784,
                full_name="Connor Sedgewick",
                first_name="Connor",
                last_name="Sedgewick",
                gender="M",
                age=29,
                image_url=None,
                email=None,
                phone=None,
                club_id=0,
            )
            opp1 = Player(
                dupr_id=5971782383,
                full_name="Ron Sussman",
                first_name="Ron",
                last_name="Sussman",
                gender="M",
                age=38,
                image_url=None,
                email=None,
                phone=None,
                club_id=0,
            )
            opp2 = Player(
                dupr_id=5837778594,
                full_name="Graham Revzin",
                first_name="Graham",
                last_name="Revzin",
                gender="M",
                age=33,
                image_url=None,
                email=None,
                phone=None,
                club_id=0,
            )

            match = Match(
                match_id=4295493637,
                name="Life Time DUMBO 8.0 DUPR Cap Moneyball",
                date="2026-02-19",
                match_type="SIDE_ONLY",
                match_source="PARTNER",
                match_score_added=True,
            )
            team1 = MatchTeam(score1=7, score2=None, score3=None, is_winner=False)
            team1.players.extend([self.player, partner])
            team2 = MatchTeam(score1=11, score2=None, score3=None, is_winner=True)
            team2.players.extend([opp1, opp2])
            match.teams.extend([team1, team2])

            snapshot = PlayerMetadataSnapshot(
                player_dupr_id=6886613721,
                player_full_name="Leo Sternlicht",
                player_metadata_json=json.dumps(
                    {
                        "id": 6886613721,
                        "fullName": "Leo Sternlicht",
                        "gender": "M",
                        "ratings": {"singles": 4.321, "doubles": 4.689},
                        "contacts": {"email": "leo@example.com", "phone": "+123456789"},
                    }
                ),
                player_metadata_updated_at=self.now,
                matches_updated_at=self.now,
                matches_scope="ALL",
                matches_start_date=None,
                matches_end_date=None,
                matches_count=1,
            )

            match_raw_payload = {
                "matchId": 4295493637,
                "eventFormat": "DOUBLES",
                "status": "ACTIVE",
                "created": "2026-02-20T01:10:41.233411Z",
                "modified": "2026-02-20T01:11:11.365011Z",
                "clientName": "Pickleball Brackets",
                "teams": [],
            }
            match_raw = PlayerMatchRaw(
                player_dupr_id=6886613721,
                match_id=4295493637,
                match_json=json.dumps(match_raw_payload),
                fetched_at=self.now,
            )

            singles_rows = [
                {"date": "2026-01-01", "matchDate": "2026-01-01", "rating": 4.10, "changedByAdmin": False},
                {"date": "2026-01-15", "matchDate": "2026-01-15", "rating": 4.32, "changedByAdmin": False},
            ]
            doubles_rows = [
                {"date": "2026-01-01", "matchDate": "2026-01-01", "rating": 4.50, "changedByAdmin": False},
                {"date": "2026-01-15", "matchDate": "2026-01-15", "rating": 4.69, "changedByAdmin": False},
            ]
            for idx, row in enumerate(singles_rows):
                sess.add(
                    PlayerRatingHistory(
                        player_dupr_id=6886613721,
                        rating_type="SINGLES",
                        scope_start_date="2025-12-01",
                        scope_end_date="2026-02-21",
                        row_index=idx,
                        rating_date=row["date"],
                        match_date=row["matchDate"],
                        rating=row["rating"],
                        changed_by_admin=row["changedByAdmin"],
                        rating_history_json=json.dumps(row),
                        fetched_at=self.now,
                    )
                )
            for idx, row in enumerate(doubles_rows):
                sess.add(
                    PlayerRatingHistory(
                        player_dupr_id=6886613721,
                        rating_type="DOUBLES",
                        scope_start_date="2025-12-01",
                        scope_end_date="2026-02-21",
                        row_index=idx,
                        rating_date=row["date"],
                        match_date=row["matchDate"],
                        rating=row["rating"],
                        changed_by_admin=row["changedByAdmin"],
                        rating_history_json=json.dumps(row),
                        fetched_at=self.now,
                    )
                )

            sess.add(snapshot)
            sess.add(match)
            sess.add(match_raw)
            sess.commit()

    def test_list_players_supports_name_and_id_filters(self):
        by_name = list_players(self.runtime, query="leo", limit=10, offset=0)
        self.assertEqual(by_name["total"], 1)
        self.assertEqual(len(by_name["rows"]), 1)
        self.assertEqual(by_name["rows"][0]["dupr_id"], 6886613721)

        by_id = list_players(self.runtime, query="6886613721", limit=10, offset=0)
        self.assertEqual(by_id["total"], 1)
        self.assertEqual(by_id["rows"][0]["name"], "Leo Sternlicht")

    def test_get_player_overview_includes_ratings_and_snapshot(self):
        detail = get_player_overview(self.runtime, 6886613721)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["dupr_id"], 6886613721)
        self.assertEqual(detail["ratings"]["singles"], "4.321")
        self.assertEqual(detail["ratings"]["doubles"], "4.689")
        self.assertEqual(detail["snapshot"]["matches_scope"], "ALL")
        self.assertEqual(detail["raw_player_metadata"]["fullName"], "Leo Sternlicht")

    def test_get_player_rating_series_returns_stats_and_trends(self):
        result = get_player_rating_series(
            self.runtime,
            6886613721,
            rating_type="both",
            start_date=None,
            end_date=None,
        )
        self.assertEqual(result["stats"]["singles"]["count"], 2)
        self.assertEqual(result["stats"]["doubles"]["count"], 2)
        self.assertAlmostEqual(result["stats"]["doubles"]["delta"], 0.19, places=3)
        self.assertNotEqual(result["trends"]["singles"], "(no data)")
        self.assertEqual(len(result["series"]["singles"]), 2)

    def test_match_summaries_and_match_detail_include_raw_metadata(self):
        summaries = get_player_match_summaries(
            self.runtime,
            6886613721,
            start_date=None,
            end_date=None,
        )
        self.assertEqual(len(summaries["rows"]), 1)
        row = summaries["rows"][0]
        self.assertEqual(row["result"], "L")
        self.assertEqual(row["format"], "DOUBLES")
        self.assertTrue(row["raw_available"])
        self.assertIn("Connor", row["partner"])

        detail = get_match_detail(self.runtime, 4295493637, player_dupr_id=6886613721)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["event_format"], "DOUBLES")
        self.assertEqual(detail["status"], "ACTIVE")
        self.assertEqual(detail["raw_player_dupr_id"], 6886613721)

    def test_list_raw_metadata_and_export_data(self):
        raw = list_raw_metadata(
            self.runtime,
            kind="rating",
            player_dupr_id=6886613721,
            match_id=None,
            limit=10,
            offset=0,
        )
        self.assertEqual(raw["count"], 4)
        self.assertIn("payload", raw["rows"][0])

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "players.csv"
            export = export_data(
                data={"rows": [{"dupr_id": 6886613721, "name": "Leo"}]},
                export_format="csv",
                output=str(out),
                clipboard=False,
                default_prefix=str(Path(tmpdir) / "fallback"),
            )
            self.assertTrue(export["file_written"])
            self.assertEqual(export["format"], "csv")
            self.assertTrue(out.exists())
            self.assertIn("dupr_id", out.read_text(encoding="utf-8"))

    def test_export_data_clipboard_failure_writes_fallback_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = str(Path(tmpdir) / "explore_rating")
            with patch("duprly.explore_services.copy_text", return_value=(False, "none", "clipboard unavailable")):
                export = export_data(
                    data={"rows": [{"dupr_id": 6886613721, "rating": 4.68}]},
                    export_format="json",
                    output=None,
                    clipboard=True,
                    default_prefix=prefix,
                )
            self.assertTrue(export["file_written"])
            self.assertFalse(export["clipboard_ok"])
            self.assertIn("clipboard unavailable", export["clipboard_reason"])
            self.assertIsNotNone(export["output"])
            self.assertTrue(Path(export["output"]).exists())


if __name__ == "__main__":
    unittest.main()
