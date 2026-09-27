"""SiteForge section library: composing a demo site from sites/_library.

A built site is a copy of the library app with four files written for the
lead:
  src/content.json   every word on the page (AI-written, facts injected)
  src/sections.json  ordered [{slot, variant, tone?}] from catalogue.json
  src/site.json      preset, slug, beacon URL
  src/tokens.css     the SITE block: brand accent + contrast companions
plus src/fonts.ts (only the chosen preset's faces) and src/brand.json.

Everything here is plain functions; app.py owns routes, leads and previews.
"""
import base64
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
LIBRARY_DIR = BASE_DIR / "sites" / "_library"
CATALOGUE_PATH = LIBRARY_DIR / "catalogue.json"
UI_DEFAULTS_PATH = LIBRARY_DIR / "ui-defaults.json"

PRESETS = ["heritage", "industrial", "clean-local", "bold"]
PRESET_LABELS = {
    "heritage": "Heritage — Brygada / Libre Franklin",
    "industrial": "Industrial — Big Shoulders / Barlow",
    "clean-local": "Clean local — Bricolage / Figtree",
    "bold": "Bold — Epilogue / Hanken Grotesk",
}
# Ground + surface of each preset: --accent-ink must clear 4.5:1 on both.
# Keep in step with src/tokens.css and scripts/use-sample.mjs.
PRESET_GROUNDS = {
    "heritage": ["#F2F0EB", "#E7E5E1"],
    "industrial": ["#101010", "#262626"],
    "clean-local": ["#FFFFFF", "#EAEAEA"],
    "bold": ["#FFFFFF", "#E3E3E3"],
}
# next/font imports per preset: (import name, css variable, extra options).
PRESET_FONTS = {
    "heritage": [("Brygada_1918", "--font-brygada", ""), ("Libre_Franklin", "--font-libre-franklin", "")],
    "industrial": [("Big_Shoulders_Display", "--font-big-shoulders", ""),
                   ("Barlow", "--font-barlow", 'weight: ["400", "500", "600", "700"], ')],
    "clean-local": [("Bricolage_Grotesque", "--font-bricolage", ""), ("Figtree", "--font-figtree", "")],
    "bold": [("Epilogue", "--font-epilogue", ""), ("Hanken_Grotesk", "--font-hanken", "")],
}
REQUIRED_SLOTS = ["nav", "hero", "contact", "footer"]
SLOT_ORDER = ["nav", "hero", "trust", "services", "about", "process", "reviews", "gallery",
              "service-area", "cta", "contact", "footer"]
TONES = {"base", "surface", "band", "accent"}

# Never copied into a built site: dev tooling, samples, QA route, docs.
COPY_IGNORE = shutil.ignore_patterns(
    "node_modules", ".next", "samples", "scripts", "_samples", ".impeccable", "catalogue",
    "PRODUCT.md", "DESIGN.md", "catalogue.json", "ui-defaults.json", "next-env.d.ts", "*.tsbuildinfo",
    "npm-install.log", "dev-server.log", ".devserver.json", ".history", ".vercel", "README.md",
    "inspiration", "INSPIRATION.md",  # design references (60MB of video): never shipped in a site
)

# Always removed: things no business data can back up on a demo site.
_CLAIM_RE = re.compile(
    r"guarantee|warranty|award|cheapest|best in|no\.?\s*1\b|number one|\bonly \d+ |limited slots|"
    r"book now before|€\s*\d|\d+\s*%",
    re.I,
)

# Checked against the source data by claim_guard(): kept only when the facts
# (name, trade, real reviews, Google opening hours, the lead's years) show it.
CLAIM_KINDS = {
    "24-hour": re.compile(r"\b24\s*(?:/|-|\s)?\s*(?:7|hours?|hrs?)\b|round[- ]the[- ]clock|around the clock|any time of (?:the )?(?:day|night)", re.I),
    "emergency": re.compile(r"\bemergenc(?:y|ies)\b|\burgent call-?outs?\b", re.I),
    "years in business": re.compile(r"\b\d+\+?\s*years?\b|\bsince\s+(?:19|20)\d{2}\b|\bestablished\b|\best\.\s*\d|\bdecades?\b|\bgenerations?\b", re.I),
    "certification": re.compile(r"safe electric|\breci\b|\brgii\b|\bseai\b|\bregistered\b|\bcertified\b|\baccredited\b|"
                                r"\bqualified\b|\blicen[cs]ed\b|\binsured\b|\binsurance\b|approved installer|\bcertificat", re.I),
}
# Never rewritten by the guard: real data, not generated copy.
_GUARD_SKIP = {"business", "reviews", "ui", "area.towns", "hero.quote", "hero.image", "about.image", "gallery"}


# ---------------------------------------------------------------------------
# Library files
# ---------------------------------------------------------------------------

def load_catalogue():
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def catalogue_index():
    return {v["id"]: v for v in load_catalogue()["variants"]}


def labs_enabled():
    """Labs variants (catalogue "labs": true) are only composed when
    SITEFORGE_LABS=1, so the stable library is the default."""
    return os.environ.get("SITEFORGE_LABS") == "1"


# What a labs variant becomes when labs are off (or its data is missing).
LABS_STABLE = {"hero-editorial": "hero-full-bleed", "hero-colour-field": "hero-typographic",
               "hero-quick-quote": "hero-typographic", "services-index": "services-grid",
               "area-marquee": "area-towns", "footer-wordmark": "footer-simple",
               "contact-chips": "contact-form-split", "hero-electric": "hero-typographic"}


def ui_defaults():
    return json.loads(UI_DEFAULTS_PATH.read_text(encoding="utf-8"))


def icon_names():
    """The icon keys content.json may use, read from the library's icons.tsx."""
    src = (LIBRARY_DIR / "src" / "components" / "icons.tsx").read_text(encoding="utf-8")
    block = src[src.index("ICONS: Record"):src.index("};", src.index("ICONS: Record"))]
    return re.findall(r'"?([a-z][a-z-]*)"?\s*:\s*[A-Z]\w+', block)


def library_ready():
    return (LIBRARY_DIR / "package.json").exists() and CATALOGUE_PATH.exists()


def copy_library(dest):
    shutil.copytree(LIBRARY_DIR, dest, ignore=COPY_IGNORE)
    shutil.rmtree(dest / "src" / "app" / "catalogue", ignore_errors=True)


def is_library_site(site_dir):
    return (site_dir / "src" / "sections.json").exists() and (site_dir / "src" / "tokens.css").exists()


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def site_sections(site_dir):
    data = read_json(site_dir / "src" / "sections.json", [])
    return data if isinstance(data, list) else []


def variant_file(slot, variant):
    return f"src/components/sections/{slot}/{variant}.tsx"


def slot_files(site_dir, slot):
    """Component file(s) rendering `slot` on this site (from sections.json)."""
    return [variant_file(s["slot"], s["variant"]) for s in site_sections(site_dir)
            if s.get("slot") == slot and (site_dir / variant_file(s["slot"], s["variant"])).exists()]


def site_slots(site_dir):
    return [s.get("slot") for s in site_sections(site_dir) if s.get("slot")]


