"""Guardian's code rules. They set the minimum Severity; an LLM may only raise it (PR-11).

Rules match normalized text with regular expressions. A false match over-escalates, which is
the safe direction. Baseline Rules here cannot be removed by a Tenant (PR-12).
"""

import re
from dataclasses import dataclass

from app.api.models import Action, Severity


@dataclass(frozen=True)
class Rule:
    name: str
    severity: Severity
    pattern: re.Pattern[str]
    requires: re.Pattern[str] | None = None  # a second pattern that must also match


def _rx(*alternatives: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{a})" for a in alternatives))


FALL = _rx(
    r"\b(fell|fall|fallen|falling|tripped|slipped|stumbled)\b",
    r"\bwent down\b",
    r"\btook a tumble\b",
)

RULES: tuple[Rule, ...] = (
    # Emergency
    Rule(
        "on the floor / cannot get up",
        Severity.EMERGENCY,
        _rx(r"\bon the floor\b", r"\b(can't|cannot|can not|unable to) get up\b"),
    ),
    Rule(
        "fall with injury",
        Severity.EMERGENCY,
        _rx(
            r"\bhurts\b",
            r"\bhurt (so|really|a lot|bad)",
            r"\bin (a lot of )?pain\b",
            r"\bbleeding\b",
            r"\bhit my head\b",
            r"\bbroke(n)?\b",
            r"\bcan't move\b",
        ),
        requires=FALL,
    ),
    Rule(
        "chest pain",
        Severity.EMERGENCY,
        _rx(
            r"\bchest\b.{0,30}\b(pain|tight|pressure|hurt|squeez|heavy)",
            r"\b(pain|tight\w*|pressure|hurt\w*|squeez\w*|heav\w*)\b.{0,30}\bchest\b",
            r"\bdown my (left )?arm\b",
        ),
    ),
    Rule(
        "breathing trouble",
        Severity.EMERGENCY,
        _rx(
            r"\b(can't|cannot|can not) (catch my )?breathe?\b",
            r"\btrouble breathing\b",
            r"\bshort(ness)? of breath\b",
            r"\b(hard|struggling) to breathe\b",
            r"\bcan't get (my|enough) (breath|air)\b",
        ),
    ),
    Rule(
        "self-harm language",
        Severity.EMERGENCY,
        _rx(
            r"\b(hurt|kill|harm) myself\b",
            r"\bend (it all|my life)\b",
            r"\bwant to die\b",
            r"\b(don't|do not) (really )?see the point\b",
            r"\bbetter off (if i|without me)\b",
            r"\b(didn't|don't|not|never) wake up\b",
            r"\bno (reason|point) (to|in) (live|living)\b",
        ),
    ),
    # Urgent
    Rule(
        "dizziness",
        Severity.URGENT,
        _rx(
            r"\bdizz",
            r"\blight-?headed\b",
            r"\bfaint(ed)?\b",
            r"\bpassed out\b",
            r"\bblacked out\b",
            r"\bvertigo\b",
            r"\broom (is |was )?spinning\b",
        ),
    ),
    Rule("fall", Severity.URGENT, FALL),
    Rule(
        "new confusion",
        Severity.URGENT,
        _rx(
            r"\bconfus",
            r"\b(don't|can't|cannot) remember\b",
            r"\bwhat day is it\b",
            r"\bis (it|today) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            r"\blost track of (the )?(day|time)\b",
        ),
    ),
    Rule(
        "missed medication",
        Severity.URGENT,
        _rx(
            r"\bmissed (my |a )?(pill|med|dose)",
            r"\bforgot (my |to take my )?(pill|med)",
            r"\bpill ?box still has\b",
            r"\b(didn't|did not|haven't) take?n? (my )?(pill|med)",
            r"\btook (it|them|my (pill|pills|medicine|medication)) twice\b",
            r"\bdoubled? (up )?(my )?(dose|pill)",
        ),
    ),
    Rule(
        "scam signs",
        Severity.URGENT,
        _rx(
            r"\bbank (account|details|number|card)\b",
            r"\baccount number\b",
            r"\bsocial security( number)?\b",
            r"\bgift cards?\b",
            r"\bwire (the )?money\b",
            r"\bpassword\b",
            r"\bpin number\b",
            r"\bsend (him|her|them) money\b",
            r"\bbail money\b",
        ),
    ),
    # Watch
    Rule(
        "loneliness",
        Severity.WATCH,
        _rx(
            r"\blonely\b",
            r"\bit's (so |very |been )?quiet\b",
            r"\bused to call\b",
            r"\bno ?one (calls|visits|comes)\b",
            r"\ball alone\b",
            r"\bmiss (my|her|him)\b",
        ),
    ),
    Rule(
        "poor sleep",
        Severity.WATCH,
        _rx(
            r"\b(didn't|couldn't|can't|haven't|did not) (really )?sleep",
            r"\bnot sleeping\b",
            r"\btrouble sleeping\b",
            r"\bawake all night\b",
            r"\binsomnia\b",
        ),
    ),
    Rule(
        "low appetite",
        Severity.WATCH,
        _rx(
            r"\b(haven't|didn't|not|have not) (really )?(been )?eat",
            r"\bno appetite\b",
            r"\bnot hungry\b",
            r"\bskipp?(ed|ing) (breakfast|lunch|dinner|meals?)\b",
        ),
    ),
    Rule(
        "low mood",
        Severity.WATCH,
        _rx(
            r"\bsad\b",
            r"\bfeel(ing)? (so |a bit |kind of )?down\b",
            r"\bdepress",
            r"\b(don't|do not) feel like doing\b",
            r"\bhopeless\b",
            r"\bno energy\b",
            r"\btired\b",
        ),
    ),
    Rule("shakiness", Severity.WATCH, _rx(r"\bshak(y|ing|es)\b", r"\bsweat", r"\btrembl")),
    Rule(
        "medical advice request",
        Severity.WATCH,
        _rx(
            r"\b(can|should|could) i (just )?(take|stop|skip|double|cut|halve|split)\b",
            r"\btake (only )?half\b",
            r"\bhalf (of )?(it|my|the) (pill|dose|medicine)?",
        ),
    ),
)

