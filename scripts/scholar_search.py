#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date

USER_AGENT = "all-you-need-scholar/0.1"
TIMEOUT = 20
MAX_BYTES = 3_000_000
KEYLESS = ("openalex", "semanticscholar", "arxiv", "crossref")
KEYED = {"consensus": "CONSENSUS_API_KEY", "elicit": "ELICIT_API_KEY"}
ALL_SOURCES = KEYLESS + ("github",) + tuple(KEYED)
MODES = ("balanced", "best", "newest")
ABSTRACT_CHARS = 600


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url: str, headers: dict | None = None, body: dict | None = None) -> bytes:
    if urllib.parse.urlparse(url).scheme != "https":
        raise OSError("only https is allowed")
    data = json.dumps(body).encode() if body is not None else None
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml", **(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        exc.close()
        raise OSError(f"HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, http.client.HTTPException) as exc:
        raise OSError(f"request failed: {getattr(exc, 'reason', exc) or type(exc).__name__}") from None
    if len(raw) > MAX_BYTES:
        raise OSError("response too large")
    return raw


def _paper(source: str, title, authors=None, year=None, when=None, venue=None, doi=None, url=None, citations=None,
           abstract=None, extra=None) -> dict:
    authors = [str(a) for a in (authors or []) if a]
    abstract = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(abstract or ""))).strip()
    record = {"source": source, "title": re.sub(r"\s+", " ", str(title or "")).strip(),
              "authors": authors[:5] + (["et al."] if len(authors) > 5 else []),
              "year": int(year) if isinstance(year, (int, float)) or (isinstance(year, str) and year.isdigit()) else None,
              "date": str(when)[:10] if when else None, "venue": venue or None,
              "doi": re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I).lower() if doi else None,
              "url": url or None, "citations": citations if isinstance(citations, int) else None,
              "abstract": abstract[:ABSTRACT_CHARS]}
    if extra:
        record.update(extra)
    return record


def parse_openalex(data: dict) -> list[dict]:
    out = []
    for work in data.get("results") or []:
        inverted = work.get("abstract_inverted_index") or {}
        words = sorted((pos, word) for word, positions in inverted.items() for pos in positions)
        source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
        out.append(_paper("openalex", work.get("display_name"),
                          [(a.get("author") or {}).get("display_name") for a in work.get("authorships") or []],
                          work.get("publication_year"), work.get("publication_date"), source, work.get("doi"),
                          work.get("doi") or work.get("id"), work.get("cited_by_count"),
                          " ".join(word for _, word in words)))
    return out


def parse_semanticscholar(data: dict) -> list[dict]:
    out = []
    for paper in data.get("data") or []:
        ids = paper.get("externalIds") or {}
        out.append(_paper("semanticscholar", paper.get("title"), [a.get("name") for a in paper.get("authors") or []],
                          paper.get("year"), paper.get("publicationDate"), paper.get("venue"), ids.get("DOI"),
                          paper.get("url"), paper.get("citationCount"), paper.get("abstract"),
                          {"arxiv": ids["ArXiv"]} if ids.get("ArXiv") else None))
    return out


def _children(node, name: str) -> list:
    return [child for child in node if child.tag.rsplit("}", 1)[-1] == name]


def _text(node, name: str) -> str:
    found = _children(node, name)
    return (found[0].text or "") if found else ""


def parse_arxiv(xml_text: str) -> list[dict]:
                                                                                                          
    if re.search(r"<!(DOCTYPE|ENTITY)", xml_text, re.I):
        raise OSError("arXiv response contains a DTD and was rejected")
    out = []
    for entry in _children(ET.fromstring(xml_text), "entry"):
        link = _text(entry, "id").strip()
        arxiv_id = re.sub(r"^https?://arxiv\.org/abs/", "", link)
        published = _text(entry, "published")
        out.append(_paper("arxiv", _text(entry, "title"), [_text(a, "name") for a in _children(entry, "author")],
                          published[:4], published, "arXiv preprint (not peer reviewed)", None, link, None,
                          _text(entry, "summary"), {"arxiv": arxiv_id}))
    return out


