import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import web_research              


class FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def agent_body(status="completed", text="Answer [1].", rid="resp_abc"):
    output = [{"type": "message", "content": [{"type": "output_text", "text": text, "annotations": [
        {"type": "url_citation", "url": "https://example.test/a", "title": "A", "start_index": 0, "end_index": 3}]}]}]
    return {"id": rid, "status": status, "model": "m", "output": output if status != "queued" else []}


class DepthProfiles(unittest.TestCase):
    def test_perplexity_depth_maps_to_effort_tiers(self):
        for depth, effort in (("standard", "low"), ("deep", "xhigh"), ("max", "ultra")):
            config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k"}, depth=depth)
            self.assertEqual(config.effort, effort)

    def test_explicit_effort_beats_depth(self):
        config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k"}, depth="max", effort="high")
        self.assertEqual(config.effort, "high")

    def test_depth_from_environment(self):
        config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k", "RESEARCH_DEPTH": "deep"})
        self.assertEqual(config.effort, "xhigh")

    def test_unknown_depth_rejected(self):
        with self.assertRaises(web_research.ConfigError):
            web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k"}, depth="astra-max")

    def test_ultra_and_max_are_long_running(self):
        ultra = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k"}, depth="max")
        low = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "k"})
        responses = web_research.resolve_config(env={"OPENAI_API_KEY": "k", "RESEARCH_PROVIDER": "openai-responses",
                                                     "RESEARCH_MODEL": "gpt-6-astra"}, depth="max")
        self.assertTrue(ultra.long_running())
        self.assertFalse(low.long_running())
        self.assertTrue(responses.long_running())


class ResponsesProvider(unittest.TestCase):
    ENV = {"OPENAI_API_KEY": "sk-test", "RESEARCH_PROVIDER": "openai-responses", "RESEARCH_MODEL": "gpt-6-astra"}

    def test_model_must_be_explicit(self):
        with self.assertRaises(web_research.ConfigError) as caught:
            web_research.resolve_config(env={"OPENAI_API_KEY": "k", "RESEARCH_PROVIDER": "openai-responses"})
        self.assertIn("does not guess", str(caught.exception))

    def test_endpoint_payload_and_default_effort(self):
        config = web_research.resolve_config(env=self.ENV)
        self.assertEqual(config.endpoint(), "https://api.openai.com/v1/responses")
        payload = web_research.build_payload(config, "what changed", "week")
        self.assertEqual(payload["model"], "gpt-6-astra")
        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        self.assertEqual(payload["reasoning"], {"effort": "medium"})
        self.assertIn("week", payload["input"])
        self.assertNotIn("background", payload)

    def test_background_flag_and_max_effort(self):
        config = web_research.resolve_config(env=self.ENV, depth="max")
        payload = web_research.build_payload(config, "q", background=True)
        self.assertEqual(payload["reasoning"], {"effort": "max"})
        self.assertTrue(payload["background"])

    def test_bad_reasoning_effort_rejected(self):
        with self.assertRaises(web_research.ConfigError):
            web_research.resolve_config(env=self.ENV, effort="astra-max")

    def test_flat_openai_citations_are_parsed(self):
        config = web_research.resolve_config(env=self.ENV)
        result = web_research.parse_response(agent_body(), config, "q")
        self.assertEqual(result["citations"], [{"url": "https://example.test/a", "title": "A"}])

    def test_incomplete_status_returns_partial(self):
        config = web_research.resolve_config(env=self.ENV)
        result = web_research.parse_response(agent_body(status="incomplete"), config, "q")
        self.assertTrue(result["incomplete"])
        self.assertIn("partial", web_research.render(result))

    def test_failed_status_is_an_error(self):
        config = web_research.resolve_config(env=self.ENV)
        with self.assertRaises(web_research.ResearchError):
            web_research.parse_response(agent_body(status="failed"), config, "q")


