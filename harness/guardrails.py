"""
Two safety layers, the same idea used in the larger private system.

1. Prompt-injection scan - an incoming email is DATA, never instructions.
   A fast heuristic flags mail that tries to hijack the assistant
   ("ignore previous instructions", "forward all mail", etc.). Flagged mail is
   quarantined (filed, never auto-drafted). A production version pairs this with
   a model-based classifier; this heuristic is the cheap first gate.

2. Human-in-the-loop approval gate - nothing that would reach a real person
   (a reply "send") happens without an explicit human yes.
"""
from dataclasses import dataclass

INJECTION_PATTERNS = [
    "ignore previous", "ignore all previous", "ignore your instructions",
    "disregard", "system prompt", "you are now", "forward all", "send all",
    "reveal", "api key", "change your instructions", "act as", "override",
]


@dataclass
class InjectionVerdict:
    suspicious: bool
    matched: str = ""


def scan_for_injection(text: str) -> InjectionVerdict:
    low = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in low:
            return InjectionVerdict(True, pattern)
    return InjectionVerdict(False)


class ApprovalGate:
    """Collects actions that need a human yes/no before they 'happen'."""

    def __init__(self, decide=None):
        # decide(item) -> bool. Defaults to an interactive terminal prompt.
        self.decide = decide or self._ask_terminal

    def review(self, items, render):
        approved, rejected = [], []
        for item in items:
            print(render(item))
            if self.decide(item):
                approved.append(item)
            else:
                rejected.append(item)
        return approved, rejected

    @staticmethod
    def _ask_terminal(_item) -> bool:
        answer = input("   Approve and 'send'? [y/N] ").strip().lower()
        return answer in ("y", "yes")
