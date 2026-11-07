---
name: business-culture-playbook
description: "Deep practitioner playbook for cross-cultural business operations."
version: 1.0.0
author: Eric Wong (pswong661-eng), GiGi (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Business, Culture, Negotiation, Cross-cultural]
    category: business
---

# Business Culture Playbook

Practitioner method for operating across business cultures. Use the plugin's
deterministic tools first (`culture_brief`, `culture_gap_analysis`,
`culture_countries`); this playbook adds the field judgment the numbers cannot
carry: diagnosing stalled deals, choosing intermediaries, sequencing a first
visit, and calibrating within-country variation.

## When to Use

- A cross-border deal has stalled ("they went quiet", "they say yes but nothing moves")
- Planning a first visit: delegation seniority, seating, gifts, meal protocol
- Drafting messages to foreign counterparts (tone, directness, pacing, who is addressed)
- Managing, hiring, or giving feedback across cultures
- Preparing a negotiation strategy against the counterpart's decision path

## Procedure

### 1. Ground the pairing in data
Run `culture_gap_analysis` (home → host, with the task). The ranked gaps name
where misreads will happen; the adaptation column is your action list.

### 2. Diagnose a stalled deal
Map symptoms to the likely scale gap:

- "They say yes but nothing moves" → trust/task gap (they haven't decided you,
  not the deal) or decide/consensual gap (the meeting's 'yes' was politeness;
  the real decision is still socializing).
- "They went quiet after the contract" → contract-as-relationship cultures:
  the signature started the relationship, not ended it. Maintenance contact IS
  the enforcement mechanism.
- "They haggle everything, even signed terms" → treat as normal wide-range
  bargaining (RU, CN, IN, MENA, LatAm): anchor, concede slowly, stay warm.
- "They ignore my deadlines" → scheduling gap: build 2-3x slack, confirm the
  day before, senior-to-senior nudges instead of invoice escalations.
- "My direct feedback damaged the relationship" → evaluating gap: switch to
  private, indirect, third-party channels and rebuild with public praise.

### 3. Sequence a first visit
1. Secure a trusted introducer (the single highest-ROI move in
   relationship-based cultures).
2. Send the most senior credible person; mirror their delegation's seniority.
3. Let the host set pace, small talk, and ceremony; never cut a ritual short.
4. Banquets/meals are the negotiation; the meeting is the formality.
5. Follow up warm and personal (not just contractual) within days.

### 4. Calibrate within-country variation
The tools report national central tendencies; adjust for: city vs capital,
generational splits, industry norms, company origin (local family firm vs
multinational subsidiary), and individual personality. A Seoul startup runs
looser than a Seoul chaebol; Singapore is not Indonesia; Chile is not Brazil.

### 5. Frontier-market overlay (LDCs)
For least-developed and informal economies (Laos, Cambodia, Myanmar, and
peers), overlay on top of the region playbook:
- Relationships substitute for weak contract enforcement — the personal
  guarantee IS the collateral.
- Expect hybrid decision paths: formal hierarchy plus informal patron networks
  running in parallel; map both.
- Cash flow reality, infrastructure gaps and seasonal rhythms (rainy season,
  festivals) dominate schedules; triple every timeline.
- Verbal commitments from the senior person outweigh documents; record them
  respectfully in follow-up notes, not contested meetings.

## Pitfalls

- Never cause public loss of face to force clarity — you will get a polite yes
  and a permanent no.
- Do not apply one Western playbook everywhere; the misread comes from the GAP
  between your culture and theirs, not from their absolute position.
- Do not mistake English fluency for cultural alignment — the smoother the
  English, the subtler the context you may be missing.
- Gift-giving: mind anti-corruption law (esp. China, US FCPA, UK Bribery Act);
  modest, culturally apt, never cash.

## Verification

- Every recommendation names its source scale or region pattern.
- For time-sensitive facts (holidays, Ramadan dates, visa rules), verify with
  `web_search` — the dataset is cultural, not calendrical.
