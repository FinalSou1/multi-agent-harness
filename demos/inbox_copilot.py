"""
Demo 1 - Inbox co-pilot.

Runs the harness over a small mock inbox and shows the whole loop:
  triage -> draft -> notify / remind -> HUMAN APPROVES before anything 'sends'.
One sample email is a prompt-injection attempt; watch it get quarantined.

Run:
    python demos/inbox_copilot.py              (offline, no key needed)
    # set GEMINI_API_KEY first for live model output
"""
import json
import sys
from pathlib import Path

# make the 'harness' package importable when run as a plain script
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.guardrails import ApprovalGate  # noqa: E402
from harness.llm import LLM  # noqa: E402
from harness.models import Email  # noqa: E402
from harness.orchestrator import AgentHarness  # noqa: E402


def load_emails():
    raw = json.loads((ROOT / "data" / "sample_emails.json").read_text(encoding="utf-8"))
    return [Email(**e) for e in raw]


def main():
    llm = LLM()
    mode = "LIVE (Gemini)" if llm.online else "OFFLINE (canned responses, no API key)"
    print(f"\nMode: {mode}\n")

    try:
        run = AgentHarness(llm).process_inbox(load_emails())
    except RuntimeError as exc:
        print(f"[live model unavailable] {exc}")
        return

    print("=" * 66)
    print("TRIAGE")
    print("=" * 66)
    for r in run.results:
        if r.quarantined:
            print(f"  [QUARANTINED] {r.email.subject}  ({r.quarantine_reason})")
        else:
            print(f"  [{r.triage.urgency:>2}/10] {r.triage.category:<10} {r.email.subject}")

    if run.notifications:
        print("\nNOTIFICATIONS")
        for n in run.notifications:
            print(f"  * {n.text}")

    if run.reminders:
        print("\nREMINDERS")
        for rm in run.reminders:
            print(f"  * {rm.text}  (due: {rm.due})")

    print("\n" + "=" * 66)
    print("DRAFTS AWAITING YOUR APPROVAL  (nothing sends without a yes)")
    print("=" * 66)

    def render(r):
        return (
            f"\n----- draft reply to {r.draft.to} -----\n"
            f"Subject: {r.draft.subject}\n\n{r.draft.body}\n"
        )

    approved, rejected = ApprovalGate().review(run.pending_drafts, render)

    outbox = [
        {"to": r.draft.to, "subject": r.draft.subject, "body": r.draft.body} for r in approved
    ]
    (ROOT / "outbox.json").write_text(json.dumps(outbox, indent=2), encoding="utf-8")

    print(
        f"\nDone. Approved & 'sent': {len(approved)}  |  "
        f"Rejected: {len(rejected)}  |  Quarantined: {len(run.quarantined)}"
    )
    print("Approved replies written to outbox.json (simulated send - no real email leaves your machine).")


if __name__ == "__main__":
    main()