# ---------------------------------------------------------------------------
# content.json paths (inline text editing writes straight to a key)
# ---------------------------------------------------------------------------

_PATH_RE = re.compile(r"^[A-Za-z][\w-]*(\.[\w-]+){0,6}$")


def set_content_path(site_dir, path, value):
    """Set a string at a dotted path ("services.items.2.title") in
    content.json. Only replaces an existing string; returns the old value,
    or raises ValueError."""
    if not _PATH_RE.match(path or ""):
        raise ValueError("invalid content path")
    content_path = site_dir / "src" / "content.json"
    data = read_json(content_path)
    if not isinstance(data, dict):
        raise ValueError("content.json is missing or invalid")
    keys = path.split(".")
    cur = data
    for key in keys[:-1]:
        cur = cur[int(key)] if isinstance(cur, list) and key.isdigit() else (cur.get(key) if isinstance(cur, dict) else None)
        if cur is None:
            raise ValueError(f"no such content key: {path}")
    last = keys[-1]
    if isinstance(cur, list) and last.isdigit() and int(last) < len(cur):
        old = cur[int(last)]
        if not isinstance(old, str):
            raise ValueError("that key isn't text")
        cur[int(last)] = value
    elif isinstance(cur, dict) and isinstance(cur.get(last), str):
        old = cur[last]
        cur[last] = value
    else:
        raise ValueError(f"no such text key: {path}")
    write_json(content_path, data)
    return old


# ---------------------------------------------------------------------------
# Colour: the brand accent and its contrast-safe companions
# ---------------------------------------------------------------------------

def _rgb(hex_):
    h = hex_.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def _lum(hex_):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def accent_fg(accent):
    return "#FFFFFF" if contrast(accent, "#FFFFFF") >= contrast(accent, "#111111") else "#111111"


def accent_ink(accent, grounds):
    """The accent nudged toward black (light grounds) or white (dark) until
    it reads at 4.5:1 on every ground: used wherever the accent sets text."""
    target = "#000000" if _lum(grounds[0]) > 0.5 else "#FFFFFF"
    for step in range(26):
        c = _mix(accent, target, step * 0.04)
        if all(contrast(c, g) >= 4.5 for g in grounds):
            return c
    return target


_SITE_BLOCK_RE = re.compile(r"/\* SITE:BEGIN[\s\S]*?SITE:END \*/")


def site_block(accent, radius=None):
    accent = accent.upper()
    lines = [
        "/* SITE:BEGIN — written by SiteForge (brand colour + contrast companions). */",
        ":root {",
        f"  --accent: {accent};",
        f"  --accent-fg: {accent_fg(accent)};",
        "}",
    ]
    for preset, grounds in PRESET_GROUNDS.items():
        lines.append(f'[data-preset="{preset}"] {{ --accent-ink: {accent_ink(accent, grounds)}; }}')
    if radius is not None:
        lines.append(f"html[data-preset] {{ --radius: {int(radius)}px; --radius-lg: {int(radius) * 2}px; }}")
    lines.append("/* SITE:END */")
    return "\n".join(lines)


def read_site_theme(site_dir):
    """(accent hex, radius px or None) from the site's tokens.css SITE block."""
    css = (site_dir / "src" / "tokens.css").read_text(encoding="utf-8")
    block = _SITE_BLOCK_RE.search(css)
    text = block.group(0) if block else ""
    m = re.search(r"--accent:\s*(#[0-9A-Fa-f]{6})", text)
    r = re.search(r"--radius:\s*(\d+)px", text)
    return (m.group(1).upper() if m else "#1D6B52"), (int(r.group(1)) if r else None)


def write_site_theme(site_dir, accent=None, radius=None, keep_radius=True):
    path = site_dir / "src" / "tokens.css"
    css = path.read_text(encoding="utf-8")
    cur_accent, cur_radius = read_site_theme(site_dir)
    block = site_block(accent or cur_accent, radius if radius is not None else (cur_radius if keep_radius else None))
    new = _SITE_BLOCK_RE.sub(lambda _: block, css) if _SITE_BLOCK_RE.search(css) else css + "\n" + block + "\n"
    path.write_text(new, encoding="utf-8")


# ---------------------------------------------------------------------------
# Preset + fonts
# ---------------------------------------------------------------------------

def fonts_ts(preset):
    fonts = PRESET_FONTS[preset]
    names = ", ".join(sorted(f[0] for f in fonts))
    lines = [
        "// Written by SiteForge for this site's style preset — pick another",
        "// preset in the theme panel to replace this file.",
        f'import {{ {names} }} from "next/font/google";',
        "",
    ]
    for i, (imp, var, extra) in enumerate(fonts):
        lines.append(f'const f{i} = {imp}({{ subsets: ["latin"], {extra}variable: "{var}", display: "swap" }});')
    lines += [
        "",
        f'export const FONT_PRESET = "{preset}";',
        "export const fontClassName = [" + ", ".join(f"f{i}.variable" for i in range(len(fonts))) + '].join(" ");',
        "",
    ]
    return "\n".join(lines)


def read_preset(site_dir):
    site = read_json(site_dir / "src" / "site.json", {}) or {}
    return site.get("preset") if site.get("preset") in PRESETS else "clean-local"


def set_preset(site_dir, preset):
    if preset not in PRESETS:
        raise ValueError("unknown preset")
    site_path = site_dir / "src" / "site.json"
    site = read_json(site_path, {}) or {}
    site["preset"] = preset
    write_json(site_path, site)
    (site_dir / "src" / "fonts.ts").write_text(fonts_ts(preset), encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared node_modules: every built site links to the library's install
# ---------------------------------------------------------------------------

def _is_link(path):
    """True for a symlink or (Windows) a directory junction."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def detach_node_modules(site_dir):
    """Remove a site's node_modules link WITHOUT touching the shared install
    it points at. Must run before any rmtree/rename of a site folder. Leaves
    a real (per-site) node_modules folder alone."""
    link = Path(site_dir) / "node_modules"
    if not _is_link(link):
        return False
    if os.name == "nt":
        os.rmdir(link)  # removes the junction itself, not the target's contents
    else:
        os.unlink(link)
    return True


def link_node_modules(site_dir):
    """Point site_dir/node_modules at the library's. Returns True on success."""
    target = LIBRARY_DIR / "node_modules"
    link = Path(site_dir) / "node_modules"
    if _is_link(link):
        return True
    if link.exists():
        return True  # a real per-site install (older site) keeps working as-is
    if os.name == "nt":
        # A directory junction needs no admin rights or Developer Mode (a symlink would).
        try:
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
            return True
        except (ImportError, OSError, AttributeError):
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                    capture_output=True, text=True)
            return result.returncode == 0
    os.symlink(target, link, target_is_directory=True)
    return True


def library_deps_installed():
    return (LIBRARY_DIR / "node_modules" / "next" / "package.json").exists()


# ---------------------------------------------------------------------------
# Facts: what we actually know about the business
# ---------------------------------------------------------------------------

_SONS_RE = re.compile(r"(?:&|\band)\s+(?:sons?|daughters?)\b", re.I)
_COMPANY_WORDS = {"ltd", "limited", "services", "electrical", "electrics", "plumbing", "heating", "roofing",
                  "building", "builders", "construction", "contractors", "landscaping", "gardens", "garden",
                  "painting", "decorating", "the", "and", "&", "group", "solutions", "company", "co"}


