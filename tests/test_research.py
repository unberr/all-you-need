import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import web_research              


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class ConfigTests(unittest.TestCase):
    def test_perplexity_is_selected_from_its_key(self):
        config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret"})
        self.assertEqual(config.provider, "perplexity")
        self.assertEqual(config.model, "")
        self.assertEqual(config.effort, "low")
        self.assertEqual(config.endpoint(), "https://api.perplexity.ai/v1/agent")

    def test_perplexity_model_and_effort_can_be_overridden(self):
        config = web_research.resolve_config(
            env={"PERPLEXITY_API_KEY": "secret", "RESEARCH_MODEL": "openai/gpt-6-luna",
                 "RESEARCH_EFFORT": "ultra"})
        self.assertEqual(config.model, "openai/gpt-6-luna")
        self.assertEqual(config.effort, "ultra")

    def test_pinned_effort_version_is_accepted(self):
        config = web_research.resolve_config(
            env={"PERPLEXITY_API_KEY": "secret", "RESEARCH_EFFORT": "low@2026-09-29.0"})
        self.assertEqual(config.effort, "low@2026-09-29.0")

    def test_effort_none_requires_a_model(self):
        with self.assertRaises(web_research.ConfigError) as caught:
            web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret", "RESEARCH_EFFORT": "none"})
        self.assertIn("RESEARCH_MODEL", str(caught.exception))

    def test_openai_compatible_requires_exact_model(self):
        with self.assertRaises(web_research.ConfigError) as caught:
            web_research.resolve_config(env={"RESEARCH_API_KEY": "secret"}, provider="openai-compatible")
        self.assertIn("RESEARCH_MODEL", str(caught.exception))

    def test_openai_compatible_accepts_exact_model(self):
        config = web_research.resolve_config(
            env={"RESEARCH_API_KEY": "secret", "RESEARCH_BASE_URL": "https://api.example.test/v1",
                 "RESEARCH_MODEL": "some-model-id"})
        self.assertEqual(config.endpoint(), "https://api.example.test/v1/chat/completions")

    def test_missing_key_names_the_variable(self):
        with self.assertRaises(web_research.ConfigError) as caught:
            web_research.resolve_config(env={}, provider="perplexity")
        self.assertIn("PERPLEXITY_API_KEY", str(caught.exception))

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(web_research.ConfigError):
            web_research.resolve_config(env={"RESEARCH_API_KEY": "secret"}, provider="other")

    def test_plain_http_is_rejected_except_localhost(self):
        for url in ("http://api.example.test/v1", "ftp://api.example.test/v1", "api.example.test"):
            with self.subTest(url=url):
                with self.assertRaises(web_research.ConfigError):
                    web_research.validate_base_url(url)
        self.assertEqual(web_research.validate_base_url("http://localhost:8000/v1"), "http://localhost:8000/v1")
        self.assertEqual(web_research.validate_base_url("https://api.example.test/v1/"),
                         "https://api.example.test/v1")


class PayloadTests(unittest.TestCase):
    def test_perplexity_payload_uses_agent_api(self):
        config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret"})
        payload = web_research.build_payload(config, "what changed", "month", 500)
        self.assertEqual(payload["input"], "what changed")
        self.assertEqual(payload["effort"], "low")
        self.assertNotIn("messages", payload)
        self.assertEqual(payload["tools"], [{"type": "web_search",
                                            "filters": {"search_recency_filter": "month"}}])
        self.assertEqual(payload["max_output_tokens"], 500)

    def test_perplexity_model_overrides_effort_model(self):
        config = web_research.resolve_config(
            env={"PERPLEXITY_API_KEY": "secret", "RESEARCH_MODEL": "openai/gpt-6-luna"})
        payload = web_research.build_payload(config, "q")
        self.assertEqual(payload["model"], "openai/gpt-6-luna")
        self.assertEqual(payload["effort"], "low")
        self.assertNotIn("max_output_tokens", payload)

    def test_openai_compatible_payload_is_chat_completions(self):
        config = web_research.resolve_config(env={"RESEARCH_API_KEY": "secret", "RESEARCH_MODEL": "m"})
        payload = web_research.build_payload(config, "what changed", "month", 500)
        self.assertEqual(payload["model"], "m")
        self.assertEqual(payload["max_tokens"], 500)
        self.assertIn("last month", payload["messages"][1]["content"])
        self.assertNotIn("effort", payload)
        self.assertNotIn("tools", payload)


