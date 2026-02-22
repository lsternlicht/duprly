import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from duprly.dupr_db import (
    Base,
    Match,
    MatchTeam,
    Player,
    PlayerRatingHistory,
    Rating,
    ensure_datasette_views,
)


class DuprDbDatasetteViewsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        today = datetime.now(timezone.utc).date()
        d1 = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        d2 = (today - timedelta(days=5)).strftime("%Y-%m-%d")

        with Session(self.engine) as sess:
            p1 = Player(
                dupr_id=1001,
                full_name="Player One",
                first_name="Player",
                last_name="One",
                gender="MALE",
                age=30,
                image_url=None,
                email=None,
                phone=None,
                club_id=1,
            )
            p1.rating = Rating(
                singles=4.1,
                singles_verified=4.1,
                is_singles_provisional=False,
                doubles=4.5,
                doubles_verified=4.5,
                is_doubles_provisional=False,
                player_dupr_id=1001,
                player_full_name="Player One",
            )

            p2 = Player(
                dupr_id=1002,
                full_name="Player Two",
                first_name="Player",
                last_name="Two",
                gender="MALE",
                age=31,
                image_url=None,
                email=None,
                phone=None,
                club_id=1,
            )
            p2.rating = Rating(
                singles=4.0,
                singles_verified=4.0,
                is_singles_provisional=False,
                doubles=4.3,
                doubles_verified=4.3,
                is_doubles_provisional=False,
                player_dupr_id=1002,
                player_full_name="Player Two",
            )

            p3 = Player(
                dupr_id=1003,
                full_name="Player Three",
                first_name="Player",
                last_name="Three",
                gender="MALE",
                age=29,
                image_url=None,
                email=None,
                phone=None,
                club_id=2,
            )
            p3.rating = Rating(
                singles=3.8,
                singles_verified=3.8,
                is_singles_provisional=False,
                doubles=4.1,
                doubles_verified=4.1,
                is_doubles_provisional=False,
                player_dupr_id=1003,
                player_full_name="Player Three",
            )

            p4 = Player(
                dupr_id=1004,
                full_name="Player Four",
                first_name="Player",
                last_name="Four",
                gender="MALE",
                age=28,
                image_url=None,
                email=None,
                phone=None,
                club_id=2,
            )
            p4.rating = Rating(
                singles=3.7,
                singles_verified=3.7,
                is_singles_provisional=False,
                doubles=4.0,
                doubles_verified=4.0,
                is_doubles_provisional=False,
                player_dupr_id=1004,
                player_full_name="Player Four",
            )

            match = Match(
                match_id=5001,
                name="Club Ladder",
                date=d2,
                match_type="DOUBLES",
                match_source="PARTNER",
                match_score_added=True,
            )
            team_win = MatchTeam(score1=11, score2=None, score3=None, is_winner=True)
            team_win.players.extend([p1, p2])
            team_lose = MatchTeam(score1=8, score2=None, score3=None, is_winner=False)
            team_lose.players.extend([p3, p4])
            match.teams.extend([team_win, team_lose])

            sess.add_all([p1, p2, p3, p4, match])
            sess.add_all(
                [
                    PlayerRatingHistory(
                        player_dupr_id=1001,
                        rating_type="DOUBLES",
                        scope_start_date=d1,
                        scope_end_date=d2,
                        row_index=0,
                        rating_date=d1,
                        match_date=d1,
                        rating=4.20,
                        changed_by_admin=False,
                        rating_history_json='{"rating": 4.20}',
                        fetched_at=datetime.now(timezone.utc),
                    ),
                    PlayerRatingHistory(
                        player_dupr_id=1001,
                        rating_type="DOUBLES",
                        scope_start_date=d1,
                        scope_end_date=d2,
                        row_index=1,
                        rating_date=d2,
                        match_date=d2,
                        rating=4.50,
                        changed_by_admin=False,
                        rating_history_json='{"rating": 4.50}',
                        fetched_at=datetime.now(timezone.utc),
                    ),
                ]
            )
            sess.commit()

        ensure_datasette_views(self.engine)

    def test_views_exist_and_return_expected_columns(self):
        with self.engine.connect() as conn:
            view_names = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='view'")
                ).fetchall()
            }
        expected = {
            "v_player_directory",
            "v_player_current_rating",
            "v_player_rating_points",
            "v_player_rating_summary_90d",
            "v_player_match_results",
            "v_player_partner_stats",
            "v_player_opponent_stats",
            "v_club_directory",
            "v_club_rating_snapshot",
            "v_club_top_risers_90d",
        }
        self.assertTrue(expected.issubset(view_names))

    def test_views_provide_player_trend_and_match_aggregates(self):
        with self.engine.connect() as conn:
            current = conn.execute(
                text(
                    "SELECT player_full_name, player_dupr_id FROM v_player_current_rating "
                    "WHERE player_dupr_id = 1001"
                )
            ).fetchone()
            self.assertIsNotNone(current)
            self.assertEqual(current[0], "Player One")

            summary = conn.execute(
                text(
                    "SELECT points_90d, delta_rating_90d "
                    "FROM v_player_rating_summary_90d "
                    "WHERE player_dupr_id = 1001 AND rating_type = 'DOUBLES'"
                )
            ).fetchone()
            self.assertIsNotNone(summary)
            self.assertEqual(summary[0], 2)
            self.assertGreater(summary[1], 0.0)

            partner = conn.execute(
                text(
                    "SELECT matches_played, wins FROM v_player_partner_stats "
                    "WHERE player_dupr_id = 1001 AND partner_dupr_id = 1002"
                )
            ).fetchone()
            self.assertIsNotNone(partner)
            self.assertEqual(partner[0], 1)
            self.assertEqual(partner[1], 1)

            opponent = conn.execute(
                text(
                    "SELECT matches_played, losses FROM v_player_opponent_stats "
                    "WHERE player_dupr_id = 1001 AND opponent_dupr_id = 1003"
                )
            ).fetchone()
            self.assertIsNotNone(opponent)
            self.assertEqual(opponent[0], 1)
            self.assertEqual(opponent[1], 0)

            club_snapshot = conn.execute(
                text(
                    "SELECT players, avg_doubles_rating FROM v_club_rating_snapshot WHERE club_id = 1"
                )
            ).fetchone()
            self.assertIsNotNone(club_snapshot)
            self.assertEqual(club_snapshot[0], 2)

            riser = conn.execute(
                text(
                    "SELECT delta_rating_90d FROM v_club_top_risers_90d "
                    "WHERE player_dupr_id = 1001 AND rating_type = 'DOUBLES'"
                )
            ).fetchone()
            self.assertIsNotNone(riser)
            self.assertGreater(riser[0], 0.0)

            player_dir = conn.execute(
                text(
                    "SELECT player_label FROM v_player_directory WHERE player_dupr_id = 1001"
                )
            ).fetchone()
            self.assertIsNotNone(player_dir)
            self.assertIn("Player One [1001]", player_dir[0])

            club_dir = conn.execute(
                text(
                    "SELECT club_name FROM v_club_directory WHERE club_id = 1"
                )
            ).fetchone()
            self.assertIsNotNone(club_dir)


if __name__ == "__main__":
    unittest.main()
