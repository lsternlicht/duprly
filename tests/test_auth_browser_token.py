import base64
import json
import tempfile
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from duprly.cli import cli
from duprly.compat_click import click
from duprly.services import extract_dupr_token_from_browser


def _jwt_with_exp(exp: int) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"exp": exp, "sub": "test"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode("utf-8")).decode("utf-8").rstrip("=")
    p = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    return f"{h}.{p}.sig"


class _Cookie:
    def __init__(self, name: str, value: str, domain: str):
        self.name = name
        self.value = value
        self.domain = domain


class _FakeClient:
    def __init__(self, env_path: Path):
        self.env_path = str(env_path)
        self.access_token = None

    def save_token(self):
        with open(self.env_path, "w", encoding="utf-8") as f:
            json.dump({"access_token": self.access_token}, f)


class _FakeRuntime:
    def __init__(self, env_path: Path):
        self.client = _FakeClient(env_path)

    def load_environment(self):
        return None


class _FakeUI:
    @contextmanager
    def status(self, _):
        yield


class AuthBrowserTokenTests(unittest.TestCase):
    def test_extract_token_from_browser_and_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dupr_config.json"
            runtime = _FakeRuntime(config_path)
            ui = _FakeUI()
            token = _jwt_with_exp(2000000000)

            fake_module = types.SimpleNamespace(
                safari=lambda domain_name=None: [
                    _Cookie("dupr_access_token", token, ".dupr.com"),
                    _Cookie("dupr_refresh_token", "refresh-token", ".dupr.com"),
                ]
            )

            with patch.dict("sys.modules", {"browser_cookie3": fake_module}):
                result = extract_dupr_token_from_browser(runtime, ui, browser="safari", save=True)

            self.assertTrue(result["token_found"])
            self.assertTrue(result["refresh_token_found"])
            self.assertTrue(result["saved"])
            self.assertEqual(result["token"], token)
            self.assertIn("...", result["token_preview"])
            self.assertIsNotNone(result["token_expires_at_utc"])

            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["access_token"], token)

    def test_extract_token_raises_when_missing_cookie(self):
        runtime = _FakeRuntime(Path(tempfile.gettempdir()) / "dupr_unused.json")
        ui = _FakeUI()
        fake_module = types.SimpleNamespace(
            safari=lambda domain_name=None: [_Cookie("other_cookie", "x", ".dupr.gg")]
        )

        with patch.dict("sys.modules", {"browser_cookie3": fake_module}):
            with self.assertRaises(click.ClickException):
                extract_dupr_token_from_browser(runtime, ui, browser="safari")

    @patch("duprly.commands.auth.extract_dupr_token_from_browser")
    def test_auth_import_browser_token_hides_token_by_default(self, extract_mock):
        extract_mock.return_value = {
            "browser": "safari",
            "domain": "dupr.com",
            "cookie_name": "dupr_access_token",
            "token_found": True,
            "refresh_token_found": False,
            "saved": True,
            "config_path": "/tmp/dupr_config.json",
            "token_preview": "abc123...xyz789",
            "token_expires_at_utc": None,
            "token": "SECRET_TOKEN_VALUE",
        }
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "auth",
                "import-browser-token",
                "--browser",
                "safari",
            ],
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertNotIn("SECRET_TOKEN_VALUE", result.output)

    @patch("duprly.commands.auth.extract_dupr_token_from_browser")
    def test_top_level_import_browser_token_alias_works(self, extract_mock):
        extract_mock.return_value = {
            "browser": "comet",
            "domain": "dupr.com",
            "cookie_name": "dupr_access_token",
            "token_found": True,
            "refresh_token_found": False,
            "saved": False,
            "config_path": "/tmp/dupr_config.json",
            "token_preview": "abc123...xyz789",
            "token_expires_at_utc": None,
            "token": "SECRET_TOKEN_VALUE",
        }
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "import-browser-token",
                "--browser",
                "comet",
                "--no-save",
            ],
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Browser Token Import", result.output)

    def test_missing_domain_reports_suggested_domain(self):
        runtime = _FakeRuntime(Path(tempfile.gettempdir()) / "dupr_unused.json")
        ui = _FakeUI()
        token = _jwt_with_exp(2000000000)
        fake_module = types.SimpleNamespace(
            safari=lambda domain_name=None: (
                [_Cookie("dupr_access_token", token, ".dupr.com")]
                if domain_name is None
                else []
            )
        )

        with patch.dict("sys.modules", {"browser_cookie3": fake_module}):
            with self.assertRaises(click.ClickException) as ctx:
                extract_dupr_token_from_browser(runtime, ui, browser="safari", domain="dupr.gg")
        msg = str(ctx.exception)
        self.assertIn("Try `--domain dupr.com`", msg)

    def test_safari_js_fallback_extracts_cookie(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dupr_config.json"
            runtime = _FakeRuntime(config_path)
            ui = _FakeUI()
            token = _jwt_with_exp(2000000000)
            fake_module = types.SimpleNamespace(
                safari=lambda domain_name=None: []
            )

            class _Res:
                returncode = 0
                stdout = f"foo=bar; dupr_access_token={token}; other=1"
                stderr = ""

            with patch.dict("sys.modules", {"browser_cookie3": fake_module}):
                with patch("duprly.services.subprocess.run", return_value=_Res()):
                    result = extract_dupr_token_from_browser(runtime, ui, browser="safari", domain="dupr.com")
            self.assertEqual(result["token"], token)
            self.assertEqual(result["browser"], "safari-js")

    def test_comet_js_fallback_extracts_cookie_when_cookie_decryption_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dupr_config.json"
            runtime = _FakeRuntime(config_path)
            ui = _FakeUI()
            token = _jwt_with_exp(2000000000)

            def _raise_loader(**_kwargs):
                raise RuntimeError("Unable to get key for cookie decryption")

            fake_module = types.SimpleNamespace(chromium=_raise_loader)

            class _Res:
                returncode = 0
                stdout = f"dupr_access_token={token}; other=1"
                stderr = ""

            with patch.dict("sys.modules", {"browser_cookie3": fake_module}):
                with patch("duprly.services.subprocess.run", return_value=_Res()):
                    result = extract_dupr_token_from_browser(runtime, ui, browser="comet", domain="dupr.com")

            self.assertEqual(result["token"], token)
            self.assertEqual(result["browser"], "comet-js")


if __name__ == "__main__":
    unittest.main()