class ParsingTests(unittest.TestCase):
    def setUp(self):
        self.config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret"})

    def test_agent_response_collects_message_and_search_results(self):
        data = {
            "status": "completed",
            "model": "openai/gpt-6-luna",
            "effort": "low@2026-09-29.0",
            "output": [
                {"type": "search_results", "results": [
                    {"id": 1, "url": "https://docs.example.test/a", "title": "A", "date": "2026-01-02"},
                    {"id": 2, "url": "https://docs.example.test/b", "title": "B"}]},
                {"type": "message", "content": [
                    {"type": "output_text", "text": "Answer [1][2]."}]},
            ],
            "usage": {"total_tokens": 12},
        }
        result = web_research.parse_response(data, self.config, "q")
        self.assertEqual(result["answer"], "Answer [1][2].")
        self.assertEqual(result["model"], "openai/gpt-6-luna")
        self.assertEqual(result["effort"], "low@2026-09-29.0")
        self.assertEqual(result["citations"][0], {"url": "https://docs.example.test/a", "title": "A",
                                                  "id": 1, "date": "2026-01-02"})
        self.assertEqual(len(result["citations"]), 2)

    def test_fetch_url_results_are_collected(self):
        data = {"status": "completed", "output": [
            {"type": "fetch_url_results", "contents": [{"url": "https://example.test/x", "title": "X"}]},
            {"type": "message", "content": [{"type": "output_text", "text": "Answer."}]}]}
        result = web_research.parse_response(data, self.config, "q")
        self.assertEqual(result["citations"], [{"url": "https://example.test/x", "title": "X"}])

    def test_failed_agent_response_is_rejected(self):
        with self.assertRaises(web_research.ResearchError) as caught:
            web_research.parse_response({"status": "failed", "error": {"message": "bad request"}},
                                        self.config, "q")
        self.assertIn("bad request", str(caught.exception))

    def test_chat_completions_response_still_parses(self):
        data = {"choices": [{"message": {"content": "Answer [source](https://example.test/s)."}}],
                "citations": ["https://example.test/s"],
                "usage": {"total_tokens": 3}}
        config = web_research.resolve_config(env={"RESEARCH_API_KEY": "secret", "RESEARCH_MODEL": "m"})
        result = web_research.parse_response(data, config, "q")
        self.assertEqual(result["answer"], "Answer [source](https://example.test/s).")
        self.assertEqual(result["citations"], [{"url": "https://example.test/s", "title": "source"}])

    def test_message_content_parts_are_joined(self):
        data = {"choices": [{"message": {"content": [{"type": "text", "text": "Part one. "},
                                                    {"type": "text", "text": "Part two."}]}}]}
        config = web_research.resolve_config(env={"RESEARCH_API_KEY": "secret", "RESEARCH_MODEL": "m"})
        result = web_research.parse_response(data, config, "q")
        self.assertEqual(result["answer"], "Part one. Part two.")

    def test_empty_answer_is_rejected(self):
        with self.assertRaises(web_research.ResearchError):
            web_research.parse_response({"status": "completed", "output": [
                {"type": "message", "content": [{"type": "output_text", "text": ""}]}]}, self.config, "q")

    def test_citation_is_numbered_once(self):
        plain = web_research.render_citation(1, {"url": "https://a.test", "title": "T"})
        tagged = web_research.render_citation(2, {"url": "https://b.test", "title": "U", "id": 3})
        self.assertEqual(plain, "1. T https://a.test")
        self.assertEqual(tagged, "2. [web:3] U https://b.test")

    def test_render_warns_when_no_citations(self):
        text = web_research.render({"answer": "Answer.", "citations": []})
        self.assertIn("unverified", text)

    def test_redact_removes_key_and_bearer_token(self):
        text = web_research.redact("token secret and Bearer abc123", "secret")
        self.assertNotIn("secret", text)
        self.assertNotIn("abc123", text)
        self.assertIn("[redacted]", text)


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.config = web_research.resolve_config(env={"PERPLEXITY_API_KEY": "secret"})

    def test_request_is_built_and_parsed(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(json.dumps({
                "status": "completed",
                "model": "openai/gpt-6-luna",
                "output": [
                    {"type": "search_results", "results": [
                        {"id": 1, "url": "https://example.test/s", "title": "S"}]},
                    {"type": "message", "content": [{"type": "output_text", "text": "Answer [1]."}]},
                ],
            }).encode())

        with mock.patch.object(web_research, "_open", fake_urlopen):
            result = web_research.research("question", self.config, "week", 500, 30)

        request = captured["request"]
        self.assertEqual(request.full_url, "https://api.perplexity.ai/v1/agent")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(captured["timeout"], 30)
        payload = json.loads(request.data)
        self.assertEqual(payload["input"], "question")
        self.assertEqual(payload["effort"], "low")
        self.assertEqual(payload["max_output_tokens"], 500)
        self.assertEqual(payload["tools"], [{"type": "web_search",
                                            "filters": {"search_recency_filter": "week"}}])
        self.assertEqual(result["answer"], "Answer [1].")
        self.assertEqual(result["citations"], [{"url": "https://example.test/s", "title": "S", "id": 1}])

    def test_redirects_are_refused_so_the_key_never_follows(self):
        request = web_research.urllib.request.Request("https://api.perplexity.ai/v1/agent", data=b"{}", method="POST")
        handler = web_research._NoRedirect()
        for code in (301, 302, 303, 307, 308):
            self.assertIsNone(handler.redirect_request(request, None, code, "Moved", {}, "https://evil.test/"))

    def test_redirect_response_is_reported_as_an_error(self):
        error = web_research.urllib.error.HTTPError(
            "https://api.perplexity.ai/v1/agent", 302, "Found", {}, io.BytesIO(b""))
        with mock.patch.object(web_research, "_open", side_effect=error):
            with self.assertRaises(web_research.ResearchError) as caught:
                web_research.research("question", self.config)
        self.assertIn("HTTP 302", str(caught.exception))

    def test_http_error_body_is_redacted(self):
        error = web_research.urllib.error.HTTPError(
            "https://api.perplexity.ai/v1/agent", 401, "Unauthorized", {},
            io.BytesIO(b'{"error":"bad key secret"}'))
        with mock.patch.object(web_research, "_open", side_effect=error):
            with self.assertRaises(web_research.ResearchError) as caught:
                web_research.research("question", self.config)
        self.assertIn("HTTP 401", str(caught.exception))
        self.assertNotIn("secret", str(caught.exception))

    def test_query_length_is_bounded(self):
        with self.assertRaises(web_research.ResearchError):
            web_research.research("x" * (web_research.MAX_QUERY_CHARS + 1), self.config)


class OutputTests(unittest.TestCase):
    def test_save_result_writes_markdown(self):
        result = {"provider": "perplexity", "model": "openai/gpt-6-luna", "effort": "low",
                  "query": "q", "answer": "Answer.",
                  "citations": [{"url": "https://example.test/x", "title": "X", "date": "2026-01-02"}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "research" / "result.md"
            web_research.save_result(result, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("# Research: q", text)
        self.assertIn("[X](https://example.test/x) (2026-01-02)", text)


class CliTests(unittest.TestCase):
    def test_missing_key_exits_with_config_error(self):
        env = {key: value for key, value in os.environ.items()
               if key not in {"PERPLEXITY_API_KEY", "RESEARCH_API_KEY", "OPENAI_API_KEY",
                              "RESEARCH_PROVIDER", "RESEARCH_MODEL", "RESEARCH_BASE_URL",
                              "RESEARCH_EFFORT"}}
        result = subprocess.run([sys.executable, "-B", "-I", str(SCRIPTS / "web_research.py"), "question"],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PERPLEXITY_API_KEY", result.stderr)

    def test_dry_run_never_prints_the_key(self):
        env = dict(os.environ, PERPLEXITY_API_KEY="secret-key-value", PERPLEXITY_EFFORT="")
        result = subprocess.run([sys.executable, "-B", "-I", str(SCRIPTS / "web_research.py"), "question", "--dry-run"],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("set (not shown)", result.stdout)
        self.assertNotIn("secret-key-value", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