class BackgroundMode(unittest.TestCase):
    def setUp(self):
        self.config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret"}, depth="max")

    def test_submit_then_poll_until_completed(self):
        calls = []

        def fake_open(request, timeout):
            calls.append((request.get_method(), request.full_url))
            if request.get_method() == "POST":
                self.assertTrue(json.loads(request.data)["background"])
                return FakeResponse(json.dumps({"id": "resp_abc", "status": "queued"}).encode())
            step = sum(1 for method, _ in calls if method == "GET")
            status = "in_progress" if step < 2 else "completed"
            return FakeResponse(json.dumps(agent_body(status=status)).encode())

        with mock.patch.object(web_research, "_open", fake_open), mock.patch.object(web_research.time, "sleep"):
            result = web_research.research("q", self.config, background=True, timeout=600)
        self.assertEqual(result["answer"], "Answer [1].")
        self.assertEqual(calls[1], ("GET", "https://api.perplexity.ai/v1/agent/resp_abc"))
        self.assertEqual([method for method, _ in calls], ["POST", "GET", "GET"])

    def test_timeout_reports_id_for_resume(self):
        clock = iter([0, 1, 2000, 2001])

        def fake_open(request, timeout):
            return FakeResponse(json.dumps({"id": "resp_abc", "status": "in_progress"}).encode())

        with mock.patch.object(web_research, "_open", fake_open):
            with self.assertRaises(web_research.ResearchError) as caught:
                web_research.wait_for_completion(self.config, {"id": "resp_abc", "status": "queued"}, 100,
                                                 sleep=lambda s: None, clock=lambda: next(clock))
        self.assertIn("--resume resp_abc", str(caught.exception))

    def test_poll_interval_has_a_floor(self):
        sleeps = []
        states = iter([{"id": "r", "status": "completed", "output": []}])

        def fake_open(request, timeout):
            return FakeResponse(json.dumps(next(states)).encode())

        with mock.patch.object(web_research, "_open", fake_open):
            web_research.wait_for_completion(self.config, {"id": "r", "status": "in_progress"}, 100, poll_interval=0.1,
                                             sleep=sleeps.append, clock=lambda: 0)
        self.assertEqual(sleeps, [web_research.MIN_POLL_SECONDS])

    def test_response_id_is_validated(self):
        with self.assertRaises(web_research.ResearchError):
            web_research.poll_url(self.config, "../../v1/models")

    def test_missing_id_is_an_error(self):
        with self.assertRaises(web_research.ResearchError):
            web_research.wait_for_completion(self.config, {"status": "queued"}, 10)

    def test_background_rejected_for_plain_chat_provider(self):
        config = web_research.resolve_config(env={"RESEARCH_API_KEY": "k", "RESEARCH_PROVIDER": "openai-compatible",
                                                  "RESEARCH_MODEL": "m"})
        with self.assertRaises(web_research.ResearchError):
            web_research.research("q", config, background=True)

    def test_resume_fetches_by_id(self):
        def fake_open(request, timeout):
            self.assertEqual(request.get_method(), "GET")
            return FakeResponse(json.dumps(agent_body()).encode())

        with mock.patch.object(web_research, "_open", fake_open):
            result = web_research.resume("resp_abc", self.config)
        self.assertEqual(result["answer"], "Answer [1].")


class LinkChecking(unittest.TestCase):
    @staticmethod
    def resolver(addresses):
        def resolve(host, port, type=0):
            return [(2, 1, 6, "", (a, port)) for a in addresses]
        return resolve

    def test_public_https_allowed(self):
        allowed, _ = web_research.is_public_url("https://example.test/x", self.resolver(["93.184.216.34"]))
        self.assertTrue(allowed)

    def test_private_loopback_and_metadata_blocked(self):
        for address in ("127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254", "::1", "172.16.0.9"):
            allowed, reason = web_research.is_public_url("https://x.test/", self.resolver([address]))
            self.assertFalse(allowed, address)
            self.assertIn("non-public", reason)

    def test_any_private_address_blocks_the_host(self):
        allowed, _ = web_research.is_public_url("https://x.test/", self.resolver(["93.184.216.34", "10.0.0.1"]))
        self.assertFalse(allowed)

    def test_non_https_and_dns_failure_skipped(self):
        self.assertFalse(web_research.is_public_url("http://example.test/", self.resolver(["93.184.216.34"]))[0])
        self.assertFalse(web_research.is_public_url("file:///etc/passwd", self.resolver(["93.184.216.34"]))[0])

        def failing(host, port, type=0):
            raise OSError("no dns")

        with mock.patch.dict(web_research.os.environ, {}, clear=True):
            self.assertIn("no DNS", web_research.is_public_url("https://x.test/", failing)[1])

    def test_behind_a_proxy_names_are_judged_without_local_dns(self):
        def failing(host, port, type=0):
            raise OSError("no dns")

        with mock.patch.dict(web_research.os.environ, {"HTTPS_PROXY": "http://proxy.test:3128"}, clear=True):
            self.assertTrue(web_research.is_public_url("https://docs.example.com/a", failing)[0])
            for blocked in ("https://localhost/x", "https://db.internal/x", "https://printer.local/x", "https://10.0.0.1/x",
                            "https://169.254.169.254/latest", "https://intranet/x"):
                self.assertFalse(web_research.is_public_url(blocked, failing)[0], blocked)
            self.assertTrue(web_research.is_public_url("https://93.184.216.34/x", failing)[0])

    def test_check_links_annotates_and_never_fetches_blocked_hosts(self):
        fetched = []

        def fetch(url):
            fetched.append(url)
            return "dead (404)"

        citations = [{"url": "https://public.test/a", "title": "A"}, {"url": "https://internal.test/b", "title": "B"}]

        def resolve(host, port, type=0):
            address = "10.0.0.1" if host == "internal.test" else "93.184.216.34"
            return [(2, 1, 6, "", (address, port))]

        checked = web_research.check_links(citations, fetch=fetch, resolver=resolve)
        self.assertEqual(fetched, ["https://public.test/a"])
        self.assertEqual(checked[0]["link_status"], "dead (404)")
        self.assertIn("non-public", checked[1]["link_status"])
        self.assertNotIn("link_status", citations[0])

    def test_render_warns_about_dead_links(self):
        result = {"answer": "x", "citations": [{"url": "https://a.test/", "title": "A", "link_status": "dead (404)"}]}
        text = web_research.render(result)
        self.assertIn("[dead (404)]", text)
        self.assertIn("did not resolve", text)

    def test_fetch_status_classification(self):
        def raising(code):
            def fake(request, timeout):
                raise web_research.urllib.error.HTTPError(request.full_url, code, "x", {}, io.BytesIO(b""))
            return fake

        for code, expected in ((404, "dead"), (410, "dead"), (403, "unverified"), (301, "ok"), (500, "error")):
            with mock.patch.object(web_research, "_open", raising(code)):
                self.assertTrue(web_research._fetch_status("https://a.test/").startswith(expected), code)


if __name__ == "__main__":
    unittest.main()
