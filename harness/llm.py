"""
The single place the system talks to a language model.

Two modes, chosen automatically:

  * LIVE    - if GEMINI_API_KEY is set, calls Google Gemini over HTTPS
              (standard library only, no SDK).
  * OFFLINE - if no key is set, returns deterministic canned responses so the
              demos and the tests run anywhere with zero setup and zero cost.

Agents never care which mode is active; they just call run_json / run_text.
"""
import json
import os
import time
import urllib.error
import urllib.request

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)


class LLM:
    def __init__(self, model: str = "gemini-2.0-flash", api_key=None):
        # api_key="" forces OFFLINE even if the environment has a key (used by tests).
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.online = bool(self.api_key)

    # ---- public API used by the agents ----
    def run_text(self, task: str, prompt: str, context=None) -> str:
        if self.online:
            return self._gemini(prompt)
        return _MOCK_TEXT[task](context or {})

    def run_json(self, task: str, prompt: str, context=None) -> dict:
        if self.online:
            return _extract_json(self._gemini(prompt))
        return _MOCK_JSON[task](context or {})

    # ---- live model call (stdlib HTTPS) ----
    def _gemini(self, prompt: str, attempts: int = 3) -> str:
        url = GEMINI_URL.format(model=self.model, key=self.api_key)
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as exc:
                # 429 (rate limited) / 503 (overloaded) are transient - back off and retry.
                if exc.code in (429, 503) and attempt < attempts - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"Live Gemini call failed (HTTP {exc.code}). Unset GEMINI_API_KEY to run offline."
                ) from exc
            except (urllib.error.URLError, KeyError, IndexError, ValueError) as exc:
                raise RuntimeError(
                    f"Live Gemini call failed ({exc}). Unset GEMINI_API_KEY to run offline."
                ) from exc
        raise RuntimeError("Live Gemini call failed after retries. Unset GEMINI_API_KEY to run offline.")


def _extract_json(text: str) -> dict:
    """Tolerantly pull the first {...} block out of a model response."""
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(cleaned[start:end + 1])
        except ValueError:
            pass
    return {}


# --------------------------------------------------------------------------
# OFFLINE mocks: deterministic, keyword-driven stand-ins for a real model so
# the project runs and tests pass with no API key. Live mode never uses these.
# --------------------------------------------------------------------------
def _mock_triage(ctx) -> dict:
    email = ctx["email"]
    t = (email.subject + " " + email.body).lower()
    if any(w in t for w in ["invest", "term sheet", "funding", "raising", "raise"]):
        return {"category": "investor", "urgency": 9, "reason": "Investor interest; time-sensitive."}
    if any(w in t for w in ["not working", "failing", "bug", "error", "blocking", "help", "broken"]):
        return {"category": "customer", "urgency": 8, "reason": "Customer is blocked and needs a reply."}
    if any(w in t for w in ["meet", "call", "schedule", "friday", "calendar", "partnership"]):
        return {"category": "scheduling", "urgency": 7, "reason": "A meeting to coordinate."}
    if any(w in t for w in ["newsletter", "unsubscribe", "digest", "weekly"]):
        return {"category": "newsletter", "urgency": 2, "reason": "Low-priority bulk mail."}
    return {"category": "other", "urgency": 5, "reason": "General correspondence."}


def _mock_notify(ctx) -> dict:
    email = ctx["email"]
    triage = ctx["triage"]
    t = (email.subject + " " + email.body).lower()
    out = {"notify": triage.urgency >= 8, "notify_text": "", "reminder": "", "reminder_due": ""}
    if out["notify"]:
        out["notify_text"] = f"Urgent ({triage.category}): {email.subject} from {email.sender}"
    if "friday" in t:
        out["reminder"], out["reminder_due"] = f"Follow up: {email.subject}", "Friday"
    elif any(w in t for w in ["next week", "monday", "tomorrow", "end of day"]):
        out["reminder"], out["reminder_due"] = f"Follow up: {email.subject}", "soon"
    return out


def _mock_plan(ctx) -> dict:
    goal = ctx["goal"]
    return {"subtasks": [
        f"What is the core question behind: {goal}?",
        f"What are the main options for: {goal}?",
        f"What are the risks and the recommended next step for: {goal}?",
    ]}


def _mock_draft(ctx) -> str:
    email = ctx["email"]
    first = email.sender.split("@")[0].split(".")[0].capitalize()
    return (
        f"Hi {first},\n\n"
        f'Thanks for reaching out about "{email.subject}". I read it and I want to help. '
        f"Give me a little time to look into this and I'll come back with specifics.\n\n"
        f"Best,\nSerhii"
    )


def _mock_research(ctx) -> str:
    sub = ctx["subtask"]
    return f"On '{sub}': keep it simple, validate early, and pick the highest-impact option first."


def _mock_synthesize(ctx) -> str:
    goal = ctx["goal"]
    findings = ctx["findings"]
    body = "\n".join(f"- {f}" for f in findings)
    return f"Short answer for '{goal}':\n{body}\n\nStart small, test it, then iterate."


_MOCK_JSON = {"triage": _mock_triage, "notify": _mock_notify, "plan": _mock_plan}
_MOCK_TEXT = {"draft": _mock_draft, "research": _mock_research, "synthesize": _mock_synthesize}
