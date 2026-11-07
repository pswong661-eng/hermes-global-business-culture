"""Tests for the global-business-culture plugin. Stdlib + pytest only, no network."""

import json
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PLUGIN_DIR)

import tools  # noqa: E402


def _load_pkg():
    """Import the plugin package (dash-named dir) with proper package context."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gbc", os.path.join(PLUGIN_DIR, "__init__.py"),
        submodule_search_locations=[PLUGIN_DIR],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gbc"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("gbc", None)
    return mod


# ---------------------------------------------------------------- data integrity

class TestData:
    def test_countries_loaded(self):
        assert len(tools.COUNTRIES) >= 55

    def test_every_country_has_required_fields(self):
        for name, entry in tools.COUNTRIES.items():
            assert entry.get("region") in tools.REGIONS, "%s region missing from regions.json" % name
            assert entry.get("globe_cluster"), name
            assert entry.get("lewis") in ("linear-active", "multi-active", "reactive"), name
            meyer = entry.get("meyer", {})
            for key, _label, _lo, _hi in tools.MEYER_SCALES:
                assert key in meyer, "%s missing meyer.%s" % (name, key)
                assert 0 <= meyer[key] <= 100, "%s meyer.%s out of range" % (name, key)
            hof = entry.get("hofstede", {})
            for key, _label in tools.HOFSTEDE_DIMS:
                if key in hof:
                    assert 0 <= hof[key] <= 120, "%s hofstede.%s out of range" % (name, key)
            hl = entry.get("highlights", [])
            assert isinstance(hl, list) and len(hl) >= 3, "%s needs >=3 highlights" % name

    def test_every_region_has_playbook(self):
        for key, region in tools.REGIONS.items():
            for field in ("label", "trust_currency", "decision_path", "communication",
                          "contract", "etiquette", "taboos"):
                assert region.get(field), "%s missing %s" % (key, field)
            assert len(region["etiquette"]) >= 3
            assert len(region["taboos"]) >= 3

    def test_all_regions_referenced(self):
        used = {e.get("region") for e in tools.COUNTRIES.values()}
        assert used == set(tools.REGIONS.keys())


# ---------------------------------------------------------------- resolution

class TestResolve:
    def test_exact_case_insensitive(self):
        assert tools._resolve_country("germany")[0] == "Germany"
        assert tools._resolve_country("JAPAN")[0] == "Japan"

    def test_diacritics(self):
        assert tools._resolve_country("Türkiye")[0] == "Turkey"
        assert tools._resolve_country("Czechia")[0] == "Czechia"

    def test_aliases(self):
        for alias, want in [
            ("USA", "United States"), ("us", "United States"), ("U.S.A.", "United States"),
            ("UK", "United Kingdom"), ("England", "United Kingdom"),
            ("UAE", "United Arab Emirates"), ("emirates", "United Arab Emirates"),
            ("Korea", "South Korea"), ("Holland", "Netherlands"),
            ("Czech Republic", "Czechia"), ("Burma", "Myanmar"),
            ("Lao PDR", "Laos"), ("lao", "Laos"), ("Saudi", "Saudi Arabia"),
            ("PRC", "China"), ("HK", "Hong Kong"), ("Turkiye", "Turkey"),
            ("the usa", "United States"), ("RSA", "South Africa"),
        ]:
            got, _ = tools._resolve_country(alias)
            assert got == want, "%r -> %r (want %r)" % (alias, got, want)

    def test_typo_fuzzy(self):
        got, _ = tools._resolve_country("Germony")
        assert got == "Germany"

    def test_ambiguous_returns_suggestions(self):
        got, suggestions = tools._resolve_country("united")
        assert got is None
        assert "United States" in suggestions and "United Kingdom" in suggestions

    def test_unknown_returns_suggestions(self):
        got, suggestions = tools._resolve_country("Atlantis")
        assert got is None
        assert suggestions

    def test_garbage_safe(self):
        assert tools._resolve_country("")[0] is None
        assert tools._resolve_country(None)[0] is None
        assert tools._resolve_country(123)[0] is None


# ---------------------------------------------------------------- culture_brief

class TestBrief:
    def test_brief_known(self):
        out = json.loads(tools.culture_brief({"country": "Japan"}))
        assert out["country"] == "Japan"
        assert out["positioning"]["globe_cluster"] == "Confucian Asia"
        assert "nemawashi" in " ".join(out["country_highlights"]).lower()
        for field in ("trust_currency", "decision_path", "communication", "contract_treatment"):
            assert out[field]
        assert out["etiquette"] and out["taboos"]

    def test_brief_with_task(self):
        out = json.loads(tools.culture_brief({"country": "Germany", "task": "negotiation"}))
        assert out["task"] == "negotiation"
        assert out["task_hint"]

    def test_brief_task_aliases(self):
        out = json.loads(tools.culture_brief({"country": "Laos", "task": "first meeting with the ministry"}))
        assert out["task"] == "first_meeting"

    def test_brief_laos_flagged_extrapolated(self):
        out = json.loads(tools.culture_brief({"country": "Laos"}))
        assert out.get("data_note")

    def test_brief_unknown_country(self):
        out = json.loads(tools.culture_brief({"country": "Atlantis"}))
        assert "error" in out and out.get("suggestions")

    def test_brief_never_raises(self):
        out = json.loads(tools.culture_brief({}))
        assert "error" in out
        out = json.loads(tools.culture_brief({"country": ["list"]}))
        assert "error" in out


# ---------------------------------------------------------------- gap analysis

class TestGap:
    def test_gap_usa_japan(self):
        out = json.loads(tools.culture_gap_analysis(
            {"home_country": "USA", "host_country": "Japan", "task": "negotiation"}))
        assert out["home_country"] == "United States"
        assert out["host_country"] == "Japan"
        gaps = out["gaps_ranked"]
        assert len(gaps) == 8
        # sorted by weighted gap desc
        ranked = [g["ranked_gap"] for g in gaps]
        assert ranked == sorted(ranked, reverse=True)
        # spot-check math: evaluating USA 45 -> Japan 88 = delta 43 HIGH
        ev = next(g for g in gaps if g["scale"] == "eval")
        assert ev["delta"] == 43 and ev["risk"] == "HIGH"
        # biggest single raw gap US->Japan is 'dis' or 'eval' territory
        assert gaps[0]["risk"] in ("HIGH", "MODERATE")
        assert out["synthesis"]["feedback_style_host"] == "indirect, face-preserving"

    def test_gap_symmetry_of_deltas(self):
        a = json.loads(tools.culture_gap_analysis({"home_country": "Germany", "host_country": "Brazil"}))
        b = json.loads(tools.culture_gap_analysis({"home_country": "Brazil", "host_country": "Germany"}))
        amap = {g["scale"]: g["delta"] for g in a["gaps_ranked"]}
        bmap = {g["scale"]: g["delta"] for g in b["gaps_ranked"]}
        for k in amap:
            assert amap[k] == -bmap[k]

    def test_gap_task_weighting_changes_order(self):
        plain = json.loads(tools.culture_gap_analysis({"home_country": "Netherlands", "host_country": "Indonesia"}))
        mgmt = json.loads(tools.culture_gap_analysis(
            {"home_country": "Netherlands", "host_country": "Indonesia", "task": "management"}))
        # management re-weights lead/eval/dis; the top gap must now be one of those
        assert mgmt["gaps_ranked"][0]["scale"] in ("lead", "eval", "dis")
        assert mgmt["gaps_ranked"][0]["weight"] > 1.0
        # plain run: no weights applied at all
        assert all(g["weight"] == 1.0 for g in plain["gaps_ranked"])

    def test_gap_same_country_errors(self):
        out = json.loads(tools.culture_gap_analysis({"home_country": "France", "host_country": "FRANCE"}))
        assert "error" in out

    def test_gap_unknown_home(self):
        out = json.loads(tools.culture_gap_analysis({"home_country": "Atlantis", "host_country": "Japan"}))
        assert "error" in out

    def test_gap_hofstede_flags(self):
        out = json.loads(tools.culture_gap_analysis({"home_country": "Sweden", "host_country": "Malaysia"}))
        dims = {f["dimension"] for f in out["hofstede_flags"]}
        assert "pdi" in dims  # 31 -> 100
        for f in out["hofstede_flags"]:
            assert abs(f["delta"]) >= 25

    def test_gap_never_raises(self):
        out = json.loads(tools.culture_gap_analysis({}))
        assert "error" in out


# ---------------------------------------------------------------- countries list

class TestCountries:
    def test_list_all(self):
        out = json.loads(tools.culture_countries({}))
        assert out["total_covered"] == len(tools.COUNTRIES)
        assert out["matched"] == len(tools.COUNTRIES)
        assert "southeast-asia" in out["regions"]
        assert "Laos" in out["regions"]["southeast-asia"]["countries"]

    def test_search(self):
        out = json.loads(tools.culture_countries({"query": "korea"}))
        names = [c for v in out["regions"].values() for c in v["countries"]]
        assert names == ["South Korea"]

    def test_search_region(self):
        out = json.loads(tools.culture_countries({"query": "nordic"}))
        assert out["matched"] == 4

    def test_search_no_match(self):
        out = json.loads(tools.culture_countries({"query": "atlantis"}))
        assert out["matched"] == 0

    def test_never_raises(self):
        out = json.loads(tools.culture_countries({"query": None}))
        assert "total_covered" in out


# ---------------------------------------------------------------- packaging / register

class TestRegister:
    def test_manifest_declares_all_tools(self):
        import re
        manifest = open(os.path.join(PLUGIN_DIR, "plugin.yaml")).read()
        for tool in ("culture_brief", "culture_gap_analysis", "culture_countries"):
            assert re.search(r"^\s*-\s*%s\s*$" % tool, manifest, re.M), tool

    def test_register_wires_everything(self):
        pkg = _load_pkg()
        registered = {"tools": [], "commands": [], "skills": []}

        class Ctx:
            def register_tool(self, name, toolset, schema, handler, **kw):
                assert schema["name"] == name
                assert callable(handler)
                assert toolset == "culture"
                registered["tools"].append(name)

            def register_command(self, name, handler, **kw):
                registered["commands"].append(name)

            def register_skill(self, name, path, **kw):
                import os as _os
                assert _os.path.exists(path)
                registered["skills"].append(name)

        pkg.register(Ctx())
        assert registered["tools"] == ["culture_brief", "culture_gap_analysis", "culture_countries"]
        assert registered["commands"] == ["culture"]
        assert registered["skills"] == ["business-culture-playbook"]

    def test_slash_command_brief(self):
        pkg = _load_pkg()
        out = pkg._format_slash_brief("Japan negotiation")
        assert "Japan" in out and "Trust" in out and "Taboos" in out

    def test_slash_command_usage(self):
        pkg = _load_pkg()
        out = pkg._format_slash_brief("")
        assert "Usage" in out

    def test_slash_command_unknown(self):
        pkg = _load_pkg()
        out = pkg._format_slash_brief("Atlantis")
        assert "Not found" in out

    def test_slash_command_never_raises(self):
        pkg = _load_pkg()
        out = pkg._format_slash_brief(None)
        assert isinstance(out, str)
