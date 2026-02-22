import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from click.testing import CliRunner
from duprly.compat_click import click

from duprly.cli import cli
from duprly.commands.explore import _ensure_datasette_runtime, _run_datasette


class ExploreCommandTests(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("duprly.commands.explore.list_players")
    def test_explore_players_json(self, list_players):
        list_players.return_value = {
            "rows": [{"name": "Leo Sternlicht", "dupr_id": 6886613721, "singles": "4.3", "doubles": "4.6"}],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "query": None,
        }

        result = self.runner.invoke(cli, ["--json", "--no-interactive", "explore", "players"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"dupr_id": 6886613721', result.output)
        list_players.assert_called_once()

    @patch("duprly.commands.explore.get_player_overview")
    def test_explore_player_detail_json(self, get_player_overview):
        get_player_overview.return_value = {
            "dupr_id": 6886613721,
            "name": "Leo Sternlicht",
            "ratings": {"singles": "4.3", "doubles": "4.6"},
            "snapshot": {},
            "raw_player_metadata": {},
        }

        result = self.runner.invoke(cli, ["--json", "--no-interactive", "explore", "player", "6886613721"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"name": "Leo Sternlicht"', result.output)
        get_player_overview.assert_called_once()

    @patch("duprly.commands.explore.get_player_rating_series")
    def test_explore_player_ratings_json(self, get_player_rating_series):
        get_player_rating_series.return_value = {
            "dupr_id": 6886613721,
            "type_requested": "both",
            "start_date": None,
            "end_date": None,
            "series": {"singles": [{"rating": 4.1}], "doubles": [{"rating": 4.6}]},
            "stats": {"singles": {"count": 1}, "doubles": {"count": 1}},
            "trends": {"singles": ":-", "doubles": "=*"},
        }

        result = self.runner.invoke(
            cli,
            ["--json", "--no-interactive", "explore", "player", "6886613721", "ratings", "--type", "both"],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"type_requested": "both"', result.output)

    @patch("duprly.commands.explore.get_player_match_summaries")
    def test_explore_player_matches_json(self, get_player_match_summaries):
        get_player_match_summaries.return_value = {
            "dupr_id": 6886613721,
            "rows": [{"match_id": 123, "event_name": "Demo", "result": "W"}],
        }

        result = self.runner.invoke(
            cli,
            ["--json", "--no-interactive", "explore", "player", "6886613721", "matches"],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"match_id": 123', result.output)

    @patch("duprly.commands.explore.get_match_detail")
    def test_explore_match_json(self, get_match_detail):
        get_match_detail.return_value = {
            "match_id": 4295493637,
            "name": "Demo Match",
            "teams": [],
            "raw": {"status": "ACTIVE"},
        }

        result = self.runner.invoke(cli, ["--json", "--no-interactive", "explore", "match", "4295493637"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"match_id": 4295493637', result.output)

    @patch("duprly.commands.explore.list_raw_metadata")
    def test_explore_raw_json(self, list_raw_metadata):
        list_raw_metadata.return_value = {
            "kind": "match",
            "rows": [{"id": 1, "player_dupr_id": 6886613721, "match_id": 123, "payload": {"ok": True}}],
            "count": 1,
            "limit": 25,
            "offset": 0,
            "player_dupr_id": None,
            "match_id": None,
        }

        result = self.runner.invoke(cli, ["--json", "--no-interactive", "explore", "raw", "--kind", "match"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"kind": "match"', result.output)

    @patch("duprly.commands.explore._run_datasette")
    def test_explore_web_command_invokes_launcher(self, run_datasette):
        run_datasette.return_value = {"url": "http://127.0.0.1:8001/", "host": "127.0.0.1", "port": 8001, "opened": False}

        result = self.runner.invoke(cli, ["--json", "--no-interactive", "explore", "web", "--no-open"])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('"url": "http://127.0.0.1:8001/"', result.output)
        run_datasette.assert_called_once()

    @patch("duprly.commands.explore.importlib.util.find_spec")
    def test_datasette_runtime_check_reports_missing_pkg_resources(self, find_spec):
        def _fake_find_spec(name):
            if name == "datasette":
                return object()
            if name == "pkg_resources":
                return None
            return object()

        find_spec.side_effect = _fake_find_spec
        with self.assertRaises(click.ClickException) as ctx:
            _ensure_datasette_runtime()
        self.assertIn("setuptools<81", str(ctx.exception))

    @patch("duprly.commands.explore.export_data")
    @patch("duprly.commands.explore.list_players")
    def test_explore_players_export_calls_export_data(self, list_players, export_data):
        list_players.return_value = {
            "rows": [{"name": "Leo Sternlicht", "dupr_id": 6886613721}],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "query": None,
        }
        export_data.return_value = {
            "format": "csv",
            "output": "players.csv",
            "file_written": True,
            "clipboard": False,
            "clipboard_ok": False,
            "clipboard_mechanism": "none",
            "clipboard_reason": "",
            "bytes": 15,
        }

        result = self.runner.invoke(
            cli,
            [
                "--no-interactive",
                "explore",
                "players",
                "--export",
                "csv",
                "--output",
                "players.csv",
            ],
        )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        export_data.assert_called_once()

    @patch("duprly.commands.explore.build_datasette_metadata")
    @patch("duprly.commands.explore.subprocess.call", return_value=0)
    @patch("duprly.commands.explore.importlib.util.find_spec")
    def test_run_datasette_passes_metadata_and_template_flags(
        self,
        find_spec,
        _subprocess_call,
        build_datasette_metadata,
    ):
        def _fake_find_spec(name):
            if name in {"datasette", "pkg_resources", "datasette_vega"}:
                return object()
            return object()

        find_spec.side_effect = _fake_find_spec
        build_datasette_metadata.return_value = {"title": "x", "databases": {"dupr": {"queries": {}}}}

        messages = []

        class _UI:
            def print(self, message, style=None):
                messages.append((message, style))

        runtime = SimpleNamespace(db_path=Path("/tmp/dupr.sqlite"), engine=object())
        result = _run_datasette(runtime, _UI(), host="127.0.0.1", port=8001, open_browser=False)

        self.assertEqual(result["database"], "dupr")
        self.assertTrue(result["metadata_generated"])
        build_datasette_metadata.assert_called_once_with("dupr")
        call_args = _subprocess_call.call_args.args[0]
        self.assertIn("--metadata", call_args)
        self.assertIn("--template-dir", call_args)
        self.assertIn("default_page_size", call_args)
        self.assertIn("max_returned_rows", call_args)
        self.assertTrue(any("Starting web explorer" in msg for msg, _ in messages))

    @patch("duprly.commands.explore.build_datasette_metadata")
    @patch("duprly.commands.explore.subprocess.call", return_value=0)
    @patch("duprly.commands.explore.importlib.util.find_spec")
    def test_run_datasette_warns_when_vega_missing(
        self,
        find_spec,
        _subprocess_call,
        build_datasette_metadata,
    ):
        def _fake_find_spec(name):
            if name in {"datasette", "pkg_resources"}:
                return object()
            if name == "datasette_vega":
                return None
            return object()

        find_spec.side_effect = _fake_find_spec
        build_datasette_metadata.return_value = {"title": "x", "databases": {"dupr": {"queries": {}}}}
        messages = []

        class _UI:
            def print(self, message, style=None):
                messages.append((message, style))

        runtime = SimpleNamespace(db_path=Path("/tmp/dupr.sqlite"), engine=object())
        result = _run_datasette(runtime, _UI(), host="127.0.0.1", port=8001, open_browser=False)
        self.assertFalse(result["vega_plugin"])
        self.assertTrue(any("datasette-vega plugin not installed" in msg for msg, _ in messages))


if __name__ == "__main__":
    unittest.main()
