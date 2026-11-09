---
description: Extract the factual claims from an answer or draft, verify each one against evidence, and label what remains unknown.
---

# /fact-check

Load the `all-you-need` skill and read `skills/all-you-need/references/rigor.md`. Check a draft or the last answer, not the whole repository.

1. Extract every claim that can be true or false: versions, APIs, flags, defaults, paths, counts, behavior, dates, prices, quotes and links. Ignore opinions and recommendations.
2. For each claim, choose the cheapest evidence:
   - local file or symbol: read it;
   - runtime behavior: run the smallest command or test;
   - version or API: read the installed source, lockfile or official docs for that version;
   - current external fact: check a dated primary source.
3. Mark each claim `Supported`, `Contradicted` or `Unknown`, with the evidence location or command and result.
4. Fix a contradicted claim. Remove a claim you cannot support, or label it `Not verified` with the reason.
5. Do not replace an unsupported claim with a different plausible claim. Do not invent a source to keep the sentence.

Report a short table: claim, status, evidence. Then list the claims you could not check and what would settle them. A clean result means every central claim is supported, not that every sentence is true.

If the draft contains exact user-supplied text, confirm it appears character for character before changing anything around it.
