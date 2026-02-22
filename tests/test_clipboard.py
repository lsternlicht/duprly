import subprocess
import unittest
from unittest.mock import patch

from duprly.clipboard import copy_text


class ClipboardTests(unittest.TestCase):
    @patch("duprly.clipboard.subprocess.run")
    @patch("duprly.clipboard.platform.system", return_value="Darwin")
    def test_copy_text_uses_pbcopy_on_macos(self, _system, run_mock):
        run_mock.return_value = subprocess.CompletedProcess(args=["pbcopy"], returncode=0)

        ok, mechanism, reason = copy_text("hello")

        self.assertTrue(ok)
        self.assertEqual(mechanism, "pbcopy")
        self.assertEqual(reason, "")
        run_mock.assert_called_once()

    @patch("duprly.clipboard.subprocess.run")
    @patch("duprly.clipboard.platform.system", return_value="Linux")
    def test_copy_text_linux_falls_back_to_xclip(self, _system, run_mock):
        run_mock.side_effect = [
            FileNotFoundError(),
            subprocess.CompletedProcess(args=["xclip", "-selection", "clipboard"], returncode=0),
        ]

        ok, mechanism, reason = copy_text("hello")

        self.assertTrue(ok)
        self.assertEqual(mechanism, "xclip")
        self.assertEqual(reason, "")
        self.assertEqual(run_mock.call_count, 2)

    @patch("duprly.clipboard.subprocess.run")
    @patch("duprly.clipboard.platform.system", return_value="Linux")
    def test_copy_text_returns_reason_on_failure(self, _system, run_mock):
        run_mock.side_effect = [
            FileNotFoundError(),
            subprocess.CalledProcessError(returncode=1, cmd=["xclip"], stderr="clipboard unavailable"),
        ]

        ok, mechanism, reason = copy_text("hello")

        self.assertFalse(ok)
        self.assertEqual(mechanism, "none")
        self.assertIn("clipboard unavailable", reason)


if __name__ == "__main__":
    unittest.main()
