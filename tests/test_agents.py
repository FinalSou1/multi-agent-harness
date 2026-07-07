import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import agents
from harness.llm import LLM
from harness.models import Email

EMAIL = Email("9", "sam@acme.com", "Bug report", "The sync button is not working, please help.")


class TestAgents(unittest.TestCase):
    def setUp(self):
        self.llm = LLM(api_key="")  # offline

    def test_triage_urgency_in_range(self):
        t = agents.triage_email(self.llm, EMAIL)
        self.assertTrue(1 <= t.urgency <= 10)

    def test_draft_is_nonempty_reply(self):
        d = agents.draft_reply(self.llm, EMAIL, "warm")
        self.assertTrue(len(d.body) > 0)
        self.assertTrue(d.subject.startswith("Re:"))

    def test_plan_subtasks_returns_list(self):
        subs = agents.plan_subtasks(self.llm, "pick a hosting provider")
        self.assertTrue(isinstance(subs, list) and len(subs) >= 1)


if __name__ == "__main__":
    unittest.main()
