"""Tool handlers — deterministic cross-cultural analysis over bundled research data.

Design rules (Hermes plugin contract):
1. Handlers receive ``args: dict`` and return a JSON string — ALWAYS, even on error.
2. Never raise. Catch everything and return error JSON.
3. Accept ``**kwargs`` for forward compatibility.
4. Pure stdlib, no network, no filesystem writes: safe offline enterprise use.
"""

import difflib
import json
import unicodedata
from pathlib import Path

_PLUGIN_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- data loading

def _load(name):
    path = _PLUGIN_DIR / "data" / name
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # pragma: no cover - defensive
        return {"_load_error": "Could not read %s: %s" % (name, exc)}

try:
    _COUNTRIES_DOC = _load("countries.json")
    _REGIONS_DOC = _load("regions.json")
    COUNTRIES = _COUNTRIES_DOC.get("countries", {})
    REGIONS = _REGIONS_DOC.get("regions", {})
except Exception:  # pragma: no cover - defensive
    COUNTRIES, REGIONS = {}, {}

# Meyer scale definitions: key -> (label, low pole, high pole)
MEYER_SCALES = [
    ("comm", "Communicating", "low-context (explicit, precise)", "high-context (implicit, layered)"),
    ("eval", "Evaluating", "direct negative feedback", "indirect negative feedback"),
    ("lead", "Leading", "egalitarian (boss as peer)", "hierarchical (status distance)"),
    ("decide", "Deciding", "consensual (group decides)", "top-down (boss decides)"),
    ("trust", "Trusting", "task-based trust", "relationship-based trust"),
    ("dis", "Disagreeing", "confrontational (open debate)", "avoids confrontation (harmony)"),
    ("sched", "Scheduling", "linear-time (agenda, punctuality)", "flexible-time (relationships > clock)"),
    ("pers", "Persuading", "applications-first (conclusion up front)", "principles-first (theory first)"),
]

HOFSTEDE_DIMS = [
    ("pdi", "Power Distance"),
    ("idv", "Individualism"),
    ("mas", "Achievement Orientation"),
    ("uai", "Uncertainty Avoidance"),
    ("lto", "Long-Term Orientation"),
    ("ivr", "Indulgence vs Restraint"),
]

