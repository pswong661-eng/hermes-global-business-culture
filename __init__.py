"""global-business-culture plugin — registration.

Registers three deterministic culture-analysis tools, an in-session
``/culture <country> [task]`` command, and a bundled practitioner playbook
skill (``global-business-culture:business-culture-playbook``).
"""

import json
import logging
from pathlib import Path

try:  # normal case: imported as a package by the Hermes plugin loader
    from . import schemas, tools
except ImportError:  # imported bare (pytest walking the dash-named dir)
    import schemas  # noqa: F401  (plugin dir is on sys.path via conftest.py)
    import tools

logger = logging.getLogger(__name__)

_SKILL_MD = Path(__file__).resolve().parent / "skills" / "business-culture-playbook" / "SKILL.md"


def _format_slash_brief(raw_args):
    """Implement /culture <country> [task] as a compact markdown brief."""
    try:
        parts = (raw_args or "").strip().split()
        if not parts:
            return (
                "Usage: /culture <country> [task] — e.g. /culture Japan negotiation.\n"
                "Tasks: negotiation, first meeting, management, communication, payment, trip."
            )
        country = tools._clip(parts[0])
        task = tools._clip(" ".join(parts[1:])) or None
        payload = {"country": country}
        if task:
            payload["task"] = task
        data = json.loads(tools.culture_brief(payload))
        if "error" in data:
            sug = ", ".join(data.get("suggestions", [])[:6]) or "-"
            return "Not found: %s\nTry: %s" % (country, sug)
        lines = ["**%s** — %s | %s | Lewis: %s" % (
            data["country"],
            data["positioning"]["region"].split("(")[0].strip(),
            data["positioning"]["globe_cluster"],
            data["positioning"]["lewis_type"],
        )]
        if data.get("data_note"):
            lines.append("_%s_" % data["data_note"])
        lines.append("")
        lines.append("**Trust:** " + data["trust_currency"])
        lines.append("**Decisions:** " + data["decision_path"])
        lines.append("**Communication:** " + data["communication"])
        lines.append("**Contracts:** " + data["contract_treatment"])
        if data.get("task_hint"):
            lines.append("**Task hint (%s):** %s" % (data["task"], data["task_hint"]))
        lines.append("")
        lines.append("**Country highlights:**")
        for h in data.get("country_highlights", [])[:5]:
            lines.append("• " + h)
        lines.append("")
        lines.append("**Taboos:**")
        for t in data.get("taboos", [])[:3]:
            lines.append("• " + t)
        lines.append("")
        lines.append("Deeper: culture_gap_analysis(home='%s') for ranked misread risks." % data["country"])
        return "\n".join(lines)
    except Exception as exc:  # never raise from a command handler
        return "culture command failed: %s" % exc


def register(ctx):
    """Wire schemas to handlers; register tools, the /culture command, and the skill."""
    ctx.register_tool(
        name="culture_brief",
        toolset="culture",
        schema=schemas.CULTURE_BRIEF,
        handler=tools.culture_brief,
    )
    ctx.register_tool(
        name="culture_gap_analysis",
        toolset="culture",
        schema=schemas.CULTURE_GAP_ANALYSIS,
        handler=tools.culture_gap_analysis,
    )
    ctx.register_tool(
        name="culture_countries",
        toolset="culture",
        schema=schemas.CULTURE_COUNTRIES,
        handler=tools.culture_countries,
    )

    ctx.register_command(
        "culture",
        _format_slash_brief,
        description="Business-culture brief for a country (/culture Japan negotiation)",
        args_hint="<country> [task]",
    )

    if _SKILL_MD.exists():
        ctx.register_skill(
            "business-culture-playbook",
            _SKILL_MD,
            description="Deep practitioner playbook for cross-cultural business operations.",
        )
    else:  # pragma: no cover - packaging error guard
        logger.warning("global-business-culture: bundled SKILL.md missing at %s", _SKILL_MD)