def owner_first_name(name):
    """A first name only when the business name clearly starts with one
    ("Aoife's Garden Care", "Derek Doyle Electrical"). "Kavanagh & Sons" or
    "MCR Electrical" give nothing — copy then says "we" instead of guessing."""
    words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóú'’]+", name or "")
    if not words:
        return ""
    first = re.sub(r"['’]s$", "", words[0])
    if first.lower() in _COMPANY_WORDS or first.isupper() or len(first) < 3:
        return ""
    possessive = re.match(r"^[A-Za-zÁÉÍÓÚáéíóú]+['’]s\b", (name or "").strip())
    two_names = len(words) >= 3 and words[1][:1].isupper() and words[1].lower() not in _COMPANY_WORDS
    return first if (possessive or two_names) and not _SONS_RE.search(name or "") else ""


def is_irish_mobile(intl):
    return bool(re.match(r"^\+?3538[35-9]\d{7}$", (intl or "").replace(" ", "")))


def nearest_towns(counties, county, home, lat, lng, limit=8):
    """Home town first, then the nearest towns in the same county (from
    data/ireland_counties.json). Real geography, used for the coverage line."""
    towns = (counties.get(county) or {}).get("towns") or []
    out = [home] if home else []
    if lat is not None and lng is not None:
        def dist(t):
            return math.hypot((t[1] - lat), (t[2] - lng) * math.cos(math.radians(lat)))
        towns = sorted(towns, key=dist)
    for t in towns:
        if len(out) >= limit:
            break
        if t[0].lower() != (home or "").lower():
            out.append(t[0])
    return out


def compress_hours(weekday_descriptions):
    """Google's ["Monday: 8:00 AM – 6:00 PM", ...] → "Mon–Fri 8am–6pm · Sat 9am–1pm"."""
    days = []
    for line in weekday_descriptions or []:
        day, _, hours = line.partition(":")
        hours = hours.strip()
        if not day or not hours:
            continue
        hours = re.sub(r":00", "", hours)
        hours = re.sub(r"\s*([AP])M", lambda m: m.group(1).lower() + "m", hours)
        hours = hours.replace(" ", "").replace(" – ", "–").replace(" - ", "–")
        days.append((day.strip()[:3], hours))
    groups = []
    for day, hours in days:
        if groups and groups[-1][2] == hours:
            groups[-1][1] = day
        else:
            groups.append([day, day, hours])
    parts = [f"{a}{'–' + b if b != a else ''} {h}" for a, b, h in groups if "closed" not in h.lower()]
    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

TRADE_DEFAULTS = {
    "electrician": ("heritage", [("plug-zap", "Rewires & upgrades"), ("ev-charger", "EV chargers"),
                                 ("lightbulb", "Lighting"), ("siren", "Fault finding & callouts")]),
    "plumber": ("heritage", [("droplets", "Leaks & repairs"), ("shower", "Bathrooms & showers"),
                             ("flame", "Boilers & heating"), ("wrench", "Taps, toilets & cylinders")]),
    "heating engineer": ("heritage", [("flame", "Boiler service & repair"), ("thermometer", "Heating systems"),
                                      ("gauge", "Controls & upgrades"), ("fan", "Heat pumps")]),
    "roofer": ("bold", [("house", "Roof repairs"), ("layers", "Flat roofs"), ("rain", "Gutters & fascia"),
                        ("brick-wall", "Chimneys & flashing")]),
    "landscaper": ("clean-local", [("scissors", "Lawns & hedges"), ("sprout", "Planting & beds"),
                                   ("shovel", "Garden tidy-ups"), ("fence", "Fencing & paving")]),
    "painter": ("clean-local", [("paint-roller", "Interior painting"), ("brush", "Exterior painting"),
                                ("paintbrush", "Doors, trims & wood"), ("layers", "Wallpapering")]),
    "builder": ("industrial", [("hammer", "Extensions"), ("house", "Renovations"), ("brick-wall", "Blockwork & groundwork"),
                               ("ruler", "Kitchens & fit-outs")]),
    "cafe": ("clean-local", [("coffee", "Coffee"), ("croissant", "Breakfast & pastries"),
                             ("sandwich", "Lunch"), ("cake", "Cakes & treats")]),
}


def _trade_key(trade):
    t = (trade or "").lower().replace("é", "e")
    for key in TRADE_DEFAULTS:
        if key in t or t in key:
            return key
    if "coffee" in t or "cafe" in t:
        return "cafe"
    if "garden" in t:
        return "landscaper"
    if "heat" in t:
        return "heating engineer"
    return ""


TRADE_MARK_ICON = {
    "electrician": "zap", "plumber": "droplets", "heating engineer": "flame", "roofer": "house",
    "landscaper": "leaf", "painter": "paint-roller", "builder": "hammer", "cafe": "coffee",
}


def default_preset(trade):
    return TRADE_DEFAULTS.get(_trade_key(trade), ("clean-local", []))[0]


def _variant_ok(variant, facts):
    if variant.startswith("reviews-"):
        return bool(facts.get("reviews"))
    if variant.startswith("gallery-"):
        return False  # only with real job photos, which a fresh build never has
    if variant == "hero-review-led":
        return bool(facts.get("reviews"))
    if variant == "area-map":
        return facts.get("lat") is not None
    if variant in ("hero-image-grid",):
        return len(facts.get("images") or {}) >= 3
    if variant == "area-marquee":
        return len(facts.get("towns") or []) >= 3
    return True


FALLBACK_SECTIONS = {
    "heritage": ["nav-centred-logo", "hero-split-image", "trust-strip", "services-list-icons", "about-owner-note",
                 "reviews-featured", "process-timeline", "area-towns", "cta-band", "contact-form-split", "footer-columns"],
    "industrial": ["nav-phone-bar", "hero-full-bleed", "trust-grid", "services-featured-grid", "process-steps",
                   "reviews-grid", "about-facts", "area-map", "cta-split", "contact-details", "footer-columns"],
    "clean-local": ["nav-minimal", "hero-typographic", "trust-strip", "services-grid", "reviews-carousel",
                    "process-cards", "about-split", "area-towns", "cta-callout", "contact-form-centered", "footer-simple"],
    "bold": ["nav-minimal", "hero-review-led", "trust-strip", "services-tabs", "reviews-featured", "process-steps",
             "area-towns", "cta-band", "contact-form-split", "footer-simple"],
}
HERO_SWAPS = {"hero-review-led": "hero-typographic", "hero-image-grid": "hero-typographic",
              "hero-split-image": "hero-split-image", "hero-full-bleed": "hero-full-bleed"}


