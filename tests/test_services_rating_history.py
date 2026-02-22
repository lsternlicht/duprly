import os
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from duprly.dupr_db import Base, PlayerRatingHistory
from duprly.services import fetch_rating_history


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
        self.calls: list[tuple[str, str, str, str]] = []
        self.rows_by_type = {
            "SINGLES": [],
            "DOUBLES": [],
        }

    def auth_user(self, *_):
        return 0

    def get_player_rating_history(
        self,
        member_id: str,
        rating_type: str,
        start_date: str,
        end_date: str,
        limit: int = 100,
        sort_by: str = "asc",
    ):
        self.calls.append((member_id, rating_type, start_date, end_date))
        return 200, list(self.rows_by_type.get(rating_type, []))


def _row(day: str, rating: float, changed_by_admin: bool = False) -> dict:
    return {
        "date": day,
        "matchDate": day,
        "rating": rating,
        "changedByAdmin": changed_by_admin,
    }


class ServicesRatingHistoryTests(unittest.TestCase):
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

    def test_fetch_rating_history_defaults_last_two_years_and_both(self):
        self.client.rows_by_type["SINGLES"] = [_row("2026-01-01", 4.11), _row("2026-01-02", 4.12)]
        self.client.rows_by_type["DOUBLES"] = [_row("2026-01-03", 4.51)]

        result = fetch_rating_history(
            runtime=self.runtime,
            ui=self.ui,
            dupr_id="10",
            rating_type="both",
            start_date=None,
            end_date=None,
            persist=True,
        )

        expected_end = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")
        expected_start = (datetime.now(timezone.utc).date() - timedelta(days=730)).strftime("%Y-%m-%d")
        self.assertEqual(result["start_date"], expected_start)
        self.assertEqual(result["end_date"], expected_end)
        self.assertEqual(result["counts"]["singles"], 2)
        self.assertEqual(result["counts"]["doubles"], 1)
        self.assertEqual(len(self.client.calls), 2)

        with Session(self.engine) as sess:
            rows = sess.scalars(select(PlayerRatingHistory)).all()
            self.assertEqual(len(rows), 3)
            self.assertEqual(sorted({row.rating_type for row in rows}), ["DOUBLES", "SINGLES"])

    def test_fetch_rating_history_replaces_same_scope_snapshot(self):
        self.client.rows_by_type["SINGLES"] = [_row("2026-01-01", 4.11), _row("2026-01-02", 4.12)]
        fetch_rating_history(
            runtime=self.runtime,
            ui=self.ui,
            dupr_id="22",
            rating_type="singles",
            start_date="2025-12-01",
            end_date="2026-02-21",
            persist=True,
        )

        self.client.rows_by_type["SINGLES"] = [_row("2026-01-03", 4.13)]
        result = fetch_rating_history(
            runtime=self.runtime,
            ui=self.ui,
            dupr_id="22",
            rating_type="singles",
            start_date="2025-12-01",
            end_date="2026-02-21",
            persist=True,
        )

        self.assertEqual(result["persisted"]["singles"]["inserted"], 1)
        self.assertEqual(result["persisted"]["singles"]["deleted"], 2)
        with Session(self.engine) as sess:
            rows = sess.scalars(
                select(PlayerRatingHistory).where(
                    PlayerRatingHistory.player_dupr_id == 22,
                    PlayerRatingHistory.rating_type == "SINGLES",
                    PlayerRatingHistory.scope_start_date == "2025-12-01",
                    PlayerRatingHistory.scope_end_date == "2026-02-21",
                )
            ).all()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].rating, 4.13)

    def test_fetch_rating_history_no_persist_returns_zeroed_persistence(self):
        self.client.rows_by_type["DOUBLES"] = [_row("2026-01-03", 4.51)]

        result = fetch_rating_history(
            runtime=self.runtime,
            ui=self.ui,
            dupr_id="33",
            rating_type="doubles",
            start_date="2025-12-14",
            end_date="2026-02-21",
            persist=False,
        )

        self.assertEqual(result["persisted"]["doubles"]["inserted"], 0)
        with Session(self.engine) as sess:
            count = sess.query(PlayerRatingHistory).count()
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
