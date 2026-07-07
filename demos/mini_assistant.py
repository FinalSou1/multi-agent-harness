"""
Demo 2 - Mini assistant.

The SAME harness, reused for a general goal:
  plan -> fan out to researcher sub-agents -> synthesize one answer.

Run:
    python demos/mini_assistant.py "help me pick a database for a small app"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.llm import LLM  # noqa: E402
from harness.orchestrator import AgentHarness  # noqa: E402


def main():
    goal = " ".join(sys.argv[1:]).strip() or "plan a simple launch checklist for a small web app"
    llm = LLM()
    mode = "LIVE (Gemini)" if llm.online else "OFFLINE (canned responses)"
    print(f"\nMode: {mode}")
    print(f"Goal: {goal}\n")

    try:
        out = AgentHarness(llm).assist(goal)
    except RuntimeError as exc:
        print(f"[live model unavailable] {exc}")
        return

    print("PLAN (fanned out to sub-agents):")
    for i, s in enumerate(out["plan"], 1):
        print(f"  {i}. {s}")

    print("\nFINDINGS:")
    for f in out["findings"]:
        print(f"  - {f}")

    print("\nANSWER:")
    print(out["answer"])


if __name__ == "__main__":
    main()
