import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from duprly.dupr_db import Base, Player, Rating, ensure_rating_player_cache


class DuprDbRatingCacheTests(unittest.TestCase):
    def test_ensure_rating_player_cache_backfills_name_and_dupr_id(self):
        engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(engine)

        with Session(engine) as sess:
            p = Player(
                dupr_id=6886613721,
                full_name="Leo Sternlicht",
                first_name="Leo",
                last_name="Sternlicht",
                gender="MALE",
                age=35,
                image_url=None,
                email=None,
                phone=None,
                club_id=0,
            )
            p.rating = Rating(
                singles=4.2,
                singles_verified=4.2,
                is_singles_provisional=False,
                doubles=4.6,
                doubles_verified=4.6,
                is_doubles_provisional=False,
                player_dupr_id=None,
                player_full_name=None,
            )
            sess.add(p)
            sess.commit()

        ensure_rating_player_cache(engine)

        with Session(engine) as sess:
            row = sess.query(Rating).one()
            self.assertEqual(row.player_dupr_id, 6886613721)
            self.assertEqual(row.player_full_name, "Leo Sternlicht")


if __name__ == "__main__":
    unittest.main()