# What a large gap on each scale means when the HOST is HIGHER / LOWER than home,
# plus the adaptation move. Written as (misread_risk, adaptation).
_GAP_MEANINGS = {
    "comm": {
        "higher": (
            "Host reads messages through context, relationships and what is NOT said. Your explicit "
            "directness may read as blunt or naive; their 'yes' may mean only 'I hear you'.",
            "Slow down, confirm understanding through a trusted intermediary, put key points in writing "
            "AFTER the meeting, listen for silence and hesitation as signals.",
        ),
        "lower": (
            "Host expects explicit, precise, written communication. Your implied meanings and softened "
            "phrasing read as evasive or unclear.",
            "Say exactly what you mean in writing; state conclusions and deadlines plainly; do not rely "
            "on shared context.",
        ),
    },
    "eval": {
        "higher": (
            "Host gives negative feedback indirectly (upgraders, private channels, third parties). Your "
            "direct criticism — even of work, not people — causes public loss of face.",
            "Wrap criticism: 'have you considered...', deliver hard messages privately or through a "
            "senior intermediary, praise publicly and correct privately.",
        ),
        "lower": (
            "Host gives blunt negative feedback as professional respect and expects the same back. Your "
            "softened hedging reads as unclear or even dishonest.",
            "Take blunt feedback as engagement, not offence; answer criticism with facts, not emotion; "
            "be specific about problems.",
        ),
    },
    "lead": {
        "higher": (
            "Host respects steep hierarchy: titles, seniority and protocol. Bypassing the senior person "
            "or treating the boss as a peer damages the relationship.",
            "Address and defer to the most senior person, use titles, send your own most-senior "
            "representative, never skip levels.",
        ),
        "lower": (
            "Host runs flat: the junior engineer may contradict the CEO and first names are immediate. "
            "Your formality reads as stiff or evasive.",
            "Drop the ceremony, engage everyone in the room as an equal, expect decisions to be "
            "challenged on merit regardless of rank.",
        ),
    },
    "decide": {
        "higher": (
            "The boss decides — quickly and personally. Endless group alignment looks weak; the deal "
            "lives or dies with one person.",
            "Identify and cultivate the single decision-maker; get their private blessing; expect fast "
            "verbal decisions that formal paper follows later.",
        ),
        "lower": (
            "Decisions are consensual: nemawashi-style alignment before the meeting. Your pressure for a "
            "fast decision feels aggressive and forces a face-losing answer.",
            "Socialize the idea with each stakeholder before the meeting; accept slow pre-alignment; "
            "once decided, the decision is solid and execution fast.",
        ),
    },
    "trust": {
        "higher": (
            "Host builds trust through meals, time, family talk and favors — contracts come AFTER "
            "confidence. Task-first behavior reads as cold and untrustworthy.",
            "Invest relationship time BEFORE negotiating terms: multiple meals, personal questions, "
            "patience; count months, not meetings.",
        ),
        "lower": (
            "Host builds trust through competence and delivery — dinners do not substitute for "
            "credentials. Relationship-first approaches can read as time-wasting or manipulative.",
            "Lead with track record, references, data and clean contracts; keep meetings efficient; "
            "deliver early to build credit.",
        ),
    },
    "dis": {
        "higher": (
            "Host avoids open disagreement to preserve harmony. Your devil's-advocate debating reads as "
            "hostility; their silence in the meeting hides real objections.",
            "Do not push for public debate; surface objections one-on-one afterwards; read warm "
            "agreement as politeness and verify through allies.",
        ),
        "lower": (
            "Host treats open disagreement as intellectual honesty and engagement. Your harmony-preserving "
            "silence reads as having no ideas or no spine.",
            "State your position and defend it with energy; do not take challenge personally; a heated "
            "exchange is often the start of the deal, not the end.",
        ),
    },
    "sched": {
        "higher": (
            "Host treats time as elastic: meetings start late, run long, and get interrupted — and "
            "deadlines are aspirations. Your clock discipline can read as distrust.",
            "Build 2-3x schedule slack, confirm everything the day before, keep warm personal follow-up, "
            "never show visible impatience.",
        ),
        "lower": (
            "Host treats the agenda and the clock as a contract. Lateness, overruns and reopened "
            "schedules read as disrespect or incompetence.",
            "Arrive 10 minutes early, send agendas ahead, end on time, treat deadlines as binding "
            "promises.",
        ),
    },
    "pers": {
        "higher": (
            "Host wants principles and method first — the 'why' and the theory before any "
            "recommendation. Leading with your conclusion reads as unsophisticated.",
            "Present the framework, method and reasoning first; let the conclusion arrive as a logical "
            "consequence; expect longer analysis phases.",
        ),
        "lower": (
            "Host wants the answer up front — executive summary, then support. Your methodical "
            "theory-first build-up reads as waffle.",
            "Lead with the recommendation and headline numbers; keep methodology in an appendix; expect "
            "interruptions with 'so what's the answer'.",
        ),
    },
}

# Task families -> weights per Meyer key (default 1.0)
_TASK_WEIGHTS = {
    "negotiation": {"trust": 1.7, "decide": 1.4, "dis": 1.3, "comm": 1.2, "sched": 1.1},
    "first_meeting": {"comm": 1.5, "trust": 1.4, "lead": 1.3, "eval": 1.1},
    "management": {"lead": 1.7, "eval": 1.5, "dis": 1.5},
    "communication": {"comm": 1.7, "eval": 1.4, "dis": 1.3},
    "payment": {"trust": 1.6, "sched": 1.4, "decide": 1.2},
    "trip": {"sched": 1.5, "lead": 1.3, "trust": 1.2, "comm": 1.1},
}

