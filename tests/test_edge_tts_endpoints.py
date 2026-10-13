"""Endpoint migration, idempotency and safe handling of upstream changes."""
import importlib.util
import stat
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location("patch_edge_tts", Path(__file__).resolve().parents[1] / "scripts/patch-edge-tts.py")
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

LEGACY = '''
BASE_URL = "speech.platform.bing.com/consumer/speech/synthesize/readaloud"
TRUSTED_CLIENT_TOKEN = "test-client-token"
WSS_URL = f"wss://{BASE_URL}/edge/v1?TrustedClientToken={TRUSTED_CLIENT_TOKEN}"
VOICE_LIST = f"https://{BASE_URL}/voices/list?trustedclienttoken={TRUSTED_CLIENT_TOKEN}"
SEC_MS_GEC_VERSION = "1-143.0.3650.75"
VOICE_HEADERS = {"Authority": "speech.platform.bing.com"}
'''


class EndpointMigration(unittest.TestCase):
    def test_speech_and_voice_list_move_together_preserving_token_version(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "constants.py"
            file.write_text(LEGACY)
            mode = stat.S_IMODE(file.stat().st_mode)
            self.assertTrue(patcher.patch_constants(file))
            namespace = {}
            exec(file.read_text(), namespace)
            for name, scheme, path in (("WSS_URL", "wss", "/tts/cognitiveservices/websocket/v1"), ("VOICE_LIST", "https", "/tts/cognitiveservices/voices/list")):
                url = urlsplit(namespace[name])
                self.assertEqual((url.scheme, url.hostname, url.path), (scheme, "api.msedgeservices.com", path))
                self.assertEqual(parse_qs(url.query), {"Ocp-Apim-Subscription-Key": ["test-client-token"]})
            self.assertEqual(namespace["SEC_MS_GEC_VERSION"], "1-143.0.3650.75")
            self.assertEqual(namespace["VOICE_HEADERS"]["Authority"], "api.msedgeservices.com")
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), mode)
            patched = file.read_bytes()
            self.assertFalse(patcher.patch_constants(file))
            self.assertEqual(file.read_bytes(), patched)

    def test_unrecognized_legacy_package_is_not_partially_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "constants.py"
            original = 'BASE_URL = "speech.platform.bing.com"\n'
            file.write_text(original)
            with self.assertRaisesRegex(RuntimeError, "refusing a partial"):
                patcher.patch_constants(file)
            self.assertEqual(file.read_text(), original)

    def test_future_upstream_endpoints_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "constants.py"
            original = 'WSS_URL = "wss://api.msedgeservices.com/future-endpoint"\n'
            file.write_text(original)
            self.assertFalse(patcher.patch_constants(file))
            self.assertEqual(file.read_text(), original)


if __name__ == "__main__":
    unittest.main()
