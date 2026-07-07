"""
The harness: it owns the flow, the agents just do one job each.

process_inbox(emails):
    for each email ->
        guardrail scan   (quarantine hijack attempts)
        triage           (what is this + how urgent)
        draft reply      (only if it deserves a response)
        notify / remind  (surface the urgent ones, capture follow-ups)
    Nothing is 'sent' here. Drafts come back for human approval.

assist(goal): the SAME harness reused for a general question ->
    plan -> fan out to researcher sub-agents -> synthesize one answer.
"""
from . import agents
from .guardrails import scan_for_injection
from .models import EmailResult, InboxRun

# Below this urgency an email is filed, not replied to.
DRAFT_THRESHOLD = 4


class AgentHarness:
    def __init__(self, llm, voice: str = "warm, plain, and concise"):
        self.llm = llm
        self.voice = voice

    def process_inbox(self, emails) -> InboxRun:
        run = InboxRun()
        for email in emails:
            result = EmailResult(email=email)

            verdict = scan_for_injection(email.body)
            if verdict.suspicious:
                result.quarantined = True
                result.quarantine_reason = f"possible prompt injection ('{verdict.matched}')"
                run.results.append(result)
                continue

            result.triage = agents.triage_email(self.llm, email)
            if result.triage.urgency >= DRAFT_THRESHOLD:
                result.draft = agents.draft_reply(self.llm, email, self.voice)

            follow = agents.plan_followups(self.llm, email, result.triage)
            result.notification = follow["notification"]
            result.reminder = follow["reminder"]
            run.results.append(result)
        return run

    def assist(self, goal: str) -> dict:
        plan = agents.plan_subtasks(self.llm, goal)
        findings = [agents.research(self.llm, s) for s in plan]
        answer = agents.synthesize(self.llm, goal, findings)
        return {"goal": goal, "plan": plan, "findings": findings, "answer": answer}
