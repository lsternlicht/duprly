import os
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from duprly.dupr_db import Base, PlayerMatchRaw, PlayerMetadataSnapshot
from duprly.services import fetch_matches


def _player_payload(pid: int, name: str) -> dict:
    return {
        "id": pid,
        "fullName": name,
        "ratings": {
            "singles": "NR",
            "singlesVerified": "NR",
            "singlesProvisional": False,
            "doubles": "NR",
            "doublesVerified": "NR",
            "doublesProvisional": False,
        },
    }


def _match_payload(match_id: int, p1: int, p2: int) -> dict:
    return {
        "matchId": match_id,
        "userId": p1,
        "displayIdentity": f"M{match_id}",
        "confirmed": True,
        "eventDate": "2025-01-01",
        "eventName": "Test Match",
        "eventFormat": "SINGLES",
        "matchScoreAdded": True,
        "matchSource": "CLUB",
        "matchType": "SIDE_ONLY",
        "teams": [
            {
                "game1": 11,
                "game2": -1,
                "game3": -1,
                "winner": True,
                "player1": _player_payload(p1, f"Player {p1}"),
            },
            {
                "game1": 5,
                "game2": -1,
                "game3": -1,
                "winner": False,
                "player1": _player_payload(p2, f"Player {p2}"),
            },
        ],
    }


class DummyRuntime:
    def __init__(self, engine, client):
        self.engine = engine
        self.client = client

    def load_environment(self):
        return None


class DummyUI:
    @contextmanager
    def status(self, _):
        yield

    def track(self, iterable, _):
        return iterable


class FakeClient:
    def __init__(self):
        self.all_matches: list[dict] = []
        self.range_matches: list[dict] = []
        self.range_calls: list[tuple[str, str, str]] = []

    def auth_user(self, *_):
        return 0

    def get_member_match_history_all(self, dupr_id: str):
        return 200, list(self.all_matches)

    def get_member_match_history_range(self, dupr_id: str, start_date: str, end_date: str, limit: int = 100):
        self.range_calls.append((dupr_id, start_date, end_date))
        return 200, list(self.range_matches)


class ServicesPlayerMatchMetadataTests(unittest.TestCase):
    def setUp(self):
        self.original_access_token = os.getenv("DUPR_ACCESS_TOKEN")
        os.environ["DUPR_ACCESS_TOKEN"] = "test-token"

        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.client = FakeClient()
        self.runtime = DummyRuntime(self.engine, self.client)
        self.ui = DummyUI()

    def tearDown(self):
        if self.original_access_token is None:
            os.environ.pop("DUPR_ACCESS_TOKEN", None)
        else:
            os.environ["DUPR_ACCESS_TOKEN"] = self.original_access_token

    def test_fetch_matches_defaults_to_all_and_persists_snapshot(self):
        self.client.all_matches = [
            _match_payload(101, 1, 2),
            _match_payload(102, 1, 3),
        ]

        result = fetch_matches(self.runtime, self.ui, dupr_id="1", persist=True)

        self.assertEqual(result["scope"], "ALL")
        self.assertEqual(result["match_count"], 2)
        self.assertTrue(result["snapshot_updated"])
        self.assertEqual(result["raw_persisted"]["inserted"], 2)

        with Session(self.engine) as sess:
            raw_rows = sess.scalars(
                select(PlayerMatchRaw).where(PlayerMatchRaw.player_dupr_id == 1)
            ).all()
            self.assertEqual(len(raw_rows), 2)

            snap = sess.execute(
                select(PlayerMetadataSnapshot).where(PlayerMetadataSnapshot.player_dupr_id == 1)
            ).scalar_one_or_none()
            self.assertIsNotNone(snap)
            self.assertEqual(snap.matches_scope, "ALL")
            self.assertEqual(snap.matches_count, 2)
            self.assertIsNotNone(snap.matches_updated_at)

    def test_fetch_matches_one_sided_range_defaults_end_date(self):
        self.client.range_matches = [_match_payload(201, 8, 9)]

        result = fetch_matches(
            self.runtime,
            self.ui,
            dupr_id="8",
            start_date="2024-01-01",
            end_date=None,
            persist=False,
        )

        self.assertEqual(result["scope"], "RANGE")
        self.assertEqual(result["start_date"], "2024-01-01")
        self.assertEqual(result["end_date"], datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        self.assertEqual(len(self.client.range_calls), 1)
        self.assertEqual(self.client.range_calls[0][1], "2024-01-01")
        self.assertEqual(self.client.range_calls[0][2], datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    def test_raw_metadata_all_replaces_and_range_upserts(self):
        self.client.all_matches = [_match_payload(301, 10, 11), _match_payload(302, 10, 12)]
        fetch_matches(self.runtime, self.ui, dupr_id="10", persist=True)

        self.client.all_matches = [_match_payload(303, 10, 11)]
        fetch_matches(self.runtime, self.ui, dupr_id="10", persist=True)

        with Session(self.engine) as sess:
            rows = sess.scalars(
                select(PlayerMatchRaw).where(PlayerMatchRaw.player_dupr_id == 10)
            ).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].match_id, 303)

        self.client.range_matches = [_match_payload(303, 10, 11), _match_payload(304, 10, 15)]
        fetch_matches(
            self.runtime,
            self.ui,
            dupr_id="10",
            start_date="2025-01-01",
            end_date="2025-01-31",
            persist=True,
        )

        with Session(self.engine) as sess:
            rows = sess.scalars(
                select(PlayerMatchRaw).where(PlayerMatchRaw.player_dupr_id == 10)
            ).all()
            match_ids = sorted([row.match_id for row in rows])
            self.assertEqual(match_ids, [303, 304])

    def test_raw_metadata_persists_full_payload_without_field_loss(self):
        payload = _match_payload(401, 20, 21)
        payload["clientName"] = "Pickleball Brackets"
        payload["scoreFormat"] = {"format": "1 Game to 11", "games": 1, "winningScore": 11}
        payload["teams"][0]["preMatchRatingAndImpact"] = {
            "preMatchDoubleRatingPlayer1": 4.12,
            "matchDoubleRatingImpactPlayer1": -0.02,
        }
        self.client.all_matches = [payload]

        fetch_matches(self.runtime, self.ui, dupr_id="20", persist=True)

        with Session(self.engine) as sess:
            row = sess.scalars(
                select(PlayerMatchRaw).where(
                    PlayerMatchRaw.player_dupr_id == 20,
                    PlayerMatchRaw.match_id == 401,
                )
            ).one()
            raw = json.loads(row.match_json)
            self.assertEqual(raw["clientName"], "Pickleball Brackets")
            self.assertEqual(raw["scoreFormat"]["format"], "1 Game to 11")
            self.assertIn("preMatchRatingAndImpact", raw["teams"][0])


if __name__ == "__main__":
    unittest.main()
