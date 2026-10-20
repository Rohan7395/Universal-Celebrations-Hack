"""Grace, the Companion. She talks; she never decides. These are the lines she is handed back."""

from typing import Any

from app.api.models import Severity
from app.engine import tools

FALLBACK_SAY = "I've let your care team know."


def say_for(
    severity: Severity,
    *,
    self_harm: bool = False,
    medical_advice: bool = False,
    visit: dict[str, Any] | None = None,
    on_call: dict[str, Any] | None = None,
    caregiver: str | None = None,
) -> str:
    coordinator = tools.first_name(on_call["name"]) if on_call else "Someone"
    if severity is Severity.EMERGENCY:
        if self_harm:
            return (
                "Thank you for telling me. You matter to us. "
                f"{coordinator} from your care team will call you right now. "
                "If you feel unsafe, please call 988 or 911."
            )
        return (
            "Please call 911 now, or press your emergency button. "
            "I am telling your care team and your family right away."
        )
    if severity is Severity.URGENT:
        if visit:
            return (
                f"Thank you for telling me. {tools.first_name(visit['caregiver_name'])} will come"
                f" to see you today at {tools.clock_time(visit['starts_at'])}."
                f" {coordinator} from your care team will call you soon."
            )
        return (
            f"Thank you for telling me. {coordinator} from your care team will call you soon"
            " to arrange a visit today."
        )
    if severity is Severity.WATCH:
        prefix = (
            "Your doctor or pharmacist is the best person to ask about your medicine. "
            if medical_advice
            else ""
        )
        who = tools.first_name(caregiver) if caregiver else "your caregiver"
        return f"{prefix}Thank you for telling me. I'll let {who} know."
    return "Thank you for sharing that with me."