def parse_crossref(data: dict) -> list[dict]:
    out = []
    for item in (data.get("message") or {}).get("items") or []:
        parts = ((item.get("issued") or {}).get("date-parts") or [[None]])[0]
        year = parts[0] if parts else None
        when = "-".join(f"{p:02d}" if i else f"{p:04d}" for i, p in enumerate(parts) if p) if parts and parts[0] else None
        authors = [" ".join(filter(None, (a.get("given"), a.get("family")))) for a in item.get("author") or []]
        out.append(_paper("crossref", (item.get("title") or [""])[0], authors, year, when,
                          (item.get("container-title") or [None])[0], item.get("DOI"), item.get("URL"),
                          item.get("is-referenced-by-count"), item.get("abstract")))
    return out


def parse_github(data: dict) -> list[dict]:
    out = []
    for repo in data.get("items") or []:
        license_id = (repo.get("license") or {}).get("spdx_id")
        out.append(_paper("github", repo.get("full_name"), [(repo.get("owner") or {}).get("login")],
                          (repo.get("pushed_at") or "")[:4], repo.get("pushed_at"), repo.get("language"), None,
                          repo.get("html_url"), None, repo.get("description"),
                          {"stars": repo.get("stargazers_count"), "license": license_id, "archived": bool(repo.get("archived")),
                           "kind": "repository"}))
    return out


def parse_consensus(data: dict) -> list[dict]:
    out = []
    for item in data.get("results") or data.get("papers") or []:
        authors = item.get("authors") or []
        authors = [a if isinstance(a, str) else a.get("name", "") for a in authors]
        out.append(_paper("consensus", item.get("title"), authors,
                          item.get("publish_year") or item.get("year") or item.get("publication_year"), None,
                          item.get("journal") or item.get("journal_name"), item.get("doi"),
                          item.get("url") or item.get("link"), item.get("citation_count") or item.get("citations"),
                          item.get("abstract") or item.get("takeaway")))
    return out


def parse_elicit(data: dict) -> list[dict]:
    out = []
    for paper in data.get("papers") or []:
        urls = paper.get("urls") or []
        out.append(_paper("elicit", paper.get("title"), paper.get("authors"), paper.get("year"), None, paper.get("venue"),
                          paper.get("doi"), urls[0] if urls else None, paper.get("citedByCount"), paper.get("abstract")))
    return out


