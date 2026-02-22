import unittest
from unittest.mock import patch

from duprly.interactive import run_interactive


class _DummyRuntime:
    def __init__(self):
        self.no_color = True


class _FakeUI:
    def __init__(self, no_color=False):
        self.answers = ["7", "q"]

    def panel(self, *_args, **_kwargs):
        return None

    def table(self, *_args, **_kwargs):
        return None

    def print(self, *_args, **_kwargs):
        return None

    def ask(self, *_args, **_kwargs):
        if self.answers:
            return self.answers.pop(0)
        return "q"

    def confirm(self, *_args, **_kwargs):
        return False


class InteractiveMenuTests(unittest.TestCase):
    @patch("duprly.interactive.run_explore_interactive")
    @patch("duprly.interactive.interactive_quick_status", return_value=[])
    @patch("duprly.interactive.UI", _FakeUI)
    def test_menu_routes_to_explore_saved_data(self, _status, run_explore_interactive):
        runtime = _DummyRuntime()
        run_interactive(runtime)
        run_explore_interactive.assert_called_once()


if __name__ == "__main__":
    unittest.main()