def normalize_sections(raw, facts, preset):
    """Validate an AI (or fallback) section list against the catalogue and
    the data we have; enforce order, required slots and tone rhythm."""
    cat = catalogue_index()
    chosen = {}
    for entry in raw or []:
        if isinstance(entry, str):
            entry = {"variant": entry}
        if not isinstance(entry, dict):
            continue
        vid = str(entry.get("variant") or "")
        meta = cat.get(vid)
        if not meta or meta["slot"] in chosen:
            continue
        if vid in LABS_STABLE and (not labs_enabled() or not _variant_ok(vid, facts)):
            vid = LABS_STABLE[vid]
            meta = cat[vid]
        if not _variant_ok(vid, facts):
            if meta["slot"] == "hero":
                vid = HERO_SWAPS.get(vid, "hero-typographic")
                meta = cat[vid]
            else:
                continue
        item = {"slot": meta["slot"], "variant": vid}
        if entry.get("tone") in TONES:
            item["tone"] = entry["tone"]
        chosen[meta["slot"]] = item
    for vid in FALLBACK_SECTIONS[preset]:
        slot = cat[vid]["slot"]
        if slot in REQUIRED_SLOTS and slot not in chosen:
            chosen[slot] = {"slot": slot, "variant": vid}
    if "services" not in chosen:
        chosen["services"] = {"slot": "services", "variant": "services-grid"}

    # Photos decide the hero: a real photo always gets an image hero; with
    # none, the typographic hero (or the review-led one when reviews exist).
    images = facts.get("images") or {}
    hero = chosen["hero"]
    photo_heroes = {"hero-split-image", "hero-full-bleed", "hero-editorial"} | ({"hero-image-grid"} if len(images) >= 3 else set())
    if images.get("hero") and hero["variant"] not in photo_heroes:
        hero["variant"] = "hero-full-bleed" if preset in ("industrial", "bold") else "hero-split-image"
        hero.pop("tone", None)
    elif not images.get("hero") and hero["variant"] in ("hero-split-image", "hero-full-bleed", "hero-image-grid"):
        hero["variant"] = "hero-typographic"
        hero.pop("tone", None)
    # A second photo belongs in About, in a variant that shows it.
    if images.get("about"):
        if "about" not in chosen:
            chosen["about"] = {"slot": "about", "variant": "about-split"}
        elif chosen["about"]["variant"] == "about-facts":
            chosen["about"]["variant"] = "about-split"

    # Labs: the quick-quote hero and the services index send into the quote
    # form, so the page needs a contact variant that has one.
    if (hero["variant"] == "hero-quick-quote" or chosen["services"]["variant"] == "services-index") \
            and chosen["contact"]["variant"] == "contact-details":
        chosen["contact"]["variant"] = "contact-form-split"

    # One phone moment at the end of the page.
    footer = chosen["footer"]
    loud_end = chosen.get("cta", {}).get("variant") == "cta-band" or chosen["contact"]["variant"] == "contact-details"
    if footer["variant"] == "footer-big-phone" and (loud_end or not facts.get("phone")):
        footer["variant"] = "footer-columns" if preset in ("heritage", "industrial") else "footer-simple"
    if chosen["contact"]["variant"] == "contact-details" and not facts.get("phone"):
        chosen["contact"]["variant"] = "contact-form-split"
    # Contact routes once: a listing/phone CTA right before contact-details repeats them.
    if chosen["contact"]["variant"] == "contact-details" and chosen.get("cta", {}).get("variant") in ("cta-split", "cta-band"):
        chosen["cta"]["variant"] = "cta-callout"
    # The rating once near the top: not in trust too when reviews are shown.
    if chosen.get("trust", {}).get("variant") == "trust-rating" and (
            chosen.get("reviews") or not facts.get("rating") or chosen["hero"]["variant"] == "hero-review-led"):
        chosen["trust"]["variant"] = "trust-strip"

    ordered = [chosen[s] for s in SLOT_ORDER if s in chosen]
    # Tone rhythm: no two identical coloured tones back to back.
    prev = None
    for item in ordered:
        tone = item.get("tone") or cat[item["variant"]].get("tone", "base")
        # In clean-local the band *is* the accent, so the two count as one colour.
        same = tone == prev["tone"] or (preset == "clean-local" and {tone, prev["tone"]} == {"band", "accent"}) \
            if prev is not None else False
        if same and tone in ("surface", "band", "accent"):
            own = cat[item["variant"]].get("tone")
            if own in ("band", "accent") and prev["item"]["slot"] not in ("nav", "hero"):
                prev["item"]["tone"] = "base"
            else:
                item["tone"] = tone = "base"
        prev = {"tone": tone, "item": item}
    return ordered


def _clean_str(v, limit=400):
    if not isinstance(v, str):
        return ""
    v = re.sub(r"\s+", " ", v).strip()
    v = v.replace("!", ".").replace("..", ".")
    return v[:limit].strip()


def _drop_claims(text):
    """Remove whole sentences that make claims we can't verify."""
    if not text:
        return text
    sentences = re.split(r"(?<=[.?])\s+", text)
    kept = [s for s in sentences if not _CLAIM_RE.search(s)]
    return " ".join(kept).strip()


def sanitize_content(raw, facts):
    """Keep only the keys the library renders, as clean strings, with
    unverifiable claims removed. Business facts are never taken from the AI."""
    raw = raw if isinstance(raw, dict) else {}
    icons = set(icon_names())
    out = {}

    def s(v, limit=400):
        return _drop_claims(_clean_str(v, limit))

    def obj(key, fields):
        src = raw.get(key) if isinstance(raw.get(key), dict) else {}
        val = {f: s(src.get(f), lim) for f, lim in fields.items()}
        return {k: v for k, v in val.items() if v}

    out["seo"] = obj("seo", {"title": 70, "description": 170})
    out["hero"] = obj("hero", {"headline": 90, "subhead": 220, "primaryCta": 32, "secondaryCta": 32})
    out["nav"] = obj("nav", {"cta": 24, "note": 70})

    def items(src, fields, max_n, need="title"):
        res = []
        for it in (src if isinstance(src, list) else [])[:max_n]:
            if not isinstance(it, dict):
                continue
            row = {f: s(it.get(f), lim) for f, lim in fields.items()}
            if not row.get(need):
                continue
            if "icon" in it:
                row["icon"] = it["icon"] if it["icon"] in icons else "badge"
            res.append({k: v for k, v in row.items() if v})
        return res

    trust = raw.get("trust") if isinstance(raw.get("trust"), dict) else {}
    # The rating already shows in the hero and the reviews section: trust
    # items and about-facts carry other facts (area, hours, how to reach them).
    rating_re = re.compile(r"\brat(ed|ing)\b|\breviews?\b|\bstars?\b|★|\b[1-5]\.\d\b", re.I)
    trust_items = [t for t in items(trust.get("items"), {"title": 40, "text": 110}, 6)
                   if not rating_re.search(f"{t.get('title', '')} {t.get('text', '')}")][:4]
    out["trust"] = {"heading": s(trust.get("heading"), 60), "items": trust_items}
    services = raw.get("services") if isinstance(raw.get("services"), dict) else {}
    svc_items = items(services.get("items"), {"title": 48, "text": 200}, 8)
    for i, it in enumerate((services.get("items") or [])[:8]):
        if i < len(svc_items) and isinstance(it, dict) and isinstance(it.get("points"), list):
            pts = [s(p, 60) for p in it["points"][:4]]
            svc_items[i]["points"] = [p for p in pts if p]
    out["services"] = {"heading": s(services.get("heading"), 60), "intro": s(services.get("intro"), 220),
                       "items": svc_items}
    about = raw.get("about") if isinstance(raw.get("about"), dict) else {}
    body = [s(p, 420) for p in (about.get("body") or [])[:3]] if isinstance(about.get("body"), list) else []
    facts_rows = [f for f in items(about.get("facts"), {"label": 20, "value": 60}, 5, need="label")
                  if not rating_re.search(f"{f.get('label', '')} {f.get('value', '')}")][:4]
    out["about"] = {"heading": s(about.get("heading"), 80), "body": [p for p in body if p],
                    "signoff": s(about.get("signoff"), 40), "facts": facts_rows}
    process = raw.get("process") if isinstance(raw.get("process"), dict) else {}
    out["process"] = {"heading": s(process.get("heading"), 60), "intro": s(process.get("intro"), 200),
                      "steps": items(process.get("steps"), {"title": 40, "text": 140}, 5)}
    out["reviews"] = obj("reviews", {"heading": 60, "intro": 200})
    out["area"] = obj("area", {"heading": 60, "intro": 200, "note": 100})
    out["cta"] = obj("cta", {"heading": 80, "text": 200, "primary": 32, "secondary": 32})
    contact = raw.get("contact") if isinstance(raw.get("contact"), dict) else {}
    out["contact"] = {k: v for k, v in {
        "heading": s(contact.get("heading"), 50), "intro": s(contact.get("intro"), 220),
        "formHeading": s(contact.get("formHeading"), 50), "submit": s(contact.get("submit"), 30),
        "success": s(contact.get("success"), 160),
        "services": [x for x in (s(v, 40) for v in (contact.get("services") or [])[:6]) if x]
        if isinstance(contact.get("services"), list) else [],
    }.items() if v}
    out["footer"] = obj("footer", {"blurb": 140})
    out["mobileBar"] = obj("mobileBar", {"call": 18, "whatsapp": 18, "quote": 18})
    return out


