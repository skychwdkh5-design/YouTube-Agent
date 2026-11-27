import json, os, re, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(__file__))
import publish as P
import second_channel as S

ROOT = P.ROOT
WF = os.path.join(ROOT, ".github", "workflows")
GOOD = {"items": [{"id": S.EXPECTED_CHANNEL_ID, "snippet": {"title": "Такое бывает"}, "statistics": {"videoCount": "3"}}]}
OTHER = {"items": [{"id": "UC_orbital_atlas_000000000", "snippet": {"title": "Orbital Atlas"}, "statistics": {}}]}
TOK = {"refresh_token": "second-refresh-secret", "scope": "x"}


def wf(name, comments=False):
    t = open(os.path.join(WF, name), encoding="utf-8").read()
    return t if comments else "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#"))


class Auth(unittest.TestCase):
    def run_auth(self, channels):
        with mock.patch.object(P, "device_flow", return_value=TOK), \
             mock.patch.object(S, "access_token_from", return_value="at"), \
             mock.patch.object(P, "api", return_value=channels), \
             mock.patch.object(P, "store_secret") as st:
            try:
                out = S.cmd_auth(None)
            except P.PublishError as e:
                return st, e
            return st, out

    def test_match_writes_only_animaverse_secret(self):
        st, out = self.run_auth(GOOD)
        st.assert_called_once_with("ANIMAVERSE_YT_REFRESH_TOKEN", "second-refresh-secret")
        self.assertEqual(out["channel"]["id"], S.EXPECTED_CHANNEL_ID)

    def test_mismatch_stops_without_any_write(self):
        st, err = self.run_auth(OTHER)
        st.assert_not_called()
        self.assertIsInstance(err, P.PublishError)
        self.assertIn("mismatch", str(err))

    def test_no_channel_stops_without_any_write(self):
        st, err = self.run_auth({"items": []})
        st.assert_not_called()

    def test_second_login_cannot_overwrite_yt_refresh_token(self):
        # Even a direct call with the Orbital Atlas secret name is refused, and nothing reaches the API.
        with mock.patch.object(P, "store_secret") as st:
            for bad in ("YT_REFRESH_TOKEN", "YT_CLIENT_SECRET", "anything_else"):
                with self.assertRaises(P.PublishError):
                    S.store_second_secret("v", name=bad)
            st.assert_not_called()

    def test_every_write_in_second_flow_targets_animaverse(self):
        for channels in (GOOD, OTHER):
            st, _ = self.run_auth(channels)
            for c in st.call_args_list:
                self.assertEqual(c.args[0], "ANIMAVERSE_YT_REFRESH_TOKEN")
                self.assertNotEqual(c.args[0], "YT_REFRESH_TOKEN")

    def test_check_reads_new_secret_and_verifies_id(self):
        with mock.patch.dict(os.environ, {"ANIMAVERSE_YT_REFRESH_TOKEN": "r", "YT_REFRESH_TOKEN": "orbital"}), \
             mock.patch.object(S, "access_token_from", return_value="at") as at, \
             mock.patch.object(P, "api", return_value=GOOD):
            out = S.cmd_check(None)
        at.assert_called_once_with("r")                      # new secret, not YT_REFRESH_TOKEN
        self.assertEqual(out["channel"]["id"], S.EXPECTED_CHANNEL_ID)
        with mock.patch.dict(os.environ, {"ANIMAVERSE_YT_REFRESH_TOKEN": "r"}), \
             mock.patch.object(S, "access_token_from", return_value="at"), \
             mock.patch.object(P, "api", return_value=OTHER):
            with self.assertRaises(P.PublishError):
                S.cmd_check(None)

    def test_check_requires_new_secret(self):
        with mock.patch.dict(os.environ, {"YT_REFRESH_TOKEN": "orbital"}, clear=False):
            os.environ.pop("ANIMAVERSE_YT_REFRESH_TOKEN", None)
            with self.assertRaises(P.PublishError):
                S.cmd_check(None)

    def test_secret_value_redacted(self):
        with mock.patch.dict(os.environ, {"ANIMAVERSE_YT_REFRESH_TOKEN": "tok-abcdef-123"}):
            self.assertNotIn("tok-abcdef-123", P.redact("fail tok-abcdef-123"))

    def test_orbital_auth_unchanged(self):
        with mock.patch.object(P, "device_flow", return_value=TOK), mock.patch.object(P, "store_secret") as st:
            P.cmd_auth(None)
        st.assert_called_once_with("YT_REFRESH_TOKEN", "second-refresh-secret")


class Workflows(unittest.TestCase):
    def test_second_auth_workflow_never_touches_orbital_token(self):
        t = wf("youtube-auth-takoe.yml")
        self.assertNotIn("YT_REFRESH_TOKEN", t.replace("ANIMAVERSE_YT_REFRESH_TOKEN", ""))
        self.assertIn("second_channel.py auth", t)
        self.assertIn("workflow_dispatch", t)

    def test_second_check_workflow_reads_new_secret_only(self):
        t = wf("youtube-check-takoe.yml")
        self.assertIn("secrets.ANIMAVERSE_YT_REFRESH_TOKEN", t)
        self.assertNotIn("YT_REFRESH_TOKEN", t.replace("ANIMAVERSE_YT_REFRESH_TOKEN", ""))
        self.assertIn("second_channel.py check", t)
        for word in ("upload", "queue-run", "publish.py"):
            self.assertNotIn(word, t)

    def test_second_module_source_has_no_orbital_secret_write(self):
        src = open(os.path.join(os.path.dirname(__file__), "second_channel.py"), encoding="utf-8").read()
        self.assertEqual(re.findall(r'store_secret\(([^)]*)\)', src.replace("def store_second_secret(value, name=SECRET_NAME)", "")),
                         ["SECRET_NAME, value"])

    def test_original_workflows_unchanged_in_secrets(self):
        self.assertIn("secrets.YT_REFRESH_TOKEN", wf("youtube-check.yml"))
        self.assertIn("publish.py auth", wf("youtube-auth.yml"))


if __name__ == "__main__":
    unittest.main()