_TASK_HINTS = {
    "negotiation": "Anchor patiently, keep warmth while holding position, and remember a signed term sheet is the START of the relationship in relationship-based cultures — maintenance calls are part of the deal.",
    "first_meeting": "Bring your most senior credible person, respect titles and seating, let the host set pace and small-talk length, and exchange cards/contacts with ceremony where expected.",
    "management": "Give feedback privately and indirectly in high-context cultures (public correction causes resignations), and use one-on-ones to learn what the group will not say openly.",
    "communication": "Match directness to the host's Evaluating position: soften or sharpen your emails, put conclusions first or last, and follow verbal agreements with gentle written summaries.",
    "payment": "In relationship-first cultures, payment follows personal confidence more than invoice terms: maintain warm senior-to-senior contact, expect schedule slip, and avoid threatening escalation paths as a first move.",
    "trip": "Confirm every appointment the day before, build slack for late starts and extended hospitality, and never cut a courtesy ritual short to 'save time' — the ritual IS the business.",
}

_TASK_ALIASES = {
    "negotiate": "negotiation", "deal": "negotiation", "sales": "negotiation", "contract": "negotiation",
    "meeting": "first_meeting", "visit": "first_meeting", "intro": "first_meeting",
    "manage": "management", "feedback": "management", "team": "management", "hiring": "management",
    "email": "communication", "message": "communication", "messaging": "communication",
    "collect": "payment", "invoice": "payment",
    "travel": "trip", "gift": "trip",
}

# Country aliases: normalized alias -> canonical name
_ALIASES = {
    "usa": "United States", "us": "United States", "u s": "United States",
    "u s a": "United States", "america": "United States", "united states of america": "United States",
    "states": "United States",
    "uk": "United Kingdom", "u k": "United Kingdom", "britain": "United Kingdom",
    "great britain": "United Kingdom", "england": "United Kingdom", "scotland": "United Kingdom",
    "uae": "United Arab Emirates", "emirates": "United Arab Emirates", "dubai": "United Arab Emirates",
    "the emirates": "United Arab Emirates",
    "korea": "South Korea", "republic of korea": "South Korea", "rok": "South Korea",
    "holland": "Netherlands", "the netherlands": "Netherlands",
    "czech republic": "Czechia", "czech rep": "Czechia",
    "burma": "Myanmar",
    "lao": "Laos", "lao pdr": "Laos", "laos pdr": "Laos", "lao peoples democratic republic": "Laos",
    "viet nam": "Vietnam", "vietnam": "Vietnam",
    "hongkong": "Hong Kong", "hk": "Hong Kong", "hong kong sar": "Hong Kong",
    "saudi": "Saudi Arabia", "ksa": "Saudi Arabia", "kingdom of saudi arabia": "Saudi Arabia",
    "prc": "China", "pr china": "China", "peoples republic of china": "China",
    "russia federation": "Russia", "russian federation": "Russia",
    "turkiye": "Turkey",
    "deutschland": "Germany",
    "espana": "Spain",
    "nihon": "Japan", "nippon": "Japan",
    "suid afrika": "South Africa", "rsa": "South Africa",
    "new york": "United States",
}

_PUNCT_TABLE = dict.fromkeys(
    i for i in range(0x110000)
    if unicodedata.category(chr(i)).startswith("P")
)