_QUOTE_OPENERS = {"he", "she", "they", "it", "this", "that", "and", "but", "so", "also", "then", "which",
                  "him", "them", "his", "her", "their", "as", "because", "plus"}


def _first_sentence(text):
    m = re.match(r"(.+?[.!?])(\s|$)", text.strip())
    return (m.group(1) if m else text.strip()).strip()


def hero_quote(reviews, max_words=25):
    """The review whose opening stands alone best, as a hero quote of at
    most `max_words` words (ellipsis when cut). A standalone opening is a
    whole sentence of 6–25 words that doesn't lean on something before it
    ("He was great…", "And the price…")."""
    best, best_score = None, None
    for r in reviews or []:
        text = re.sub(r"\s+", " ", r.get("text") or "").strip()
        if not text:
            continue
        first = _first_sentence(text)
        words = first.split()
        n = len(words)
        score = 0.0
        score += 3 if 6 <= n <= max_words else (1 if n < 6 else 0)
        score -= 3 if words and words[0].lower().strip(",.") in _QUOTE_OPENERS else 0
        score += 1 if first[-1:] in ".!" else 0
        score += (r.get("rating") or 5) - 5  # 4-star reviews rank just below 5-star
        score -= abs(n - 16) / 20  # a comfortable length reads best at display size
        if best_score is None or score > best_score:
            best, best_score = (r, first, words), score
    if not best:
        return None
    r, first, words = best
    if len(words) < 6:  # a very short opening borrows the next sentence
        words = re.sub(r"\s+", " ", r["text"]).split()
    quote = " ".join(words[:max_words])
    if len(words) > max_words:
        quote = quote.rstrip(",;:—-") + "…"
    return {"text": quote, "author": r.get("author", ""), "rating": r.get("rating") or 5}


def _source_text(facts):
    parts = [facts.get("name"), facts.get("trade"), facts.get("hours"), facts.get("source_text")]
    parts += [r.get("text") for r in facts.get("reviews") or []]
    return " ".join(p for p in parts if p)


def claim_guard(content, facts, log=print):
    """Before content.json is written: remove any 24-hour / emergency /
    years-in-business / certification claim that the source data doesn't
    show, sentence by sentence (a list item left empty is dropped). Returns
    the removals as [{path, kind, text}] and logs each one."""
    source = _source_text(facts)
    allowed = {kind for kind, rx in CLAIM_KINDS.items() if rx.search(source)}
    if (facts.get("years") or "").strip():
        allowed.add("years in business")
    if re.search(r"open 24 hours", facts.get("hours") or "", re.I):
        allowed.add("24-hour")
    removed = []

    def check(text, path):
        sentences = re.split(r"(?<=[.?!])\s+", text)
        kept = []
        for sentence in sentences:
            hit = next((k for k, rx in CLAIM_KINDS.items() if k not in allowed and rx.search(sentence)), None)
            if hit:
                removed.append({"path": path, "kind": hit, "text": sentence})
            else:
                kept.append(sentence)
        return " ".join(kept).strip()

    def walk(node, path):
        if any(path == skip or path.startswith(skip + ".") for skip in _GUARD_SKIP):
            return node
        if isinstance(node, str):
            return check(node, path)
        if isinstance(node, list):
            out = []
            for i, item in enumerate(node):
                new = walk(item, f"{path}.{i}")
                # An item whose title/label was the claim goes entirely: its
                # leftover one-liner means nothing without its heading.
                lost_head = isinstance(item, dict) and any(item.get(k) and not new.get(k) for k in ("title", "label"))
                empty = new == "" or lost_head or (isinstance(new, dict) and not (new.get("title") or new.get("text") or new.get("label")))
                if not empty or not isinstance(item, (str, dict)):
                    out.append(new)
            return out
        if isinstance(node, dict):
            return {k: walk(v, f"{path}.{k}" if path else k) for k, v in node.items()}
        return node

    guarded = walk(content, "")
    for r in removed:
        log(f"[claim-guard] removed unverified {r['kind']} claim at {r['path']}: \"{r['text']}\"")
    content.clear()
    content.update(guarded)
    return removed


