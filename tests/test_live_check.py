import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import live_check              


def stream(*events):
    return [json.dumps(e) for e in events]


GOOD = stream(
    {"type": "system", "subtype": "init", "plugins": [{"name": "all-you-need"}, {"name": "other"}]},
    {"type": "system", "subtype": "hook_response", "hook_name": "SessionStart:startup", "exit_code": 0, "output": "all-you-need harness is active. Rules:"},
    {"type": "system", "subtype": "hook_response", "hook_name": "SessionStart:startup", "exit_code": 0, "output": "other plugin"},
    {"type": "result", "result": "ROUTER 7", "is_error": False},
)


class Guard(unittest.TestCase):
    def test_denial_and_clean_reply_pass(self):
        lines = stream({"type": "user", "message": {"content": [{"type": "tool_result", "content": "all-you-need secret guard: /x/.env holds credentials"}]}},
                       {"type": "result", "result": "BLOCKED"})
        self.assertTrue(all(p for p, _ in live_check.evaluate_guard(lines).values()))

    def test_no_denial_fails(self):
        lines = stream({"type": "result", "result": "BLOCKED"})
        self.assertFalse(live_check.evaluate_guard(lines)["PreToolUse guard denied the credentials read"][0])

    def test_leaked_secret_fails(self):
        lines = stream({"type": "user", "message": "all-you-need secret guard"}, {"type": "result", "result": f"API_KEY={live_check.SECRET_VALUE}"})
        self.assertFalse(live_check.evaluate_guard(lines)["secret value stayed out of the reply"][0])


class Evaluate(unittest.TestCase):
    def test_all_checks_pass_on_a_good_session(self):
        checks = live_check.evaluate(GOOD)
        self.assertTrue(all(passed for passed, _ in checks.values()), checks)

    def test_missing_plugin_fails(self):
        lines = [line.replace("all-you-need", "x") for line in GOOD]
        self.assertFalse(live_check.evaluate(lines)["plugin loaded"][0])

    def test_failed_hook_is_reported(self):
        lines = stream(
            {"type": "system", "subtype": "init", "plugins": ["all-you-need"]},
            {"type": "system", "subtype": "hook_response", "hook_name": "SessionStart:startup", "exit_code": 1, "output": "all-you-need harness is active"},
            {"type": "result", "result": "ROUTER 7"})
        self.assertFalse(live_check.evaluate(lines)["SessionStart hook injected the core rules"][0])

    def test_other_plugins_hooks_do_not_count_as_ours(self):
        lines = stream({"type": "system", "subtype": "init", "plugins": ["all-you-need"]},
                       {"type": "system", "subtype": "hook_response", "exit_code": 0, "output": "caveman rules"},
                       {"type": "result", "result": "ROUTER 7"})
        self.assertFalse(live_check.evaluate(lines)["SessionStart hook injected the core rules"][0])

    def test_router_none_means_method_not_received(self):
        lines = [line.replace("ROUTER 7", "ROUTER none") for line in GOOD]
        self.assertFalse(live_check.evaluate(lines)["UserPromptSubmit hook delivered the research method"][0])

    def test_garbage_lines_are_ignored(self):
        checks = live_check.evaluate(["not json", "[]", "null"] + GOOD)
        self.assertTrue(all(passed for passed, _ in checks.values()))

    def test_empty_stream_fails_everything(self):
        self.assertFalse(any(passed for passed, _ in live_check.evaluate([]).values()))


if __name__ == "__main__":
    unittest.main()