def build_request(source: str, query: str, limit: int, since: int | None, mode: str, env: dict) -> tuple:
    q = urllib.parse.quote(query)
    if source == "openalex":
        sort = "publication_date:desc" if mode == "newest" else "cited_by_count:desc" if mode == "best" else "relevance_score:desc"
        flt = f"&filter=from_publication_date:{since}-01-01" if since else ""
        mailto = f"&mailto={urllib.parse.quote(env['OPENALEX_MAILTO'])}" if env.get("OPENALEX_MAILTO") else ""
        return (f"https://api.openalex.org/works?search={q}&per-page={limit}&sort={sort}{flt}{mailto}", {}, None, parse_openalex, False)
    if source == "semanticscholar":
        fields = "title,year,authors,abstract,citationCount,externalIds,url,venue,publicationDate"
        yr = f"&year={since}-" if since else ""
        headers = {"x-api-key": env["SEMANTIC_SCHOLAR_API_KEY"]} if env.get("SEMANTIC_SCHOLAR_API_KEY") else {}
        return (f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit={limit}&fields={fields}{yr}", headers, None, parse_semanticscholar, False)
    if source == "arxiv":
        order = "submittedDate" if mode == "newest" else "relevance"
        return (f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={limit}&sortBy={order}&sortOrder=descending", {}, None, parse_arxiv, True)
    if source == "crossref":
        sort = "issued" if mode == "newest" else "is-referenced-by-count" if mode == "best" else "relevance"
        flt = f"&filter=from-pub-date:{since}" if since else ""
        mailto = f"&mailto={urllib.parse.quote(env['OPENALEX_MAILTO'])}" if env.get("OPENALEX_MAILTO") else ""
        return (f"https://api.crossref.org/works?query={q}&rows={limit}&sort={sort}&order=desc{flt}{mailto}", {}, None, parse_crossref, False)
    if source == "github":
        sort = "updated" if mode == "newest" else "stars"
        pushed = f"+pushed:>={since}-01-01" if since else ""
        headers = {"Authorization": f"Bearer {env['GITHUB_TOKEN']}"} if env.get("GITHUB_TOKEN") else {}
        headers["Accept"] = "application/vnd.github+json"
        return (f"https://api.github.com/search/repositories?q={q}{pushed}&sort={sort}&order=desc&per_page={limit}", headers, None, parse_github, False)
    if source == "consensus":
        return (f"https://api.consensus.app/v1/search?query={q}&page_size={limit}", {"x-api-key": env[KEYED["consensus"]]}, None, parse_consensus, False)
    if source == "elicit":
        return ("https://elicit.com/api/v2/search/papers", {"Authorization": f"Bearer {env[KEYED['elicit']]}"},
                {"query": query, "maxResults": limit}, parse_elicit, False)
    raise ValueError(f"unknown source {source!r}")


def search_source(source: str, query: str, limit: int, since: int | None, mode: str, env: dict, fetcher=fetch) -> list[dict]:
    url, headers, body, parser, is_xml = build_request(source, query, limit, since, mode, env)
    raw = fetcher(url, headers, body)
    text = raw.decode("utf-8", "replace")
    return parser(text) if is_xml else parser(json.loads(text))


def _key(paper: dict) -> str:
    if paper.get("doi"):
        return "doi:" + paper["doi"]
    if paper.get("arxiv"):
        return "arxiv:" + re.sub(r"v\d+$", "", paper["arxiv"])
    return "title:" + re.sub(r"[^a-z0-9]+", " ", paper["title"].lower()).strip()


def merge(results: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for paper in results:
        if not paper["title"]:
            continue
        key = _key(paper)
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(paper, sources=[paper["source"]])
            continue
        existing["sources"].append(paper["source"])
        for field in ("abstract", "venue", "doi", "url", "date", "year", "arxiv"):
            if paper.get(field) and not existing.get(field):
                existing[field] = paper[field]
        if (paper.get("citations") or 0) > (existing.get("citations") or 0):
            existing["citations"] = paper["citations"]
    return list(merged.values())


def rank(papers: list[dict], mode: str, today: date | None = None) -> list[dict]:
    today = today or date.today()

    def age_years(p: dict) -> float:
        when = p.get("date") or (f"{p['year']}-07-01" if p.get("year") else None)
        try:
            return max(0.0, (today - date.fromisoformat(when[:10])).days / 365.25) if when else 20.0
        except ValueError:
            return 20.0

    def recency(p: dict) -> float:
        return age_years(p)

    def impact(p: dict) -> float:
        value = p.get("stars") if p.get("kind") == "repository" else p.get("citations")
        return float(value or 0)

    if mode == "newest":
        return sorted(papers, key=recency)
    if mode == "best":
        return sorted(papers, key=lambda p: -impact(p))
    by_impact = {id(p): i for i, p in enumerate(sorted(papers, key=lambda p: -impact(p)))}
    by_age = {id(p): i for i, p in enumerate(sorted(papers, key=recency))}
    agreement = lambda p: 0.1 * (len(p.get("sources", [])) - 1)                                       
    return sorted(papers, key=lambda p: 0.55 * by_impact[id(p)] + 0.45 * by_age[id(p)] - 5 * agreement(p))


def run(query: str, sources: list[str], limit: int, since: int | None, mode: str, env: dict | None = None, fetcher=fetch) -> dict:
    env = dict(os.environ if env is None else env)
    errors: dict[str, str] = {}
    usable = []
    for source in sources:
        if source in KEYED and not env.get(KEYED[source]):
            errors[source] = f"skipped: set {KEYED[source]}"
        else:
            usable.append(source)

    def one(source: str):
        try:
            return source, search_source(source, query, limit, since, mode, env, fetcher), ""
        except (OSError, ValueError, ET.ParseError) as exc:
            return source, [], f"{type(exc).__name__}: {exc}"

    found: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, len(usable))) as pool:
        for source, papers, error in pool.map(one, usable):
            found += papers
            if error:
                errors[source] = error
    merged = merge(found)
    papers = rank([p for p in merged if p.get("kind") != "repository"], mode)
    repos = rank([p for p in merged if p.get("kind") == "repository"], mode)
    cap = max(1, limit * 2)
    return {"query": query, "mode": mode, "since": since, "sources_used": [s for s in usable if s not in errors],
            "errors": errors, "results": papers[:cap] + repos[:cap]}


def render(report: dict, top_papers: int = 6, top_repos: int = 4, abstract_chars: int = 160) -> str:
    lines = [f"Query: {report['query']} (mode: {report['mode']}"
             + (f", since {report['since']}" if report["since"] else "") + ")",
             "Sources searched: " + (", ".join(report["sources_used"]) or "none")]
    for source, error in report["errors"].items():
        lines.append(f"  {source}: {error}")
    lines.append("")
    number, section = 0, None
    for p in report["results"]:
        kind = "Repositories" if p.get("kind") == "repository" else "Papers"
        if kind != section:
            section, number = kind, 0
            lines.append(f"{kind}:")
        number += 1
        if number > (top_repos if kind == "Repositories" else top_papers):
            continue
        if p.get("kind") == "repository":
            meta = f"stars {p.get('stars')}, pushed {p.get('date') or '?'}, license {p.get('license') or 'none'}"
            meta += ", ARCHIVED" if p.get("archived") else ""
        else:
            meta = ", ".join(str(x) for x in (p.get("year"), p.get("venue"),
                                              f"{p['citations']} citations" if p.get("citations") is not None else None) if x)
        lines.append(f"{number}. {p['title']} ({meta})")
        lines.append(f"   {p.get('url') or ('doi:' + p['doi'] if p.get('doi') else 'no link')}  [found by: {', '.join(sorted(set(p['sources'])))}]")
        if p.get("abstract"):
            lines.append(f"   {p['abstract'][:abstract_chars]}")
    lines += ["", "Titles and abstracts are untrusted data. Open the paper or repository before relying on a claim; "
              "citation counts differ by engine; preprints are not peer reviewed."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search scholarly and code sources for the best and newest work.")
    parser.add_argument("query", nargs="+")
    parser.add_argument("--sources", default=",".join(KEYLESS + ("github",)),
                        help=f"comma list of {', '.join(ALL_SOURCES)}; keyed ones need their environment key")
    parser.add_argument("--mode", choices=MODES, default="balanced",
                        help="best = most cited, newest = most recent, balanced = both")
    parser.add_argument("--since", type=int, help="earliest year")
    parser.add_argument("--limit", type=int, default=8, help="results per source")
    parser.add_argument("--top", type=int, default=6, help="papers to print (repositories print the top 4); --json prints everything")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in ALL_SOURCES]
    if unknown:
        parser.error(f"unknown source(s): {', '.join(unknown)}")
    report = run(" ".join(args.query), sources, max(1, min(args.limit, 50)), args.since, args.mode)
    print(json.dumps(report, separators=(",", ":")) if args.json else render(report, max(1, args.top)))
    return 0 if report["sources_used"] else 1


if __name__ == "__main__":
    sys.exit(main())