def fallback_content(facts):
    """Plain, true copy from the facts alone (no API key, or the AI failed)."""
    name, town, trade = facts["name"], facts.get("town") or "", facts.get("trade") or "Local business"
    first = facts.get("owner_first_name") or ""
    trade_l = trade.lower()
    key = _trade_key(trade)
    svc = TRADE_DEFAULTS.get(key, ("clean-local", []))[1] or [("wrench", "Repairs"), ("house", "New work"),
                                                              ("clipboard", "Quotes"), ("clock", "Callouts")]
    where = f" in {town}" if town else ""
    who = first or "we"
    return {
        "seo": {"title": f"{name} | {trade}{where}",
                "description": f"{name}, {trade_l}{where}{', Co. ' + facts['county'] if facts.get('county') else ''}. "
                               + (f"Call {facts['phone']['display']}." if facts.get("phone") else "Get in touch for a quote.")},
        "hero": {"headline": f"{trade}{where}, one call away.",
                 "subhead": f"{name} works across {town or 'the area'} and the towns around it. Ring for a chat or a quote.",
                 "secondaryCta": "Get a free quote"},
        "nav": {"cta": f"Call {first}" if first else "Call us", "note": f"{trade}{where}"},
        "trust": {"items": [{"icon": "pin", "title": f"Local to {town}" if town else "Local", "text": "Out to you quickly, no long waits."},
                            {"icon": "phone", "title": "Talk to the person doing the job", "text": "No call centre."},
                            {"icon": "receipt", "title": "Clear quotes", "text": "You know the price before work starts."}]},
        "services": {"heading": "What we do", "items": [{"icon": i, "title": t} for i, t in svc]},
        "about": {"heading": f"Local work{where}.",
                  "body": [f"{name} is based in {town or 'the area'} and works for homes and businesses nearby.",
                           f"Ring and {'you will get ' + first if first else 'you will get the person who does the work'}."]},
        "process": {"heading": "How it works",
                    "steps": [{"title": "Get in touch", "text": "Call, WhatsApp or send the form."},
                              {"title": "Get a price", "text": "A clear quote before anything starts."},
                              {"title": "Job done", "text": "Done properly and left tidy."}]},
        "reviews": {"heading": "What customers say"},
        "area": {"heading": "Where we work", "intro": f"Based in {town} and working in the towns around it." if town else ""},
        "cta": {"heading": "Need a hand?", "text": f"Ring {who if first else 'us'} and we'll take it from there."},
        "contact": {"heading": "Get a quote", "intro": "Leave your details and we'll come back to you.",
                    "services": [t for _, t in svc] + ["Something else"], "submit": "Send",
                    "success": "Thanks, we'll be in touch soon."},
        "footer": {"blurb": f"{trade}{where}."},
    }


def build_prompt(facts, catalogue):
    compact = {
        "presets": catalogue["presets"],
        "rules": catalogue["rules"],
        "variants": [{k: v[k] for k in ("id", "slot", "desc", "needs", "best", "tone")} for v in catalogue["variants"]
                     if labs_enabled() or not v.get("labs")],
    }
    fact_lines = {k: facts.get(k) for k in ("name", "trade", "town", "county", "owner_first_name", "email",
                                            "rating", "review_count", "towns", "hours", "has_website")}
    fact_lines["phone"] = (facts.get("phone") or {}).get("display", "")
    fact_lines["whatsapp"] = bool((facts.get("phone") or {}).get("wa"))
    fact_lines["photos"] = sorted((facts.get("images") or {}).keys())
    fact_lines["reviews"] = [{"rating": r["rating"], "text": r["text"][:300]} for r in facts.get("reviews", [])[:5]]
    return (
        "You compose a one-page website for a real Irish local business from a section library, "
        "and write all of its copy. Return ONLY a JSON object, no prose, no code fences.\n\n"
        "PRESET: choose one of heritage | industrial | clean-local | bold that fits this business "
        "(trade, domestic vs commercial, how the name reads).\n"
        "SECTIONS: ordered list of {\"variant\": id, \"tone\"?: base|surface|band|accent} using ONLY ids "
        "from the catalogue, one per slot, following its rules. Only use a reviews-* variant when reviews "
        "are listed below. Never use gallery-*. Use hero-image-grid only with 3 photos.\n\n"
        "COPY RULES (these are binding):\n"
        "- Irish English spelling. Plain, warm, local, confident. Short sentences. No exclamation marks.\n"
        "- The hero headline names the trade (or what they do) AND the home town, max 10 words.\n"
        "- NEVER invent facts: no years in business, founding dates, registrations (Safe Electric, RECI, "
        "RGII, SEAI), insurance, guarantees, awards, prices, percentages, team size, family-run, or numbers "
        "of jobs. No fake urgency. If a claim isn't in the facts, don't make it.\n"
        "- Use the owner's first name only if owner_first_name is given; otherwise say 'we'.\n"
        "- Services: 4-6 things this trade typically does, each with a one-line description.\n"
        "- Trust items: 3 plain promises about how the work is handled or facts from the data (the towns "
        "covered, opening hours, call/WhatsApp direct, you talk to the person doing the job). NEVER the "
        "rating or reviews (they appear elsewhere). No credentials. Years in business only if given.\n"
        "- Icons: pick from this list only: " + ", ".join(icon_names()) + "\n"
        "- Button labels: primaryCta like 'Call 087 123 4567' (use the phone), secondaryCta like "
        "'Get a free quote' or 'WhatsApp a photo' (only mention WhatsApp if whatsapp is true).\n\n"
        "OUTPUT SHAPE:\n"
        '{"preset": "...", "sections": [{"variant": "nav-minimal"}, ...], "content": {'
        '"seo": {"title", "description"}, "nav": {"cta", "note"}, '
        '"hero": {"headline", "subhead", "primaryCta", "secondaryCta"}, '
        '"trust": {"heading", "items": [{"icon", "title", "text"}]}, '
        '"services": {"heading", "intro", "items": [{"icon", "title", "text", "points"?: []}]}, '
        '"about": {"heading", "body": ["para", "para"], "signoff"?, "facts"?: [{"label", "value"}]}, '
        '"process": {"heading", "intro", "steps": [{"title", "text"}]}, '
        '"reviews": {"heading", "intro"}, "area": {"heading", "intro", "note"}, '
        '"cta": {"heading", "text", "primary", "secondary"}, '
        '"contact": {"heading", "intro", "formHeading", "services": ["option"], "submit", "success"}, '
        '"footer": {"blurb"}, "mobileBar": {"call", "whatsapp", "quote"}}}\n\n'
        f"BUSINESS FACTS:\n{json.dumps(fact_lines, ensure_ascii=False)}\n\n"
        f"CATALOGUE:\n{json.dumps(compact, separators=(',', ':'), ensure_ascii=False)}\n"
    )


