"""Plain data shapes passed between agents. Just containers, no logic."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Email:
    id: str
    sender: str
    subject: str
    body: str


@dataclass
class Triage:
    category: str      # e.g. "investor", "customer", "scheduling", "newsletter"
    urgency: int       # 1 (ignore) .. 10 (drop everything)
    reason: str


@dataclass
class Draft:
    email_id: str
    to: str
    subject: str
    body: str


@dataclass
class Reminder:
    email_id: str
    text: str
    due: str           # plain-language due date, e.g. "Friday"


@dataclass
class Notification:
    email_id: str
    text: str


@dataclass
class EmailResult:
    """Everything the harness produced for one email."""
    email: Email
    triage: Optional[Triage] = None
    draft: Optional[Draft] = None
    reminder: Optional[Reminder] = None
    notification: Optional[Notification] = None
    quarantined: bool = False          # guardrail blocked it
    quarantine_reason: str = ""


@dataclass
class InboxRun:
    """The result of processing a whole inbox."""
    results: List[EmailResult] = field(default_factory=list)

    @property
    def pending_drafts(self) -> List[EmailResult]:
        return [r for r in self.results if r.draft and not r.quarantined]

    @property
    def quarantined(self) -> List[EmailResult]:
        return [r for r in self.results if r.quarantined]

    @property
    def reminders(self) -> List[Reminder]:
        return [r.reminder for r in self.results if r.reminder]

    @property
    def notifications(self) -> List[Notification]:
        return [r.notification for r in self.results if r.notification]