def _normalize(text):
    """lowercase, strip diacritics + punctuation, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().translate(_PUNCT_TABLE)
    return " ".join(text.split())


# normalized-name -> canonical name (case/diacritic-insensitive exact index)
_NORM_INDEX = {_normalize(name): name for name in COUNTRIES}


def _resolve_country(raw):
    """Return (canonical_name or None, suggestions list)."""
    if not isinstance(raw, str) or not raw.strip():
        return None, sorted(COUNTRIES)[:8]
    norm = _normalize(raw)
    if not norm:
        return None, sorted(COUNTRIES)[:8]
    if norm in _NORM_INDEX:
        return _NORM_INDEX[norm], []
    for cand in (norm, norm.replace("the ", "", 1), "the " + norm):
        if cand in _ALIASES and _ALIASES[cand] in COUNTRIES:
            return _ALIASES[cand], []
    # containment: "united states inc" / "south korean market"
    contains = [name for name in sorted(COUNTRIES) if norm in _normalize(name)]
    if len(contains) == 1:
        return contains[0], []
    close_norms = difflib.get_close_matches(norm, list(_NORM_INDEX), n=4, cutoff=0.72)
    close = [_NORM_INDEX[c] for c in close_norms]
    if len(close) == 1 and not contains:
        return close[0], []
    pool = contains + [c for c in close if c not in contains]
    return None, (pool if pool else sorted(COUNTRIES)[:6])


def _resolve_task(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    norm = _normalize(raw)
    for key in _TASK_WEIGHTS:
        if key.replace("_", " ") in norm or norm in key:
            return key
    for alias, task in _TASK_ALIASES.items():
        if alias in norm:
            return task
    return None


def _risk(abs_delta):
    if abs_delta >= 30:
        return "HIGH"
    if abs_delta >= 18:
        return "MODERATE"
    return "LOW"


# Security bound: country/task/query strings never legitimately exceed this.
# Clipping at entry caps compute on pathological inputs and keeps error echoes
# small so a hostile tool argument cannot flood the model context.
_MAX_INPUT = 200


def _clip(raw):
    """Bound an attacker-influenced string to _MAX_INPUT chars (+ length marker)."""
    if not isinstance(raw, str) or len(raw) <= _MAX_INPUT:
        return raw
    return "%s...[%d chars total]" % (raw[:_MAX_INPUT], len(raw))



def _meyer_view(name):
    entry = COUNTRIES[name]
    out = {}
    for key, label, low, high in MEYER_SCALES:
        pos = entry.get("meyer", {}).get(key)
        if pos is None:
            continue
        pole = low if pos <= 50 else high
        out[key] = {"position": pos, "label": label, "leans": pole}
    return out


def _hofstede_view(name):
    entry = COUNTRIES[name]
    return dict(entry.get("hofstede", {}))


def _region_data(name):
    region_key = COUNTRIES[name].get("region", "")
    return REGIONS.get(region_key, {})


# ---------------------------------------------------------------- tool handlers

def culture_brief(args, **kwargs):
    try:
        raw_country = _clip(args.get("country", ""))
        task = _resolve_task(_clip(args.get("task", "")))
        name, suggestions = _resolve_country(raw_country)
        if name is None:
            return json.dumps({
                "error": "Country not found: %r" % raw_country,
                "suggestions": suggestions,
                "hint": "Call culture_countries with a query to search coverage.",
            })
        entry = COUNTRIES[name]
        region = _region_data(name)
        result = {
            "country": name,
            "positioning": {
                "region": region.get("label", entry.get("region", "")),
                "globe_cluster": entry.get("globe_cluster", ""),
                "lewis_type": entry.get("lewis", ""),
                "meyer_scales": _meyer_view(name),
                "hofstede": _hofstede_view(name),
            },
            "trust_currency": region.get("trust_currency", ""),
            "decision_path": region.get("decision_path", ""),
            "communication": region.get("communication", ""),
            "contract_treatment": region.get("contract", ""),
            "etiquette": region.get("etiquette", []),
            "taboos": region.get("taboos", []),
            "country_highlights": entry.get("highlights", []),
        }
        if entry.get("extrapolated"):
            result["data_note"] = (
                "Scale positions extrapolated from GLOBE-cluster neighbours (country not in the "
                "original published data sets); practitioner highlights are field-based."
            )
        if task:
            result["task"] = task
            result["task_hint"] = _TASK_HINTS.get(task, "")
        result["next_step"] = (
            "Run culture_gap_analysis with your home country to see the ranked gaps that cause "
            "misreads in this specific pairing."
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": "culture_brief failed: %s" % exc})


def culture_gap_analysis(args, **kwargs):
    try:
        raw_home = _clip(args.get("home_country", ""))
        home, sug_h = _resolve_country(raw_home)
        if home is None:
            return json.dumps({
                "error": "home_country not found: %r" % raw_home,
                "suggestions": sug_h,
            })
        raw_host = _clip(args.get("host_country", ""))
        host, sug_o = _resolve_country(raw_host)
        if host is None:
            return json.dumps({
                "error": "host_country not found: %r" % raw_host,
                "suggestions": sug_o,
            })
        if home == host:
            return json.dumps({
                "error": "home and host are the same country (%s)" % home,
                "hint": "Gap analysis compares two different cultures.",
            })
        task = _resolve_task(_clip(args.get("task", "")))
        weights = _TASK_WEIGHTS.get(task, {}) if task else {}

        home_e, host_e = COUNTRIES[home], COUNTRIES[host]
        gaps = []
        for key, label, low, high in MEYER_SCALES:
            h = home_e.get("meyer", {}).get(key)
            o = host_e.get("meyer", {}).get(key)
            if h is None or o is None:
                continue
            delta = o - h
            ad = abs(delta)
            direction = "higher" if delta > 0 else "lower"
            risk, adapt = _GAP_MEANINGS.get(key, {}).get(direction, ("", ""))
            gaps.append({
                "scale": key,
                "scale_label": label,
                "home": h,
                "host": o,
                "delta": delta,
                "gap": ad,
                "risk": _risk(ad),
                "weight": weights.get(key, 1.0),
                "ranked_gap": round(ad * weights.get(key, 1.0), 1),
                "misread_risk": risk,
                "adaptation": adapt,
            })
        gaps.sort(key=lambda g: g["ranked_gap"], reverse=True)

        # Hofstede secondary flags (only meaningful large differences)
        hof_flags = []
        for key, label in HOFSTEDE_DIMS:
            hv = home_e.get("hofstede", {}).get(key)
            ov = host_e.get("hofstede", {}).get(key)
            if hv is None or ov is None:
                continue
            d = ov - hv
            if abs(d) < 25:
                continue
            hof_flags.append({
                "dimension": key, "label": label,
                "home": hv, "host": ov, "delta": d,
                "note": "%s: host %d vs home %d" % (label, ov, hv),
            })

        headline = []
        for g in gaps[:3]:
            if g["risk"] == "LOW":
                continue
            headline.append(
                "%s: %d -> %d (%s %s)" % (g["scale_label"], g["home"], g["host"],
                                          "MORE" if g["delta"] > 0 else "LESS",
                                          g["scale_label"].lower())
            )

        result = {
            "home_country": home,
            "host_country": host,
            "task": task or "general",
            "biggest_gaps": headline,
            "gaps_ranked": gaps,
            "hofstede_flags": hof_flags,
            "synthesis": {
                "trust_mode_host": (
                    "relationship-based" if host_e.get("meyer", {}).get("trust", 50) > 55 else "task-based"
                ),
                "trust_mode_home": (
                    "relationship-based" if home_e.get("meyer", {}).get("trust", 50) > 55 else "task-based"
                ),
                "decision_pace_host": (
                    "slow consensual pre-alignment" if host_e.get("meyer", {}).get("decide", 50) < 40
                    else "fast top-down" if host_e.get("meyer", {}).get("decide", 50) > 70
                    else "mixed"
                ),
                "feedback_style_host": (
                    "indirect, face-preserving" if host_e.get("meyer", {}).get("eval", 50) > 60
                    else "direct" if host_e.get("meyer", {}).get("eval", 50) < 40
                    else "moderate"
                ),
            },
        }
        if COUNTRIES[host].get("extrapolated"):
            result["data_note"] = (
                "Host scale positions extrapolated from GLOBE-cluster neighbours; treat as directional."
            )
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": "culture_gap_analysis failed: %s" % exc})


def culture_countries(args, **kwargs):
    try:
        query = _normalize(_clip(args.get("query", "")))
        by_region = {}
        for name in sorted(COUNTRIES):
            region = COUNTRIES[name].get("region", "other")
            if query and query not in _normalize(name) and query not in _normalize(region):
                continue
            by_region.setdefault(region, []).append(name)
        total = sum(len(v) for v in by_region.values())
        result = {
            "total_covered": len(COUNTRIES),
            "matched": total,
            "regions": {
                region: {
                    "playbook": REGIONS.get(region, {}).get("label", region),
                    "countries": names,
                }
                for region, names in sorted(by_region.items())
            },
            "hint": "Use culture_brief / culture_gap_analysis with any of these names or common aliases.",
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": "culture_countries failed: %s" % exc})