def _parse_json_object(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def compose_with_ai(client, model, facts):
    """(preset, raw sections, raw content) from Claude, or raises."""
    message = client.messages.create(
        model=model, max_tokens=6000,
        messages=[{"role": "user", "content": build_prompt(facts, load_catalogue())}],
    )
    text = "".join(b.text for b in message.content if getattr(b, "type", "") == "text")
    data = _parse_json_object(text)
    if not isinstance(data, dict):
        raise ValueError("composer returned no object")
    return data.get("preset"), data.get("sections"), data.get("content")


def finalize_content(base, facts, sections, images):
    """Merge sanitized copy with facts SiteForge knows to be true."""
    c = dict(base)
    trade, town, name = facts.get("trade") or "", facts.get("town") or "", facts["name"]
    first = facts.get("owner_first_name") or ""
    phone = facts.get("phone")
    c["business"] = {k: v for k, v in {
        "name": name, "trade": trade, "town": town, "county": facts.get("county") or "",
        "ownerFirstName": first, "phone": phone, "email": facts.get("email") or "",
        "hours": facts.get("hours") or "", "mapsUrl": facts.get("maps_url") or "",
        "lat": facts.get("lat"), "lng": facts.get("lng"),
    }.items() if v not in (None, "", {})}

    hero = dict(c.get("hero") or {})
    fb = fallback_content(facts)
    if not hero.get("headline"):
        hero["headline"] = fb["hero"]["headline"]
    elif town and town.lower() not in hero["headline"].lower():
        # The first screen must say where: keep their line as the subhead.
        hero["subhead"] = hero.get("subhead") or hero["headline"]
        hero["headline"] = f"{trade or 'Local work'} in {town}." if trade else f"Local work in {town}."
    if phone and not hero.get("primaryCta"):
        hero["primaryCta"] = f"Call {phone['display']}"
    if facts.get("rating") and facts.get("review_count", 0) >= 3:
        hero["note"] = f"Rated {facts['rating']:.1f} from {facts['review_count']} Google reviews"
    if images.get("hero"):
        hero["image"] = images["hero"]
    quote = hero_quote(facts.get("reviews"))
    if quote:
        hero["quote"] = quote
    mark = TRADE_MARK_ICON.get(_trade_key(trade))
    if mark:
        hero["icon"] = mark  # the typographic hero's oversized outline mark
    c["hero"] = hero
    for key in ("seo", "services", "contact", "footer", "process", "about", "trust", "cta", "area"):
        if not (c.get(key) or {}).get("items" if key in ("services",) else next(iter(fb.get(key, {})), "")):
            c[key] = {**fb.get(key, {}), **(c.get(key) or {})}
    if not (c.get("services") or {}).get("items"):
        c["services"] = fb["services"]
    if images.get("about"):
        c.setdefault("about", {})["image"] = images["about"]
    if not first and (c.get("about") or {}).get("signoff"):
        c["about"].pop("signoff", None)

    reviews = facts.get("reviews") or []
    if reviews:
        r = dict(c.get("reviews") or {})
        r.setdefault("heading", "What customers say")
        r.update({"rating": facts.get("rating"), "count": facts.get("review_count"), "source": "Google",
                  "link": facts.get("maps_url") or "", "items": reviews})
        if facts.get("review_count"):
            r["linkLabel"] = f"Read all {facts['review_count']} reviews on Google"
        c["reviews"] = {k: v for k, v in r.items() if v not in (None, "")}
    elif facts.get("rating"):
        c["reviews"] = {"heading": "", "rating": facts["rating"], "count": facts.get("review_count"),
                        "link": facts.get("maps_url") or "", "items": []}
    else:
        c.pop("reviews", None)

    area = dict(c.get("area") or {})
    area.setdefault("heading", "Where we work")
    area["towns"] = facts.get("towns") or ([town] if town else [])
    c["area"] = area

    slots = {s["slot"] for s in sections}
    links = [("services", "Services", "#services"), ("about", "About", "#about"), ("process", "How it works", "#process"),
             ("reviews", "Reviews", "#reviews"), ("service-area", "Areas", "#area"), ("contact", "Contact", "#contact")]
    nav = dict(c.get("nav") or {})
    nav["links"] = [{"label": label, "href": href} for slot, label, href in links
                    if slot in slots and (slot != "reviews" or reviews)]
    c["nav"] = nav
    c.setdefault("footer", {})["legal"] = f"© {date.today().year} {name}"
    mb = dict(c.get("mobileBar") or {})
    mb.setdefault("call", f"Call {first}" if first else "Call now")
    mb.setdefault("whatsapp", "WhatsApp")
    mb.setdefault("quote", "Get a quote")
    c["mobileBar"] = mb
    c["ui"] = ui_defaults()
    order = ["business", "seo", "nav", "hero", "trust", "services", "about", "process", "reviews", "gallery",
             "area", "cta", "contact", "footer", "mobileBar", "ui"]
    return {k: c[k] for k in order if k in c and c[k] not in (None, {}, [])}


def compose(facts, client=None, model=None, log=print):
    """(preset, sections, content, source). AI first, plain fallback after."""
    preset, raw_sections, raw_content, source = None, None, None, "fallback"
    if client is not None:
        try:
            preset, raw_sections, raw_content = compose_with_ai(client, model, facts)
            source = "ai"
        except Exception as exc:  # noqa: BLE001 - any API/JSON failure falls back to plain copy
            log(f"[compose] AI composition failed, using fallback: {exc}")
    if preset not in PRESETS:
        preset = facts.get("preset") if facts.get("preset") in PRESETS else default_preset(facts.get("trade"))
    if facts.get("preset") in PRESETS:
        preset = facts["preset"]  # a style the operator picked earlier wins
    sections = normalize_sections(raw_sections or [{"variant": v} for v in FALLBACK_SECTIONS[preset]], facts, preset)
    content = sanitize_content(raw_content, facts) if raw_content else fallback_content(facts)
    content = finalize_content(content, facts, sections, facts.get("images") or {})
    facts["claims_removed"] = claim_guard(content, facts, log=log)
    return preset, sections, content, source


# ---------------------------------------------------------------------------
# Gemini scene photos, kept only if a vision check passes
# ---------------------------------------------------------------------------

SCENES = {
    "electrician": ("an electrician's hands wiring a new consumer unit in an Irish home, tools on a dust sheet",
                    "a tidy open electrician's tool bag with a multimeter and cable on a workbench"),
    "plumber": ("a plumber fitting copper pipework under a kitchen sink in an Irish home",
                "a plumber's tools laid out on a bathroom floor beside a new chrome shower valve"),
    "heating engineer": ("a heating engineer servicing a wall-mounted boiler in a utility room",
                         "a pressure gauge and tools beside a radiator valve"),
    "roofer": ("a roofer replacing slates on a pitched roof of an Irish house under a grey sky",
               "a new felt flat roof on a small rear extension, rolls of membrane and tools"),
    "landscaper": ("a neatly edged lawn and freshly planted borders in an Irish back garden, overcast light",
                   "gardening tools and a wheelbarrow of mulch beside a trimmed hedge"),
    "painter": ("a painter rolling a warm neutral colour onto a living room wall, dust sheets on the floor",
                "brushes and a paint tin on a step ladder in a bright room"),
    "builder": ("a builder laying blockwork for a single-storey extension on an Irish suburban site",
                "a spirit level, trowel and plans on a stack of concrete blocks"),
    "cafe": ("a flat white and a scone on a wooden counter in a small Irish café, morning light",
             "a barista's hands pouring milk into a cup at an espresso machine"),
}


def _scene_prompt(scene, aspect):
    return (
        f"Documentary-style photograph: {scene}. Shot on a full-frame camera, 35mm lens, natural light, "
        "realistic colours, shallow depth of field, candid and unposed. Composition leaves calm space. "
        "No text, no signage, no logos, no watermarks, no brand names, no faces in close-up. "
        f"Aspect ratio {aspect}."
    )


def gemini_image(api_key, model, prompt, aspect):
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}},
        timeout=120,
    )
    resp.raise_for_status()
    for cand in resp.json().get("candidates") or []:
        for part in ((cand.get("content") or {}).get("parts") or []):
            data = (part.get("inlineData") or part.get("inline_data") or {}).get("data")
            if data:
                return base64.b64decode(data)
    raise ValueError("Gemini returned no image")


QA_PROMPT = (
    "You are checking an AI-generated photo before it goes on a real small business's website. Be strict: "
    "reject anything a customer might notice is fake. Reject if ANY of: visible text/letters/logos/watermarks; "
    "malformed hands, fingers, tools or objects; warped geometry (bent pipes/walls that shouldn't be, melted "
    "details); plastic or over-smooth 'AI look'; wrong trade or setting for: {subject}; not plausibly Ireland; "
    "cluttered or low quality. Return ONLY JSON: "
    '{{"ok": true|false, "score": 1-10, "problems": ["..."], "alt": "plain one-sentence alt text"}}'
)


