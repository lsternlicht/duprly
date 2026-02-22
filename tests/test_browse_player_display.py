import unittest

from duprly.commands.browse import _extract_player_ratings


class BrowsePlayerDisplayTests(unittest.TestCase):
    def test_extract_player_ratings_from_nested_ratings_object(self):
        pdata = {
            "id": 1,
            "fullName": "Aidan Bai",
            "ratings": {
                "singles": 4.3012,
                "doubles": 4.9981,
                "singlesVerified": 4.28,
                "doublesVerified": 4.95,
                "singlesProvisional": False,
                "doublesProvisional": True,
            },
        }

        ratings = _extract_player_ratings(pdata)
        self.assertEqual(ratings["singles"], "4.301")
        self.assertEqual(ratings["doubles"], "4.998")
        self.assertEqual(ratings["singles_verified"], "4.28")
        self.assertEqual(ratings["doubles_verified"], "4.95")
        self.assertEqual(ratings["singles_provisional"], "False")
        self.assertEqual(ratings["doubles_provisional"], "True")

    def test_extract_player_ratings_from_flat_fields(self):
        pdata = {
            "id": 2,
            "fullName": "Leo Sternlicht",
            "singles": "NR",
            "doubles": 4.686,
            "singlesVerified": None,
            "doublesVerified": 4.65,
            "singlesProvisional": True,
            "doublesProvisional": False,
        }

        ratings = _extract_player_ratings(pdata)
        self.assertEqual(ratings["singles"], "NR")
        self.assertEqual(ratings["doubles"], "4.686")
        self.assertEqual(ratings["singles_verified"], "NR")
        self.assertEqual(ratings["doubles_verified"], "4.65")
        self.assertEqual(ratings["singles_provisional"], "True")
        self.assertEqual(ratings["doubles_provisional"], "False")


if __name__ == "__main__":
    unittest.main()
