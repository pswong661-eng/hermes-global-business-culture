"""Tool schemas — what the LLM reads to decide when to call the tools."""

CULTURE_BRIEF = {
    "name": "culture_brief",
    "description": (
        "Generate a structured business-culture brief for a country: how trust is built, how decisions "
        "are really made, how contracts and time are treated, communication style, etiquette and taboos. "
        "Computed from bundled Meyer (Culture Map 8 scales), Hofstede (6 dimensions), GLOBE cluster and "
        "Lewis model data plus practitioner notes. Use before any cross-border negotiation, first meeting, "
        "management action, email to foreign counterparts, or when a cross-cultural deal stalls."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "country": {
                "type": "string",
                "description": "Country name (aliases work: 'USA', 'UK', 'UAE', 'Korea', 'Burma', 'Lao PDR', 'Holland', 'Czech Republic')",
            },
            "task": {
                "type": "string",
                "description": (
                    "Optional task context — one of: negotiation, first meeting, management/feedback, "
                    "email/communication, payment collection, business trip, gift giving, hiring. "
                    "Tailors the quick-advice section."
                ),
            },
        },
        "required": ["country"],
    },
}

CULTURE_GAP_ANALYSIS = {
    "name": "culture_gap_analysis",
    "description": (
        "Compute the cultural distance between YOUR home country and a HOST country across the 8 Meyer "
        "scales and 6 Hofstede dimensions: ranked biggest gaps, the misread risk each gap creates, and "
        "concrete adaptation moves. Deterministic arithmetic over research data — this is the tool that "
        "prevents 'they said yes but nothing moves' failures. Use whenever you (or your user) will "
        "interact across cultures: negotiating, managing, selling, or writing to another country."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "home_country": {
                "type": "string",
                "description": "The country you/your user operate from (aliases supported)",
            },
            "host_country": {
                "type": "string",
                "description": "The counterpart's country (aliases supported)",
            },
            "task": {
                "type": "string",
                "description": "Optional task (negotiation, first meeting, management, email, payment, trip) — weights which gaps matter most",
            },
        },
        "required": ["home_country", "host_country"],
    },
}

CULTURE_COUNTRIES = {
    "name": "culture_countries",
    "description": (
        "List the countries covered by the culture tools (57 economies), optionally filtered by a search "
        "query. Use when unsure whether culture_brief covers a country, or to show coverage."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional substring to filter countries (e.g. 'asia', 'united')",
            },
        },
        "required": [],
    },
}