def qa_image(client, model, image_bytes, subject, prompt=None):
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    msg = client.messages.create(
        model=model, max_tokens=400,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(buf.getvalue()).decode("ascii")}},
            {"type": "text", "text": (prompt or QA_PROMPT).format(subject=subject)},
        ]}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return _parse_json_object(text)


def scene_images(facts, cache_dir, gemini_key, gemini_model, client, claude_model, log=print, min_score=7,
                 slots=("hero", "about")):
    """{"hero": {src, alt, width, height}, "about": {...}} for images that
    passed QA. Cached per lead in cache_dir, so rebuilds cost nothing. With
    no Gemini key or no Claude client (nothing to check quality) → {}."""
    if not (gemini_key and client):
        return {}
    key = _trade_key(facts.get("trade"))
    scenes = SCENES.get(key)
    if not scenes:
        return {}
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    jobs = [job for job in (("hero", scenes[0], "4:3"), ("about", scenes[1], "4:5")) if job[0] in slots]

    def one(job):
        slot, scene, aspect = job
        meta_path = cache_dir / f"{slot}.json"
        meta = read_json(meta_path)
        if meta and (cache_dir / meta.get("file", "")).exists():
            return slot, meta if meta.get("ok") else None
        for attempt in range(2):
            try:
                raw = gemini_image(gemini_key, gemini_model, _scene_prompt(scene, aspect), aspect)
                verdict = qa_image(client, claude_model, raw, f"{facts.get('trade') or 'local business'} ({scene})")
            except Exception as exc:  # noqa: BLE001 - photos are optional; never fail a build
                log(f"[images] {slot}: {exc}")
                break
            ok = bool(verdict.get("ok")) and int(verdict.get("score") or 0) >= min_score
            log(f"[images] {slot} attempt {attempt + 1}: score {verdict.get('score')} "
                f"{'kept' if ok else 'rejected'} {verdict.get('problems') or ''}")
            if ok:
                from PIL import Image
                im = Image.open(io.BytesIO(raw)).convert("RGB")
                im.thumbnail((1800, 1800))
                name = f"{slot}.webp"
                im.save(cache_dir / name, "WEBP", quality=80)
                meta = {"ok": True, "file": name, "alt": _clean_str(verdict.get("alt"), 160) or scene,
                        "width": im.width, "height": im.height, "score": verdict.get("score"),
                        "prompt": _scene_prompt(scene, aspect), "model": gemini_model, "created": time.time()}
                write_json(meta_path, meta)
                return slot, meta
        write_json(meta_path, {"ok": False, "file": "", "created": time.time()})
        return slot, None

    out = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for slot, meta in pool.map(one, jobs):
            if meta:
                out[slot] = meta
    return out


PLACES_QA_PROMPT = (
    "This is a photo a business uploaded to its Google listing. Could it be used, as is, as a large "
    "photo on that business's own website ({subject})? Reject logos, flyers, business cards, "
    "screenshots, text-heavy images, blurry or dark shots, close-up selfies, and anything unrelated. "
    'Return ONLY JSON: {{"ok": true|false, "score": 1-10, "problems": ["..."], "alt": "plain one-sentence alt text"}}'
)


def _places_photo_bytes(api_key, name, max_width=1800):
    resp = requests.get(f"https://places.googleapis.com/v1/{name}/media",
                        params={"maxWidthPx": max_width, "key": api_key}, timeout=60)
    resp.raise_for_status()
    if not resp.headers.get("Content-Type", "").startswith("image/"):
        raise ValueError("not an image")
    return resp.content


def places_photos(facts, cache_dir, api_key, client, claude_model, log=print):
    """The lead's own Google Places photos: the best landscape photo at
    least 1200px wide for the hero, a second good photo for About. Each is
    checked by Claude vision when available (logos, flyers and screenshots
    are common uploads). Keeps Google's required author attribution.
    Cached per lead like the Gemini photos."""
    photos = [p for p in (facts.get("place_photos") or []) if p.get("name")]
    if not (api_key and photos):
        return {}
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = read_json(cache_dir / "places.json")
    if cached is not None and cached.get("names") == [p["name"] for p in photos]:
        return {k: v for k, v in cached.get("chosen", {}).items() if (cache_dir / v["file"]).exists()}

    def wide(p):
        return int(p.get("widthPx") or 0), int(p.get("heightPx") or 0)

    landscape = sorted((p for p in photos if wide(p)[0] >= 1200 and wide(p)[0] > wide(p)[1] * 1.15),
                       key=lambda p: -(wide(p)[0] * wide(p)[1]))
    others = sorted((p for p in photos if wide(p)[0] >= 800), key=lambda p: -(wide(p)[0] * wide(p)[1]))
    chosen, used = {}, set()
    subject = f"{facts.get('trade') or 'local business'} {facts.get('name', '')}"
    for slot, pool in (("hero", landscape[:4]), ("about", others[:6])):
        for p in pool:
            if p["name"] in used:
                continue
            try:
                raw = _places_photo_bytes(api_key, p["name"])
                verdict = {"ok": True, "score": 7, "alt": ""}
                if client is not None:
                    verdict = qa_image(client, claude_model, raw, subject, prompt=PLACES_QA_PROMPT)
            except Exception as exc:  # noqa: BLE001 - photos are optional
                log(f"[places photos] {slot}: {exc}")
                continue
            if not verdict.get("ok") or int(verdict.get("score") or 0) < 6:
                log(f"[places photos] {slot}: rejected {verdict.get('problems') or ''}")
                used.add(p["name"])
                continue
            from PIL import Image
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((1800, 1800))
            fname = f"places-{slot}.webp"
            im.save(cache_dir / fname, "WEBP", quality=82)
            authors = ", ".join(a.get("displayName", "") for a in (p.get("authorAttributions") or []) if a.get("displayName"))
            chosen[slot] = {"ok": True, "file": fname, "width": im.width, "height": im.height,
                            "alt": _clean_str(verdict.get("alt"), 160) or f"{facts.get('name', '')} photo",
                            "credit": f"Photo: {authors} on Google" if authors else "Photo: Google",
                            "source": "google_places", "photo_name": p["name"]}
            used.add(p["name"])
            break
    write_json(cache_dir / "places.json", {"names": [p["name"] for p in photos], "chosen": chosen, "created": time.time()})
    return chosen


def install_images(site_dir, cache_dir, metas):
    """Copy approved images into public/images and return content.json image objects."""
    dest = Path(site_dir) / "public" / "images"
    dest.mkdir(parents=True, exist_ok=True)
    result = {}
    for slot, meta in metas.items():
        shutil.copy2(Path(cache_dir) / meta["file"], dest / meta["file"])
        result[slot] = {"src": f"/images/{meta['file']}", "alt": meta.get("alt", ""),
                        "width": meta.get("width"), "height": meta.get("height")}
        if meta.get("credit"):
            result[slot]["credit"] = meta["credit"]
    return result


_install_lock = threading.Lock()
