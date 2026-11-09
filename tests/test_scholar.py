import io
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import scholar_search as s              
import web_research as w              

OPENALEX = {"results": [{"display_name": "RAG eval", "publication_year": 2026, "publication_date": "2026-03-01",
                         "cited_by_count": 12, "doi": "https://doi.org/10.1/ABC", "id": "https://openalex.org/W1",
                         "primary_location": {"source": {"display_name": "Journal X"}},
                         "authorships": [{"author": {"display_name": "A"}}, {"author": {"display_name": "B"}}],
                         "abstract_inverted_index": {"Hello": [0], "world": [1]}}]}
ARXIV = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2601.00001v2</id>
<published>2026-01-02T00:00:00Z</published><title> A  paper
 title </title><summary>Summary text</summary><author><name>Z</name></author></entry></feed>"""
GITHUB = {"items": [{"full_name": "o/r", "html_url": "https://github.com/o/r", "description": "d", "stargazers_count": 50,
                     "pushed_at": "2026-10-01T00:00:00Z", "language": "Python", "license": {"spdx_id": "MIT"},
                     "owner": {"login": "o"}, "archived": False}]}


class Parsers(unittest.TestCase):
    def test_openalex(self):
        paper = s.parse_openalex(OPENALEX)[0]
        self.assertEqual((paper["title"], paper["year"], paper["citations"], paper["doi"]), ("RAG eval", 2026, 12, "10.1/abc"))
        self.assertEqual(paper["abstract"], "Hello world")
        self.assertEqual(paper["venue"], "Journal X")

    def test_arxiv_and_dtd_rejected(self):
        paper = s.parse_arxiv(ARXIV)[0]
        self.assertEqual(paper["title"], "A paper title")
        self.assertEqual(paper["arxiv"], "2601.00001v2")
        self.assertIn("not peer reviewed", paper["venue"])
        with self.assertRaises(OSError):
            s.parse_arxiv('<!DOCTYPE x [<!ENTITY a "b">]><feed xmlns="http://www.w3.org/2005/Atom"/>')

    def test_github_semantic_crossref_elicit_consensus(self):
        repo = s.parse_github(GITHUB)[0]
        self.assertEqual((repo["stars"], repo["license"], repo["kind"]), (50, "MIT", "repository"))
        self.assertEqual(s.parse_semanticscholar({"data": [{"title": "T", "year": 2025, "citationCount": 3,
                                                           "externalIds": {"DOI": "10.2/X", "ArXiv": "2501.1"}}]})[0]["doi"], "10.2/x")
        crossref = s.parse_crossref({"message": {"items": [{"title": ["C"], "DOI": "10.3/Y", "issued": {"date-parts": [[2025, 6]]},
                                                            "is-referenced-by-count": 7, "author": [{"given": "G", "family": "F"}]}]}})[0]
        self.assertEqual((crossref["year"], crossref["date"], crossref["authors"]), (2025, "2025-06", ["G F"]))
        elicit = s.parse_elicit({"papers": [{"title": "E", "authors": ["x"], "year": 2024, "doi": None, "venue": "v",
                                             "citedByCount": 9, "urls": ["https://e.test/p"], "abstract": "a"}]})[0]
        self.assertEqual((elicit["citations"], elicit["url"]), (9, "https://e.test/p"))
        self.assertEqual(s.parse_consensus({"results": [{"title": "K", "year": 2023, "doi": "10.4/z"}]})[0]["title"], "K")


class Pipeline(unittest.TestCase):
    def test_merge_dedupes_by_doi_and_keeps_best_citations(self):
        a = s._paper("openalex", "Same", doi="10.1/a", citations=5, year=2025)
        b = s._paper("crossref", "Same!", doi="https://doi.org/10.1/A", citations=9, abstract="abs")
        merged = s.merge([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0]["citations"], merged[0]["abstract"], sorted(merged[0]["sources"])), (9, "abs", ["crossref", "openalex"]))

    def test_rank_modes(self):
        old_cited = s._paper("x", "old", year=2015, when="2015-01-01", citations=900)
        new_uncited = s._paper("x", "new", year=2026, when="2026-10-01", citations=0)
        today = date(2026, 11, 8)
        self.assertEqual(s.rank([old_cited, new_uncited], "best", today)[0]["title"], "old")
        self.assertEqual(s.rank([old_cited, new_uncited], "newest", today)[0]["title"], "new")

    def test_requests_use_https_hosts_and_modes(self):
        for source in ("openalex", "semanticscholar", "arxiv", "crossref", "github"):
            url = s.build_request(source, "rag eval", 5, 2025, "newest", {})[0]
            self.assertTrue(url.startswith("https://"), source)
        self.assertIn("publication_date:desc", s.build_request("openalex", "q", 5, None, "newest", {})[0])
        self.assertIn("cited_by_count:desc", s.build_request("openalex", "q", 5, None, "best", {})[0])
        self.assertIn("pushed:>=2025-01-01", s.build_request("github", "q", 5, 2025, "best", {})[0])
        self.assertIn("from_publication_date:2025-01-01", s.build_request("openalex", "q", 5, 2025, "best", {})[0])

    def test_keyed_sources_skipped_without_key_and_failures_isolated(self):
        def fetcher(url, headers=None, body=None):
            if "openalex" in url:
                return json.dumps(OPENALEX).encode()
            raise OSError("HTTP 429")

        report = s.run("q", ["openalex", "crossref", "elicit"], 5, None, "balanced", env={}, fetcher=fetcher)
        self.assertEqual(report["sources_used"], ["openalex"])
        self.assertIn("429", report["errors"]["crossref"])
        self.assertIn("ELICIT_API_KEY", report["errors"]["elicit"])
        self.assertEqual(report["results"][0]["title"], "RAG eval")

    def test_keys_go_in_the_right_headers(self):
        self.assertEqual(s.build_request("consensus", "q", 3, None, "best", {"CONSENSUS_API_KEY": "k"})[1], {"x-api-key": "k"})
        url, headers, body, _, _ = s.build_request("elicit", "q", 3, None, "best", {"ELICIT_API_KEY": "e"})
        self.assertEqual((url, headers, body), ("https://elicit.com/api/v2/search/papers", {"Authorization": "Bearer e"},
                                                {"query": "q", "maxResults": 3}))

    def test_render_separates_papers_from_repositories_and_warns(self):
        report = {"query": "q", "mode": "best", "since": None, "sources_used": ["openalex", "github"], "errors": {},
                  "results": [dict(s.parse_openalex(OPENALEX)[0], sources=["openalex"]), dict(s.parse_github(GITHUB)[0], sources=["github"])]}
        text = s.render(report)
        self.assertLess(text.index("Papers:"), text.index("Repositories:"))
        self.assertIn("untrusted data", text)

    def test_fetch_refuses_http_and_redirects(self):
        with self.assertRaises(OSError):
            s.fetch("http://example.test/")
        self.assertIsNone(s._NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test"))

    def test_fetch_maps_truncated_responses_to_oserror(self):
        import http.client

        class Boom:
            def open(self, request, timeout):
                raise http.client.IncompleteRead(b"x")

        with mock.patch.object(s.urllib.request, "build_opener", return_value=Boom()):
            with self.assertRaises(OSError):
                s.fetch("https://example.test/")


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class NewProviders(unittest.TestCase):
    def test_anthropic_config_payload_and_headers(self):
        config = w.resolve_config(env={"ANTHROPIC_API_KEY": "k", "RESEARCH_PROVIDER": "anthropic", "RESEARCH_MODEL": "claude-opus-5-5"}, depth="deep")
        self.assertEqual(config.endpoint(), "https://api.anthropic.com/v1/messages")
        self.assertEqual(config.headers(), {"x-api-key": "k", "anthropic-version": "2023-06-01"})
        payload = w.build_payload(config, "q")
        self.assertEqual(payload["tools"], [{"type": "web_search_20250305", "name": "web_search", "max_uses": 15}])
        self.assertEqual(payload["model"], "claude-opus-5-5")
        with self.assertRaises(w.ConfigError):
            w.resolve_config(env={"ANTHROPIC_API_KEY": "k", "RESEARCH_PROVIDER": "anthropic"})
        with self.assertRaises(w.ConfigError):
            w.resolve_config(env={"ANTHROPIC_API_KEY": "k", "RESEARCH_PROVIDER": "anthropic", "RESEARCH_MODEL": "m"}, effort="max")

    def test_anthropic_parses_citations_and_continues_pause_turn(self):
        config = w.resolve_config(env={"ANTHROPIC_API_KEY": "k", "RESEARCH_PROVIDER": "anthropic", "RESEARCH_MODEL": "m"})
        paused = {"stop_reason": "pause_turn", "content": [{"type": "server_tool_use", "id": "t"}]}
        final = {"stop_reason": "end_turn", "model": "m", "content": [
            {"type": "web_search_tool_result", "content": [{"type": "web_search_result", "url": "https://a.test/", "title": "A"}]},
            {"type": "text", "text": "Answer.", "citations": [{"type": "web_search_result_location", "url": "https://b.test/", "title": "B"}]}]}
        replies = iter([paused, final])
        seen = []

        def fake_open(request, timeout):
            seen.append(json.loads(request.data))
            return Resp(json.dumps(next(replies)).encode())

        with mock.patch.object(w, "_open", fake_open):
            result = w.research("q", config)
        self.assertEqual(result["answer"], "Answer.")
        self.assertEqual({c["url"] for c in result["citations"]}, {"https://a.test/", "https://b.test/"})
        self.assertEqual(seen[1]["messages"][-1]["role"], "assistant")

    def test_gemini_defaults_agents_by_depth_and_forces_background(self):
        base = {"GEMINI_API_KEY": "g", "RESEARCH_PROVIDER": "gemini"}
        self.assertEqual(w.resolve_config(env=base).model, "deep-research-preview-04-2026")
        config = w.resolve_config(env=base, depth="max")
        self.assertEqual(config.model, "deep-research-max-preview-04-2026")
        self.assertEqual(config.endpoint(), "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(config.headers(), {"x-goog-api-key": "g"})
        self.assertTrue(config.long_running())
        self.assertEqual(w.build_payload(config, "q"), {"input": "q", "agent": config.model, "background": True})

    def test_gemini_submit_poll_parse(self):
        config = w.resolve_config(env={"GEMINI_API_KEY": "g", "RESEARCH_PROVIDER": "gemini"})
        done = {"id": "int_1", "status": "completed", "steps": [
            {"type": "thought", "content": [{"type": "text", "text": "thinking"}]},
            {"type": "model_output", "content": [{"type": "text", "text": "Report. See [Doc](https://docs.test/x) and https://raw.test/y."}]}]}
        calls = []

        def fake_open(request, timeout):
            calls.append((request.get_method(), request.full_url))
            if request.get_method() == "POST":
                return Resp(json.dumps({"id": "int_1", "status": "in_progress"}).encode())
            return Resp(json.dumps(done).encode())

        with mock.patch.object(w, "_open", fake_open), mock.patch.object(w.time, "sleep"):
            result = w.research("q", config, timeout=60)
        self.assertEqual(calls[1], ("GET", "https://generativelanguage.googleapis.com/v1beta/interactions/int_1"))
        self.assertIn("Report.", result["answer"])
        self.assertEqual({c["url"] for c in result["citations"]}, {"https://docs.test/x", "https://raw.test/y"})

    def test_gemini_failed_status_is_an_error(self):
        config = w.resolve_config(env={"GEMINI_API_KEY": "g", "RESEARCH_PROVIDER": "gemini"})
        with self.assertRaises(w.ResearchError):
            w.parse_response({"status": "failed", "error": {"message": "quota"}}, config, "q")

    def test_background_flag_rejected_for_anthropic(self):
        config = w.resolve_config(env={"ANTHROPIC_API_KEY": "k", "RESEARCH_PROVIDER": "anthropic", "RESEARCH_MODEL": "m"})
        with self.assertRaises(w.ResearchError):
            w.research("q", config, background=True)


class OutputSize(unittest.TestCase):
    def test_scholar_render_caps_items_and_abstracts(self):
        papers = [dict(s._paper("openalex", f"Paper {i}", year=2025, citations=i, abstract="x" * 500), sources=["openalex"]) for i in range(12)]
        report = {"query": "q", "mode": "best", "since": None, "sources_used": ["openalex"], "errors": {}, "results": papers}
        text = s.render(report)
        self.assertEqual(text.count("Paper "), 6)
        self.assertLess(max(len(line) for line in text.splitlines() if line.startswith("   x")), 170)

    def test_long_answers_are_saved_and_cut(self):
        import tempfile
        result = {"provider": "p", "model": "m", "effort": "", "query": "What is X?", "citations": [], "answer": "line\n" * 4000}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "full.md"
            shown, saved = w.fit_output(result, 500, path)
            self.assertEqual(saved, path)
            self.assertLess(len(shown["answer"]), 700)
            self.assertIn("full.md", shown["answer"])
            self.assertGreater(len(path.read_text()), 15000)

    def test_short_answers_are_untouched(self):
        result = {"query": "q", "answer": "short"}
        self.assertEqual(w.fit_output(result, 500, None), (result, None))
        self.assertEqual(w.fit_output({"query": "q", "answer": "x" * 9999}, 0, None)[1], None)

    def test_slugify(self):
        self.assertEqual(w.slugify("What's new in Rust 1.90?!"), "what-s-new-in-rust-1-90")


if __name__ == "__main__":
    unittest.main()
