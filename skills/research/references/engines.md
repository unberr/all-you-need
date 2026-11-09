# Research engines: what each is, how to reach it, what was verified

Checked against the providers' own documentation in November 2026. Names, ids and limits change: confirm in the docs before relying on any row. "Verified" means an official page said it; "Not available" means no public API id or API existed when checked.

## General web research (use through `scripts/web_research.py`)
| Engine | Reach it with | Status |
| --- | --- | --- |
| Perplexity Agent API (`ultra`, `xhigh`) | `RESEARCH_PROVIDER=perplexity`, `--depth max\|deep`, key `PERPLEXITY_API_KEY` | Verified. `ultra` is for broad research and runs long; background mode. API credits are separate from a Perplexity Max subscription. |
| OpenAI Responses API with `web_search` | `RESEARCH_PROVIDER=openai-responses`, `RESEARCH_MODEL=gpt-6-astra`, key `OPENAI_API_KEY` | Verified. OpenAI's guidance for multi-step research is `gpt-6-astra` at `high` or `xhigh` reasoning. |
| Claude web search tool (Opus 5.5) | `RESEARCH_PROVIDER=anthropic`, `RESEARCH_MODEL=claude-opus-5-5`, key `ANTHROPIC_API_KEY`; `--depth` sets the search budget (5, 15, 30) | Verified: `claude-opus-5-5` is on Anthropic's list of models that support the `web_search_20250305` server tool. Citations come back on text blocks. Long turns can return `pause_turn`; the script continues them. |
| Gemini Deep Research agents (Interactions API) | `RESEARCH_PROVIDER=gemini`, key `GEMINI_API_KEY`; default agent `deep-research-preview-04-2026`, `--depth deep\|max` uses `deep-research-max-preview-04-2026` | Verified in Google's docs (preview ids, they may be renamed). Always runs in the background; up to 60 minutes. The poll URL and the `steps[-1]` result shape are from the docs; the id format was not shown, so a strange id is rejected rather than guessed. |
| Gemini 4 Carbon | none | Not available. Announced October 28, 2026; Google had published no API model id when checked, and the newest listed id was `gemini-4-argon`. Do not hardcode a guessed id. |
| Kimi K3.1 Pro (`kimi-k3.1-pro`, `kimi-k3`) | OpenAI-compatible: `RESEARCH_PROVIDER=openai-compatible`, `RESEARCH_BASE_URL=https://api.moonshot.ai/v1`, key `RESEARCH_API_KEY` | Verified as a model, not as a web researcher: Moonshot's docs say web search "is being updated and is not recommended for use in the near term". Use it for reasoning over sources you supply. |
| ChatGPT Deep Research | none (a ChatGPT product feature) | No separate API: use the Responses API row. The "30-minute" figure in lists is a product claim; the API depth is the `xhigh`/`max` reasoning setting. |

## Scholarly and code sources (use through `scripts/scholar_search.py`)
| Source | Key | Notes |
| --- | --- | --- |
| OpenAlex | none (`OPENALEX_MAILTO` optional, faster pool) | Broad, citation counts, open-access links. |
| Semantic Scholar | optional `SEMANTIC_SCHOLAR_API_KEY` | Keyless use is rate limited and often returns HTTP 429. |
| arXiv | none | Preprints, newest first. Not peer reviewed. |
| Crossref | none (`OPENALEX_MAILTO` is reused as the polite mailto) | DOI metadata; sometimes closes connections. |
| GitHub repositories | optional `GITHUB_TOKEN` | Code ideas: stars, last push, license, archived flag. Unauthenticated search is rate limited. |
| Consensus | `CONSENSUS_API_KEY` | Verified: `GET https://api.consensus.app/v1/search`, header `x-api-key`; the free plan has 30 calls a month and 1 request per second. The response field names were read from prose, so the parser is tolerant. |
| Elicit | `ELICIT_API_KEY` (Pro or above) | Verified: `POST https://elicit.com/api/v2/search/papers` with `query` and `maxResults`, bearer key. |
| SciSpace | not wired | A public beta API exists (`https://api.scispace.com/v1`, key required) but its request shapes were not checked, so it is not wired. |

Corpus sizes quoted for these tools differ between sources (Elicit 125 or 138 million papers; Consensus 220 or 400 million; SciSpace 280 million). Treat them as marketing figures, not evidence.