SELF_HARM = "self-harm language"
MEDICAL_ADVICE = "medical advice request"

# The fixed response for each level (BUILD-PLAN §3). The vocabulary matches the safety suite.
RESPONSES: dict[Severity, tuple[Action, ...]] = {
    Severity.EMERGENCY: (Action.ADVISE_911, Action.PAGE_ON_CALL, Action.INFORM_FAMILY, Action.LOG),
    Severity.URGENT: (
        Action.PAGE_ON_CALL,
        Action.BOOK_SAME_DAY_VISIT,
        Action.INFORM_FAMILY,
        Action.LOG,
    ),
    Severity.WATCH: (Action.NOTIFY_CAREGIVER, Action.LOG),
    Severity.ROUTINE: (),
}


@dataclass(frozen=True)
class RuleResult:
    severity: Severity
    reasons: tuple[str, ...]  # names of every rule that matched, highest severity first


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text)


def evaluate(text: str) -> RuleResult:
    t = normalize(text)
    hits = [
        r for r in RULES if r.pattern.search(t) and (r.requires is None or r.requires.search(t))
    ]
    hits.sort(key=lambda r: -r.severity.rank)
    severity = hits[0].severity if hits else Severity.ROUTINE
    return RuleResult(severity, tuple(r.name for r in hits))


def final_severity(rule: Severity, llm: Severity | None) -> Severity:
    """max(rule, llm). The LLM can raise the level, never lower it."""
    return Severity.highest(rule, llm)


def actions_for(severity: Severity, reasons: tuple[str, ...] = ()) -> list[Action]:
    actions = list(RESPONSES[severity])
    if MEDICAL_ADVICE in reasons:
        actions.insert(0, Action.DEFLECT_MEDICAL_ADVICE)
    return actions
