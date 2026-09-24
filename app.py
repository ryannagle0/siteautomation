"""SiteForge v0.1 - local lead-gen / demo-site / outreach tool."""
import asyncio
import atexit
import base64
import csv
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from threading import Timer

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
LEADS_CSV = BASE_DIR / "leads.csv"  # legacy file, only read once for migration
LEADS_DB = BASE_DIR / "leads.db"
SITES_DIR = BASE_DIR / "sites"
TEMPLATE_SITE = SITES_DIR / "derek-doyle-electrical"

CSV_FIELDS = [
    "name", "phone", "email", "website", "location", "score", "years",
    "slug", "demo_built", "demo_url", "email_sent", "replied", "sold",
]

app = Flask(__name__)

# ---------------------------------------------------------------------------
# .env loading (no external dependency required)
# ---------------------------------------------------------------------------

def load_env():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
TWENTYFIRST_API_KEY = os.environ.get("TWENTYFIRST_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
OPERATOR_NAME = os.environ.get("OPERATOR_NAME", "")
OPERATOR_PHONE = os.environ.get("OPERATOR_PHONE", "")

try:
    import anthropic
    _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except Exception:
    _client = None

CLAUDE_MODEL = "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------
# read_leads()/write_leads()/leads_transaction() keep the exact same
# signatures they had as CSV helpers (list-of-dict in, list-of-dict out) so
# every call site elsewhere in this file — which works with plain Python
# dicts/lists, not SQL — needed zero changes. SQLite's own file locking
# handles concurrent access, so there's no separate lock to take: a fresh
# short-lived connection is opened per call, matching how the CSV version
# opened the file fresh each time.


def _get_conn():
    conn = sqlite3.connect(LEADS_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db():
    conn = _get_conn()
    try:
        columns_sql = ", ".join(f'"{f}" TEXT NOT NULL DEFAULT \'\'' for f in CSV_FIELDS)
        conn.execute(f"CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})")
        conn.commit()
        existing = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    finally:
        conn.close()

    # One-time migration from the old leads.csv, if present and the table is
    # still empty (so this never overwrites data already in the database).
    if existing == 0 and LEADS_CSV.exists():
        with LEADS_CSV.open("r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if rows:
            write_leads([{k: row.get(k, "") for k in CSV_FIELDS} for row in rows])


def read_leads():
    ensure_db()
    conn = _get_conn()
    try:
        rows = conn.execute(f"SELECT {', '.join(CSV_FIELDS)} FROM leads ORDER BY id").fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def write_leads(rows):
    placeholders = ", ".join("?" for _ in CSV_FIELDS)
    columns = ", ".join(CSV_FIELDS)
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM leads")
        conn.executemany(
            f"INSERT INTO leads ({columns}) VALUES ({placeholders})",
            [tuple(row.get(k, "") for k in CSV_FIELDS) for row in rows],
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def leads_transaction():
    """Read the rows, yield them for in-place mutation, then write them back.

    Kept as a single connection/transaction so the read-modify-write is
    atomic under SQLite's own locking — a concurrent writer blocks (up to
    the connection timeout) rather than racing this one.
    """
    ensure_db()
    conn = _get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(f"SELECT {', '.join(CSV_FIELDS)} FROM leads ORDER BY id").fetchall()
        leads = [dict(row) for row in rows]
        yield leads
        placeholders = ", ".join("?" for _ in CSV_FIELDS)
        columns = ", ".join(CSV_FIELDS)
        conn.execute("DELETE FROM leads")
        conn.executemany(
            f"INSERT INTO leads ({columns}) VALUES ({placeholders})",
            [tuple(row.get(k, "") for k in CSV_FIELDS) for row in leads],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "business"


def rmtree_retry(path, attempts=10, delay=1.0):
    """shutil.rmtree with retries — Windows can briefly hold a file lock on
    node_modules' native binaries right after a spawned process is killed."""
    for attempt in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except (PermissionError, OSError):
            if attempt == attempts - 1:
                raise
            time.sleep(delay)


def _background_rmtree(path):
    try:
        rmtree_retry(path, attempts=30, delay=2.0)
    except (PermissionError, OSError):
        pass  # best-effort cleanup; a leftover .stale-* folder is harmless


def clear_site_dir(dest):
    """Make `dest` available for a fresh copytree.

    A file inside node_modules (native binaries, or just something Windows
    Defender / Search Indexer is mid-scan on) can stay locked for a few
    seconds after the process that used it exits — even after killing every
    process we know about (see kill_stale_preview / stop_preview_server).
    Deleting in place blocks the whole request on that lock clearing.
    Renaming out of the way succeeds far more often even with a locked file
    inside, since Windows resolves open handles by file object, not path —
    so prefer that, and clean up the renamed copy in the background.
    """
    if not dest.exists():
        return
    try:
        stale = dest.with_name(f"{dest.name}.stale-{time.time_ns()}")
        dest.rename(stale)
        threading.Thread(target=_background_rmtree, args=(stale,), daemon=True).start()
        return
    except OSError:
        pass
    rmtree_retry(dest, attempts=20, delay=1.5)


def phone_variants(raw):
    """Derive tel:/wa.me/intl/display phone formats from a scraped IE number."""
    raw = (raw or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return {"display": "", "tel": "", "intl": "", "wa": ""}
    if raw.startswith("+"):
        intl_digits = digits
    elif digits.startswith("353"):
        intl_digits = digits
    elif digits.startswith("0"):
        intl_digits = "353" + digits[1:]
    else:
        intl_digits = "353" + digits
    tel = ("0" + intl_digits[3:]) if intl_digits.startswith("353") else digits
    return {"display": raw, "tel": tel, "intl": "+" + intl_digits, "wa": intl_digits}


def owner_first_name(business_name):
    """Best-effort guess at a first name to use in personal-toned copy."""
    first = re.split(r"\s+", (business_name or "").strip())[0] if business_name else ""
    first = re.sub(r"[^A-Za-z'-]", "", first)
    return first or "the team"


def hero_headline(town, years):
    """"[Town]'s electrician[. For over N years.]" — the years claim only
    appears when we actually have years-in-business data for the lead
    (there's no such data from the scraper today, so it's omitted by
    default rather than reusing the template's original "20 years")."""
    town = (town or "").strip() or "Ireland"
    headline = f"{town}&rsquo;s electrician."
    years = (years or "").strip()
    if years:
        headline += f" For over {years} years."
    return headline


DUBLIN_FALLBACK_COORDS = (-6.2603, 53.3331)  # longitude, latitude
_geocode_cache = {}
_geocode_lock = threading.Lock()
_last_geocode_call = [0.0]


def geocode_location(location_text):
    """Best-effort geocode of a scraped address via Nominatim (OSM), so each
    demo site's contact-section map actually points at the lead's own area
    instead of a hardcoded Dublin pin. Falls back to Dublin on any failure —
    scraped addresses are messy and Nominatim has no API key/quota to lean on.
    Returns (longitude, latitude).
    """
    location_text = (location_text or "").strip()
    if not location_text:
        return DUBLIN_FALLBACK_COORDS
    if location_text in _geocode_cache:
        return _geocode_cache[location_text]

    query = location_text if "ireland" in location_text.lower() else f"{location_text}, Ireland"
    with _geocode_lock:
        # Nominatim's usage policy caps free requests at 1/sec.
        wait = 1.0 - (time.time() - _last_geocode_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_geocode_call[0] = time.time()
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "ie"},
            headers={"User-Agent": "SiteForge/0.1 (local lead-gen tool)"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            coords = (float(results[0]["lon"]), float(results[0]["lat"]))
            _geocode_cache[location_text] = coords
            return coords
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass

    _geocode_cache[location_text] = DUBLIN_FALLBACK_COORDS
    return DUBLIN_FALLBACK_COORDS


# ---------------------------------------------------------------------------
# Next.js demo-site preview servers (one `next dev` per built site)
# ---------------------------------------------------------------------------

NPM_CMD = "npm.cmd" if os.name == "nt" else "npm"
RUNNING_PREVIEWS = {}  # slug -> {"process": Popen, "port": int, "log_file": file}
_claimed_ports = set()  # ports we've handed out but whose process may not be listening yet
_preview_lock = threading.Lock()
# Running many `npm install`s at once (e.g. clicking Build Site on several
# leads back to back) has caused transient Windows subprocess failures under
# the resulting CPU/disk/process-creation load. Serialize installs instead —
# builds queue up rather than fight each other for resources.
_npm_install_lock = threading.Lock()


def find_free_port(start=4100, end=4999):
    """Pick a port nobody's listening on AND nobody's already been handed
    (a spawned `next dev` process may not be listening yet, so a plain
    socket-connect check alone isn't race-safe between concurrent builds).
    Caller must hold _preview_lock.
    """
    for port in range(start, end):
        if port in _claimed_ports:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                _claimed_ports.add(port)
                return port
    raise RuntimeError("no free port available for preview server")


def wait_for_port(port, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.5)
    return False


def wait_for_preview_ready(port, timeout=90):
    """Wait until the dev server doesn't just accept connections but actually
    serves a real compiled page. `next dev` opens its port almost immediately
    on startup, long before webpack has compiled the "/" route for the first
    time — waiting on the port alone tells the frontend "ready" while the
    page is still mid-compile, which is what caused the blank white iframe.
    """
    if not wait_for_port(port, timeout=min(timeout, 25)):
        return False
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/"
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.text) > 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def kill_process_on_port(port):
    """Windows: `npm run dev` spawns node.exe as a detached child of the
    npm.cmd shell, so terminating the Popen handle (or even /T tree-killing
    it) doesn't reliably reach the actual listening node.exe — it can be
    reparented before we get to it. Killing whatever's actually bound to the
    port is the only reliable way to free the node_modules file lock.
    """
    if os.name != "nt":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=10
        )
    except Exception:
        return
    needle = f":{port} "
    for line in result.stdout.splitlines():
        if needle in line and "LISTENING" in line:
            pid = line.split()[-1]
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid], capture_output=True, timeout=10
                )
            except Exception:
                pass


def run_npm_install(site_dir, log_path, attempts=2):
    """Run `npm install`, retrying once on transient Windows subprocess/
    resource failures (these have been seen to succeed on retry after many
    concurrent builds/dev servers put load on the system — genuine npm
    errors, by contrast, show up as a normal non-zero exit with output in
    the log, not a caught Python exception). Any Python-level exception
    (as opposed to a normal npm failure) is now written into the log
    instead of being silently swallowed, since an empty log with no clue
    why is undiagnosable."""
    last_exc = None
    for attempt in range(attempts):
        try:
            with _npm_install_lock, open(log_path, "w", encoding="utf-8") as log:
                result = subprocess.run(
                    [NPM_CMD, "install"],
                    cwd=str(site_dir),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=480,
                    shell=(os.name == "nt"),
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            last_exc = exc
            time.sleep(2)

    try:
        with open(log_path, "w", encoding="utf-8") as log:
            log.write(
                f"npm install could not even start (not a normal npm error):\n"
                f"{type(last_exc).__name__}: {last_exc}\n"
            )
    except OSError:
        pass
    return False


def _devserver_marker_path(site_dir):
    return site_dir / ".devserver.json"


def start_preview_server(slug):
    """(Re)start `next dev` for a built site and return its port."""
    site_dir = SITES_DIR / slug
    with _preview_lock:
        existing = RUNNING_PREVIEWS.get(slug)
        if existing and existing["process"].poll() is None:
            return existing["port"]

    # Not tracked in this process's memory — but a prior SiteForge run may
    # have left a dev server (and its marker file) behind. Clean it up
    # before claiming a fresh port, or we'll leak an orphaned node.exe.
    kill_stale_preview(site_dir)

    with _preview_lock:
        port = find_free_port()
        log_file = open(site_dir / "dev-server.log", "w", encoding="utf-8")
        proc = subprocess.Popen(
            [NPM_CMD, "run", "dev", "--", "-p", str(port)],
            cwd=str(site_dir),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            shell=(os.name == "nt"),
        )
        RUNNING_PREVIEWS[slug] = {"process": proc, "port": port, "log_file": log_file}
        # Persist pid+port to disk so a *future* SiteForge process (after a
        # restart) can still find and kill this server — RUNNING_PREVIEWS
        # lives only in this process's memory, but the spawned node.exe
        # keeps running (and keeps its node_modules file locks) across any
        # number of Flask restarts unless something kills it explicitly.
        try:
            _devserver_marker_path(site_dir).write_text(
                json.dumps({"pid": proc.pid, "port": port}), encoding="utf-8"
            )
        except OSError:
            pass
        return port


def _kill_pid_tree(pid):
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True, timeout=10,
            )
        else:
            os.kill(pid, 15)
    except Exception:
        pass


def kill_stale_preview(site_dir):
    """Kill whatever dev server previously ran for this site directory, even
    one started by an earlier (now-restarted) SiteForge process. Always call
    this before deleting node_modules — see start_preview_server's comment.
    """
    marker = _devserver_marker_path(site_dir)
    if not marker.exists():
        return
    try:
        info = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        marker.unlink(missing_ok=True)
        return
    if info.get("pid"):
        _kill_pid_tree(info["pid"])
    if info.get("port"):
        kill_process_on_port(info["port"])
        with _preview_lock:
            _claimed_ports.discard(info["port"])
    marker.unlink(missing_ok=True)
    time.sleep(0.5)  # give Windows a beat to release file handles


def stop_preview_server(slug):
    with _preview_lock:
        info = RUNNING_PREVIEWS.pop(slug, None)
        if not info:
            return
        proc = info["process"]
        _kill_pid_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:
            pass
        # Belt and braces on Windows: the tree-kill above can miss node.exe if
        # npm.cmd already reparented it, so also kill whatever's actually
        # bound to the port before we try to delete node_modules.
        kill_process_on_port(info["port"])
        try:
            info["log_file"].close()
        except Exception:
            pass
        _claimed_ports.discard(info["port"])
        _devserver_marker_path(SITES_DIR / slug).unlink(missing_ok=True)
        time.sleep(0.5)  # give Windows a beat to release file handles


@atexit.register
def _cleanup_previews():
    for slug in list(RUNNING_PREVIEWS):
        stop_preview_server(slug)


# ---------------------------------------------------------------------------
# Scraping + scoring
# ---------------------------------------------------------------------------

FREE_BUILDER_HINTS = ["webador", "wix.com", "weebly", "godaddysites", "sites.google"]
FREE_EMAIL_HINTS = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com"]


def score_lead(name, website, email):
    name = (name or "").lower()
    website = (website or "").lower().strip()
    email = (email or "").lower().strip()
    has_site = bool(website)
    is_free_email = any(h in email for h in FREE_EMAIL_HINTS)
    is_ie_email = email.endswith(".ie")

    if "ltd" in re.split(r"\W+", name) or is_ie_email:
        return 0
    if not has_site:
        return 10 if is_free_email else 9
    if any(h in website for h in FREE_BUILDER_HINTS):
        return 8
    if is_free_email:
        return 7
    return 5


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def split_query(query):
    """Split a free-text "trade location" query into (what, where)."""
    parts = query.strip().split()
    if len(parts) < 2:
        return query.strip(), ""
    return " ".join(parts[:-1]), parts[-1]


def fetch_detail_email(session, detail_url):
    """Visit a listing's detail page to pull an email address, if any."""
    try:
        resp = session.get(detail_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    email_el = soup.select_one("a[href^='mailto:']")
    if not email_el:
        return ""
    return email_el.get("href", "").replace("mailto:", "").split("?")[0].strip()


DETAIL_WORKERS = 12
RESULTS_PER_PAGE = 20


def fetch_results_page(session, what, where, page_num):
    """Fetch one page of goldenpages.ie business results (20 listings each),
    plus the "N results" total the page reports (for pagination bounds)."""
    url = (
        "https://www.goldenpages.ie/q/business/advanced/where/"
        + requests.utils.quote(where or "ireland")
        + "/what/"
        + requests.utils.quote(what)
        + "/"
        + (str(page_num) if page_num > 1 else "")
    )
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as exc:
        return [], None, f"Could not reach goldenpages.ie ({exc.__class__.__name__}). Check your connection and try again."

    if resp.status_code in (429, 403):
        return [], None, "Rate limited — try again in 10 minutes."
    try:
        resp.raise_for_status()
    except requests.RequestException:
        return [], None, f"goldenpages.ie returned an error (HTTP {resp.status_code}). Try again shortly."

    total_count = None
    count_match = re.search(r"([\d,]+)\s+result", resp.text, re.I)
    if count_match:
        total_count = int(count_match.group(1).replace(",", ""))

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".listing_container")
    parsed = []
    for card in cards:
        title_el = card.select_one(".listing_title_link")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        name = re.sub(r"^\d+\.\s*", "", name)  # strip leading "1." rank prefix
        if not name:
            continue

        phone_el = card.select_one(".link_listing_number")
        phone = phone_el.get("href", "").replace("tel:", "").strip() if phone_el else ""

        loc_el = card.select_one(".listing_address")
        location = loc_el.get_text(strip=True) if loc_el else ""

        website = ""
        for link in card.select(".listing_links a"):
            href = link.get("href", "")
            if link.get_text(strip=True) == "Website" and href.startswith("http"):
                website = href
                break

        detail_link = card.select_one(".listing_base_link, .listing_title_link")
        detail_href = detail_link.get("href", "") if detail_link else ""
        detail_url = (
            requests.compat.urljoin("https://www.goldenpages.ie/", detail_href)
            if detail_href else ""
        )

        parsed.append({
            "name": name,
            "phone": phone,
            "email": "",
            "website": website,
            "location": location,
            "_detail_url": detail_url,
        })
    return parsed, total_count, None


def scrape_goldenpages_page(query, page_num=1):
    """Scrape exactly one goldenpages.ie business-results page (20 listings).

    goldenpages.ie's search form POSTs to /q/business/ and redirects to
    /q/business/advanced/where/<where>/what/<what>/[page]. Email addresses
    are only shown on each listing's own detail page, so this page's ~20
    listings are resolved in parallel. Returns (results, total_count, error).
    """
    what, where = split_query(query)
    if not what:
        return [], None, "search query is empty"

    session = requests.Session()
    results, total_count, error = fetch_results_page(session, what, where, page_num)
    if error:
        return [], None, error

    def resolve_email(lead):
        if lead["_detail_url"]:
            lead["email"] = fetch_detail_email(session, lead["_detail_url"])
        return lead

    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as pool:
        futures = [pool.submit(resolve_email, lead) for lead in results]
        for future in as_completed(futures):
            future.result()

    for lead in results:
        lead.pop("_detail_url", None)

    return results, total_count, None


def scrape_google_maps(query):
    """Google Places Text Search API. Returns (leads, total_count, error),
    matching scrape_goldenpages_page's signature. Phone numbers aren't
    included in a Text Search result — that needs a separate Place Details
    call per result (using each result's "place_id"), not yet wired up
    here."""
    if not GOOGLE_MAPS_API_KEY:
        return [], None, "GOOGLE_MAPS_API_KEY not set"

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query + " Ireland", "key": GOOGLE_MAPS_API_KEY}

    resp = requests.get(url, params=params, timeout=15)
    results = resp.json().get("results", [])

    leads = []
    for r in results:
        leads.append({
            "name": r.get("name", ""),
            "phone": "",  # needs Place Details call
            "email": "",
            "website": r.get("website", ""),
            "location": r.get("formatted_address", ""),
            "score": 0,
        })
    return leads, len(results), None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    try:
        page = max(1, int(data.get("page", 1) or 1))
    except (TypeError, ValueError):
        page = 1
    if not query:
        return jsonify({"error": "query is required"}), 400

    results, total_count, error = scrape_goldenpages_page(query, page)
    if error and not results:
        return jsonify({"error": error}), 502
    scanned = len(results)

    for r in results:
        r["score"] = score_lead(r.get("name"), r.get("website"), r.get("email"))

    results = [r for r in results if r["score"] > 0]
    results.sort(key=lambda r: r["score"], reverse=True)

    total_pages = None
    if total_count:
        total_pages = -(-total_count // RESULTS_PER_PAGE)  # ceil division
    has_more = scanned > 0 and (total_pages is None or page < total_pages)

    return jsonify({
        "results": results,
        "scanned": scanned,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "has_more": has_more,
        "warning": error,
    })


@app.route("/api/pipeline", methods=["GET"])
def api_pipeline_list():
    return jsonify({"leads": read_leads()})


@app.route("/api/pipeline/add", methods=["POST"])
def api_pipeline_add():
    data = request.get_json(force=True) or {}
    new_rows = data.get("leads") or []

    added = 0
    with leads_transaction() as leads:
        existing_keys = {(l["name"], l["email"]) for l in leads}
        for lead in new_rows:
            key = (lead.get("name", ""), lead.get("email", ""))
            if key in existing_keys:
                continue
            leads.append({
                "name": lead.get("name", ""),
                "phone": lead.get("phone", ""),
                "email": lead.get("email", ""),
                "website": lead.get("website", ""),
                "location": lead.get("location", ""),
                "score": lead.get("score", ""),
                "years": lead.get("years", ""),
                "slug": slugify(lead.get("name", "")),
                "demo_built": "No",
                "demo_url": "",
                "email_sent": "No",
                "replied": "No",
                "sold": "No",
            })
            existing_keys.add(key)
            added += 1
        result_leads = list(leads)

    return jsonify({"added": added, "leads": result_leads})


def find_lead(leads, slug):
    for lead in leads:
        if lead["slug"] == slug:
            return lead
    return None


@app.route("/api/pipeline/build_site", methods=["POST"])
def api_build_site():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    lead = find_lead(read_leads(), slug)
    if not lead:
        return jsonify({"error": "lead not found"}), 404

    if not TEMPLATE_SITE.exists():
        return jsonify({"step": "template", "error": f"template folder not found: {TEMPLATE_SITE}"}), 500

    dest = SITES_DIR / lead["slug"]

    try:
        stop_preview_server(lead["slug"])
        if dest.exists():
            kill_stale_preview(dest)  # catches dev servers from a prior SiteForge run
            clear_site_dir(dest)
        shutil.copytree(TEMPLATE_SITE, dest)
    except OSError as exc:
        return jsonify({"step": "copy_template", "error": f"Could not set up the site folder: {exc}"}), 500

    try:
        phone = phone_variants(lead.get("phone", ""))
        lng, lat = geocode_location(lead.get("location", ""))
    except Exception as exc:
        return jsonify({"step": "geocode", "error": f"Could not look up the town's location: {exc}"}), 500

    replacements = {
        "{{BUSINESS_NAME}}": lead.get("name", "") or "Your Business",
        "{{TOWN}}": lead.get("location", "") or "Ireland",
        "{{EMAIL}}": lead.get("email", "") or "",
        "{{OWNER_FIRST_NAME}}": owner_first_name(lead.get("name", "")),
        "{{SLUG}}": lead["slug"],
        "{{PHONE_DISPLAY}}": phone["display"] or "Call us",
        "{{PHONE_TEL}}": phone["tel"],
        "{{PHONE_INTL}}": phone["intl"],
        "{{PHONE_WA}}": phone["wa"],
        "{{LAT}}": repr(lat),
        "{{LNG}}": repr(lng),
        "{{HERO_HEADLINE}}": hero_headline(lead.get("location", ""), lead.get("years", "")),
    }

    try:
        for path in dest.rglob("*"):
            if path.is_file() and path.suffix in {".ts", ".tsx", ".json", ".mjs", ".md", ".css"}:
                text = path.read_text(encoding="utf-8")
                new_text = text
                for token, value in replacements.items():
                    new_text = new_text.replace(token, value)
                if new_text != text:
                    path.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        return jsonify({"step": "personalize", "error": f"Could not write the personalized site files: {exc}"}), 500

    log_path = dest / "npm-install.log"
    if not run_npm_install(dest, log_path):
        tail = ""
        if log_path.exists():
            tail = log_path.read_text(encoding="utf-8", errors="ignore")[-2000:]
        return jsonify({
            "step": "npm_install",
            "error": "npm install failed — see the tail of npm-install.log below for why.",
            "log_tail": tail,
        }), 500

    port = start_preview_server(lead["slug"])
    ready = wait_for_preview_ready(port)
    if not ready:
        return jsonify({
            "step": "preview_server",
            "error": "The site was built, but the preview server didn't come up in time. "
                     "It may just need longer to compile — try Edit Site again in a minute.",
            "preview_port": port,
        }), 500

    with leads_transaction() as leads:
        lead = find_lead(leads, slug)
        if lead:
            lead["demo_built"] = "Yes"

    return jsonify({"lead": lead, "preview_port": port, "preview_ready": ready})


@app.route("/api/pipeline/preview/<slug>", methods=["GET"])
def api_preview(slug):
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not built yet"}), 404

    if not (site_dir / "node_modules").exists():
        log_path = site_dir / "npm-install.log"
        if not run_npm_install(site_dir, log_path):
            return jsonify({"error": "npm install failed"}), 500

    port = start_preview_server(slug)
    ready = wait_for_preview_ready(port)
    return jsonify({"port": port, "ready": ready})


CONTENT_FILES = [
    "tailwind.config.ts",
    "src/app/layout.tsx",
    "src/app/page.tsx",
    "src/app/globals.css",
    "src/components/icons.tsx",
    "src/components/Nav.tsx",
    "src/components/Hero.tsx",
    "src/components/TrustBar.tsx",
    "src/components/Services.tsx",
    "src/components/About.tsx",
    "src/components/Process.tsx",
    "src/components/Reviews.tsx",
    "src/components/Contact.tsx",
    "src/components/Footer.tsx",
]


def is_safe_new_component_path(rel_path):
    """Whether Claude may create a brand-new file at this path (e.g. when it
    splits a section out into its own component, like ReviewsCarousel.tsx).
    Previously any file not already in CONTENT_FILES was silently dropped —
    the import would get written but the new file never would, breaking the
    build with "Module not found". Scoped to src/components/ so this can't
    write outside the site (path traversal) or touch build config."""
    posix = rel_path.replace("\\", "/")
    if ".." in posix.split("/"):
        return False
    return bool(re.fullmatch(r"src/components/[A-Za-z0-9_\-/]+\.(tsx|ts)", posix))


def extract_json_array(text):
    """Pull the JSON array of {path, content} objects out of Claude's raw
    response text. The prompt asks for ONLY a JSON array, but on larger/more
    complex edits (e.g. integrating a big fetched component) Claude sometimes
    still wraps it in a ```json fence with leading/trailing prose, or fences
    it without the response being fence-bounded end-to-end. A naive strip of
    ^``` / ```$ only works when the fence exactly bounds the whole response —
    it silently fails (and the leftover prose breaks json.loads) any other
    time, which is the likely cause of intermittent 'invalid JSON' failures.
    This tries progressively looser extraction instead of giving up after one
    exact-match attempt."""
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\[.*\])\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def apply_edit_instruction(site_dir, instruction, layout_image=None, layout_image_media_type=None):
    """Send the site's content files + an instruction to Claude and write
    back whatever files it changes. Returns (changed_files, error).

    layout_image: optional base64-encoded screenshot/mockup used as a literal
    layout reference (e.g. colour-coded boxes the user explains in
    `instruction`, like "blue box = hero, green box = services")."""
    if not _client:
        return None, "ANTHROPIC_API_KEY not configured"

    bundle = []
    for rel in CONTENT_FILES:
        fp = site_dir / rel
        if fp.exists():
            bundle.append(f"--- FILE: {rel} ---\n{fp.read_text(encoding='utf-8')}")
    bundle_text = "\n\n".join(bundle)

    prompt = (
        "You are editing the source of a Next.js (App Router, TypeScript, Tailwind) "
        "small-business demo website. Below are its content files, each preceded by "
        "'--- FILE: <path> ---'. Apply the requested change.\n\n"
        "Named colors (blue, navy, ink, base, grey-line, grey-section, etc.) used in "
        "className strings like 'text-blue' or 'bg-navy' are defined as hex values in "
        "tailwind.config.ts, NOT arbitrary Tailwind classes. If asked to change a color, "
        "edit the hex value for that name in tailwind.config.ts instead of inventing a new "
        "utility class name (e.g. 'bg-teal') that has no definition and would render as nothing. "
        "Only introduce a new class name if you also add its definition to tailwind.config.ts.\n\n"
        "Every icon component used anywhere (e.g. <PhoneIcon />, <StarIcon />) must be one that "
        "is actually exported from src/components/icons.tsx, shown below. Importing or using an "
        "icon name that doesn't exist there crashes the page at runtime ('Element type is "
        "invalid... got: undefined'). If you need an icon that isn't already defined, ADD a new "
        "exported function to icons.tsx (copy the style of the existing ones: an SVG wrapped in "
        "the shared `base(props)` helper) rather than referencing a name that doesn't exist. "
        "If the instruction asks to add or replace an icon (e.g. 'add a house icon', 'replace "
        "with a phone icon'), prefer importing the matching icon component from 'lucide-react' "
        "(already an approved dependency, e.g. `import { Home } from 'lucide-react'`) instead of "
        "hand-drawing a new inline SVG path in icons.tsx — lucide-react has a real, correct icon "
        "for almost any request, and a hand-drawn path is much more likely to render as a broken "
        "or malformed shape. Only add a custom SVG to icons.tsx if no reasonable lucide-react icon "
        "matches what was asked for. When you use a lucide-react icon, set its color via a "
        "className like `text-blue` (or whatever the site's accent color token is) so it matches "
        "the rest of the site rather than defaulting to black or an unrelated color.\n\n"
        "When a 21st.dev component is injected, do NOT rewrite or recreate it. Inject the raw "
        "component code exactly as received. Only adapt its className values to match the site's "
        "existing Tailwind color tokens (e.g. replace hardcoded hex colors with the named token "
        "like 'text-blue' or 'bg-navy').\n\n"
        "You MAY create a brand-new file (e.g. splitting a section into its own "
        "src/components/SomeName.tsx) if that's the cleanest way to do the change — just make "
        "sure you also include and fully write that new file in your response, not only the file "
        "that imports it. An import with no corresponding file breaks the build "
        "('Module not found'). New files must be under src/components/.\n\n"
        "Some components (e.g. Reviews.tsx) are async Server Components that `await` server-side "
        "data (like `getGoogleReviews()`) — they have NO 'use client' directive. A Client Component "
        "(one marked 'use client') CANNOT be async/use await; adding 'use client' to one of these "
        "breaks the page with a blank render and a 'component was suspended by an uncached promise' "
        "error. If you want to add framer-motion animation to such a component's content, do NOT "
        "add 'use client' to the async component itself — instead wrap just the relevant JSX in an "
        "already-client child component (see src/components/motion/FadeUp.tsx's exported "
        "`StaggerGrid`/`StaggerItem`/`FadeUp` helpers, already used this way elsewhere) and keep the "
        "outer async function a plain Server Component.\n\n"
        "Do NOT import any npm package that isn't already used in the files shown below "
        "(framer-motion, motion, lucide-react, maplibre-gl, clsx, tailwind-merge, class-variance-"
        "authority, react, next). Importing a package that isn't installed (e.g. 'gsap', "
        "'swiper', 'react-icons') breaks the build with 'Module not found' — there is no install "
        "step after your edit runs. Build any new interaction/animation using only these already-"
        "available packages, or plain CSS/Tailwind.\n\n"
        "IMPORTANT — when a reference design's distinctive visual effect depends on a blocked "
        "package (e.g. a WebGL/shader library like '@paper-design/shaders-react', a carousel "
        "library, gsap), do NOT respond by just deleting that effect and rendering a plain flat "
        "fallback (a solid-color box where there was a shader panel is a FAILURE, not a safe "
        "simplification — it throws away the actual visual character you were asked to recreate). "
        "Instead, approximate the same visual character using only CSS/Tailwind/SVG/already-"
        "approved packages: a glass/shader panel can be approximated with `backdrop-blur` + "
        "layered semi-transparent gradients + a subtle noise/grain texture; distorted/fluted "
        "glass can be approximated with an inline SVG `<filter>` using `feTurbulence` + "
        "`feDisplacementMap` (no package needed, just raw SVG markup); a moving shader background "
        "can be approximated with an animated CSS gradient (framer-motion or CSS `@keyframes` on "
        "background-position/transform). The goal is always to preserve what makes the reference "
        "visually distinctive, not to find the path of least resistance to a build that compiles.\n\n"
        "Visual quality is not optional — a change that compiles but looks broken has failed. "
        "Before finalizing, check every file you touch against these:\n"
        "- No large empty whitespace gaps: sections should have consistent, deliberate padding "
        "(look at how other sections on this page space themselves — mt-14/py-24/px-6 etc. — and "
        "match that rhythm, don't leave a section half-empty or oddly tall).\n"
        "- No overlapping text or elements: if you use absolute/fixed positioning, verify the "
        "surrounding container actually has enough height/width for it, and that nothing else in "
        "that space collides with it. A stacked-card or carousel effect needs its container sized "
        "to fit the stack, not left to guess.\n"
        "- Respect the page's existing max-width container pattern (max-w-content, mx-auto) — "
        "don't let new content sit misaligned, off-center, or floating disconnected from the "
        "column other sections use.\n"
        "- Match existing typography and color usage (text-navy, text-blue, font sizes already in "
        "use) rather than introducing a visually inconsistent new style.\n"
        "- Text must be readable against its ACTUAL background, not just the background you "
        "wrote in isolation. Two cases that break this constantly:\n"
        "  (a) If you change a section's background to something dark (bg-navy, bg-ink, etc.), "
        "any text inside it must be a light color (text-white, text-navy/-ish light variants) — "
        "check every text className in that section, don't leave text-navy or another dark color "
        "sitting on a dark background you just introduced (invisible dark-on-dark text).\n"
        "  (b) Nav.tsx renders fixed/transparent on top of whatever section is at the top of the "
        "page (usually Hero) before the user scrolls — its own text/logo color (see Nav.tsx below) "
        "assumes it's sitting over a specific background. If you change Hero's background color or "
        "darkness, you MUST also check Nav.tsx's text color still has real contrast against the "
        "new Hero background, and adjust Nav.tsx if it doesn't — do this automatically as part of "
        "the same edit, don't leave it for the user to notice and ask again separately.\n"
        "  (c) This is a general rule, not just a Hero/Nav special case: for every element you add "
        "or restyle, look at the actual background color it will sit on (its own bg-* class, or "
        "the nearest ancestor's if it has none) and pick a text color with real contrast against "
        "it — roughly, dark backgrounds (navy, ink, black, dark accent colors) need light text "
        "(white or a light tint), and light backgrounds (base, white, light grey) need dark text "
        "(navy/ink). Never leave a same-tone-on-same-tone pairing (dark text on a dark bg you just "
        "set, or light text on a light bg you just set).\n"
        "If you're not confident a layout will render cleanly, prefer a simpler, more "
        "conservative implementation over a fragile one.\n\n"
        + (
            "An image is attached as a literal layout reference. If it shows colour-coded boxes "
            "or a wireframe, treat each region as a real section of the page: match its relative "
            "position, size and proportions in the actual layout. The requested-change text below "
            "explains what each colour/box is meant to contain — follow that mapping exactly "
            "rather than guessing from the image alone.\n\n"
            if layout_image else ""
        )
        + f"Requested change: {instruction}\n\n"
        "Respond with ONLY a JSON array (no markdown fences, no commentary) of objects "
        '{"path": "<path, existing or new under src/components/>", "content": "<full new file content>"} '
        "for every file you changed OR created. Do not include unchanged files. Preserve all "
        "other code, imports and structure exactly except for what the instruction asks for.\n\n"
        f"{bundle_text}"
    )

    content_blocks = []
    if layout_image:
        content_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": layout_image_media_type or "image/png",
                "data": layout_image,
            },
        })
    content_blocks.append({"type": "text", "text": prompt})

    try:
        message = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": content_blocks}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        ).strip()
        truncated = message.stop_reason == "max_tokens"
    except Exception as exc:
        return None, str(exc)

    changed_files = extract_json_array(text)
    if changed_files is None:
        if truncated:
            return None, ("Claude's response was cut off (too many files changed at once). "
                           "Try a more targeted edit, e.g. one section at a time.")
        return None, "Claude returned invalid JSON"

    written = []
    for item in changed_files:
        rel = item.get("path", "")
        content = item.get("content")
        if content is None:
            continue
        if rel not in CONTENT_FILES and not is_safe_new_component_path(rel):
            continue
        target = site_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel)

    if not written:
        return None, "Claude did not return any file changes"

    # The edited files were just written to disk, but Next.js dev's on-demand
    # compiler hasn't necessarily rebuilt the page yet — it invalidates the
    # old chunk on file-change and rebuilds lazily on the next request. If we
    # tell the frontend "done" now, its immediate forced iframe reload can
    # land in that gap and hit a ChunkLoadError ("missing app/page.js") for a
    # chunk that's been invalidated but not yet regenerated. Wait for a real
    # compiled response before reporting success, so the reload lands clean.
    slug = site_dir.name
    preview = RUNNING_PREVIEWS.get(slug)
    if preview:
        wait_for_preview_ready(preview["port"], timeout=60)

    return written, None


@app.route("/api/pipeline/edit_site", methods=["POST"])
def api_edit_site():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    instruction = (data.get("instruction") or "").strip()
    image = data.get("image")  # optional base64 layout reference (no data: prefix)
    image_media_type = data.get("image_media_type") or "image/png"
    if not instruction:
        return jsonify({"error": "instruction is required"}), 400

    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not found"}), 404

    written, error = apply_edit_instruction(site_dir, instruction, image, image_media_type)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"ok": True, "changed_files": written})


TWENTYFIRST_MCP_URL = "https://21st.dev/api/mcp"


def call_21st_mcp_tool(tool_name, arguments):
    """Call a tool on 21st.dev's real MCP server (verified live against the
    actual account: tools are `search` / `get_component`, not a plain REST
    API — this speaks the MCP protocol over streamable HTTP)."""
    import httpx2
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async def _call():
        client = httpx2.AsyncClient(headers={"x-api-key": TWENTYFIRST_API_KEY}, timeout=30)
        async with streamable_http_client(TWENTYFIRST_MCP_URL, http_client=client) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                text = "\n".join(getattr(c, "text", "") or str(c) for c in result.content)
                return text, bool(getattr(result, "isError", False))

    return asyncio.run(_call())


def parse_21st_search_results(text):
    """Parse the markdown-formatted text `search` returns into structured
    {id, name, description, thumbnail, author} dicts. Verified against real
    output: each result looks like:
        ### [component] Name  [id: 1234]
        by author
        optional description line(s)
        preview: https://...
        install: npx shadcn@latest add "..."
        → get the code: get_component({ id: 1234 })
    """
    results = []
    for block in re.split(r"\n(?=### )", text):
        block = block.strip()
        if not block.startswith("###"):
            continue
        header = re.match(r"###\s*\[(\w+)\]\s*(.+?)\s*\[id:\s*(\d+)\]", block)
        if not header:
            continue
        _entry_type, name, comp_id = header.groups()
        preview = re.search(r"preview:\s*(\S+)", block)
        author = re.search(r"\[id:\s*\d+\]\s*\nby ([^\n]+)", block)
        desc = re.search(r"\[id:\s*\d+\]\s*\nby [^\n]+\n(.*?)(?:\npreview:|\Z)", block, re.DOTALL)
        results.append({
            "id": int(comp_id),
            "name": name.strip(),
            "description": (desc.group(1).strip() if desc else ""),
            "thumbnail": preview.group(1) if preview else "",
            "author": (author.group(1).strip() if author else ""),
        })
    return results


def extract_component_code(text):
    match = re.search(r"```(?:tsx|jsx|ts|js)?\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else text


SECTION_FILE_HINTS = [
    (("hero",), "Hero.tsx"),
    (("about",), "About.tsx"),
    (("service",), "Services.tsx"),
    (("review", "testimonial"), "Reviews.tsx"),
    (("footer",), "Footer.tsx"),
    (("contact", "form"), "Contact.tsx"),
    (("nav", "header", "menu"), "Nav.tsx"),
    (("process", "step", "how it works"), "Process.tsx"),
    (("trust", "badge", "certif"), "TrustBar.tsx"),
]


def guess_section_file(section_text):
    """Map a free-text section hint (e.g. "about section", from the search
    query) to the actual component file it almost certainly refers to, so
    the edit instruction can name the exact file instead of leaving Claude
    to infer it — that ambiguity is what let it "integrate" a component by
    just animating the untouched original section instead of replacing it."""
    text = (section_text or "").lower()
    for keywords, filename in SECTION_FILE_HINTS:
        if any(kw in text for kw in keywords):
            return filename
    return None


@app.route("/api/pipeline/component_search", methods=["POST"])
def api_component_search():
    if not TWENTYFIRST_API_KEY:
        return jsonify({"error": "TWENTYFIRST_API_KEY not configured"}), 500

    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400
    try:
        limit = int(data.get("limit") or 10)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, 30))  # 30 is the MCP search tool's own hard max

    try:
        text, is_error = call_21st_mcp_tool("search", {"query": query, "type": "component", "limit": limit})
    except Exception as exc:
        return jsonify({"error": f"Could not reach 21st.dev MCP server: {exc}"}), 502
    if is_error:
        return jsonify({"error": f"21st.dev search failed: {text[:500]}"}), 502

    return jsonify({"results": parse_21st_search_results(text)})


@app.route("/api/pipeline/component_apply", methods=["POST"])
def api_component_apply():
    if not TWENTYFIRST_API_KEY:
        return jsonify({"error": "TWENTYFIRST_API_KEY not configured"}), 500

    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    component_id = data.get("component_id")
    section = (data.get("section") or "the most appropriate section").strip()
    if not component_id:
        return jsonify({"error": "component_id is required"}), 400

    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not found"}), 404

    try:
        text, is_error = call_21st_mcp_tool("get_component", {"id": int(component_id)})
    except Exception as exc:
        return jsonify({"error": f"Could not reach 21st.dev MCP server: {exc}"}), 502
    if is_error:
        return jsonify({"error": f"Could not fetch component: {text[:500]}"}), 502

    code = extract_component_code(text)
    target_file = guess_section_file(section)
    target_hint = (
        f"This corresponds to src/components/{target_file}, shown among the files below. "
        f"You MUST rewrite that file's JSX — replace its current return()/content with a new "
        f"implementation based on the component below. Do not leave the old headline, paragraph "
        f"text, or layout in place.\n\n"
        if target_file else
        "This doesn't correspond to one single existing named section (hero/about/services/etc.) "
        "— it's a page-level or multi-section effect (e.g. a scroll-choreographed 'story' layout, "
        "a full-page transition system). You have full authority over page.tsx AND every "
        "component file shown below to make this actually work: reorder sections, merge or split "
        "them, remove ones that don't fit, or write new ones — this is not limited to editing one "
        "file. Two failure modes to avoid, in opposite directions:\n"
        "- Too basic: don't just import the component and wrap the page's UNCHANGED sections in "
        "it as a thin shell (e.g. every existing section as-is, each just wrapped in a generic "
        "sticky/rotate/fade container). That reproduces none of the reference's actual character "
        "and looks like a broken generic effect slapped over the real site.\n"
        "- Too destructive: don't mechanically force literally every existing section (Hero, "
        "Services, About, Process, Reviews, Contact, Footer) through the same heavy scroll "
        "choreography just because the component technically CAN wrap N children. For a normal "
        "local trade business site, forcing 6-7 long, text-heavy sections into e.g. a full-height "
        "sticky-and-rotate stack makes the page enormous, disorienting to scroll, and breaks the "
        "site's internal nav anchors (#services, #about, #contact, etc. must still land on "
        "visible, normally-readable content).\n"
        "Instead, actually assess this page's specific sections and decide, section by section, "
        "which ones the reference effect genuinely suits (usually a small number — a hero moment, "
        "or 2-4 short highlight panels with a single headline/stat/image each) versus which ones "
        "should stay in a normal flowing layout untouched by the effect (long-form content like "
        "detailed service lists, testimonials, contact forms, footers rarely suit heavy scroll "
        "choreography). State that split by how you structure the JSX, not by leaving a comment. "
        "Faithfully rebuild the reference's actual visual mechanic (its real transforms, layering, "
        "timing) for the sections you do apply it to, rather than a watered-down approximation. "
        "Don't blanket-apply a fixed `min-h-screen` (or similar forced full-viewport height) to "
        "every wrapped section regardless of how much content it actually has — a short section "
        "(e.g. a trust-badge row) forced to full screen height leaves a large dead empty gap "
        "before the next section. Size each wrapped section to fit its real content (or the "
        "minimum height the transform mechanic itself needs to read correctly), not a blanket "
        "screen-height rule.\n\n"
    )
    instruction = (
        f"Fully replace {section} of this site with the component below.\n\n"
        f"{target_hint}"
        "This is a REPLACEMENT, not a decorative addition. A common mistake is to keep the "
        "section's existing text/layout completely unchanged and just wrap it in a fade-in "
        "animation — that is a FAILURE of this task, because visually nothing looks different "
        "and the fetched component never actually shows up. The end result must visibly look "
        "like a different section design, using the fetched component's actual structure "
        "(its layout, its elements, its arrangement), not the old section with an effect layered "
        "on top.\n\n"
        "Requirements:\n"
        "1. Adapt colors/fonts/spacing to the site's existing design tokens (tailwind.config.ts) "
        "instead of pasting it in with a visually mismatched look.\n"
        "2. Strip out or replace EVERY piece of placeholder content that doesn't belong on a real "
        "local trade business's site — generic tech-company logos (Nvidia, GitHub, Nike, etc.), "
        "placeholder lorem-ipsum text, fake testimonials, unrelated stock imagery. If the "
        "component includes a 'trusted by' logo row, either remove it entirely or replace it with "
        "something that actually fits this business (e.g. certifications already used elsewhere "
        "on the site) — never leave unrelated brand logos in the final result.\n"
        "3. Make sure the whole section is coherent afterward, not just one button or fragment "
        "bolted onto the old content — if you touch a section, finish integrating it completely.\n"
        "4. The npm-package rule below applies even if a file you're editing ALREADY imports "
        "something unauthorized (e.g. a previous bad edit added 'gsap') — that's leftover from a "
        "past mistake, not permission to keep using it. Remove that import and rebuild any "
        "animation using framer-motion/motion instead. It ALSO applies even if the COMPONENT "
        "SOURCE below (the fetched reference material itself) imports gsap, ScrollTrigger, "
        "@gsap/react, swiper, or any other package not in the whitelist — that source is "
        "reference material for the *visual result*, not code you may copy verbatim. Reimplement "
        "any scroll-triggered/entrance animation it does using framer-motion's `whileInView` / "
        "`useScroll` / `useTransform` hooks (already used elsewhere in this codebase, e.g. "
        "About.tsx's whileInView pattern) instead of the gsap APIs the source uses. Do not create "
        "a new file that imports gsap just because the reference component was structured that "
        "way.\n"
        "5. Preserve the fetched component's actual JSX structure as closely as possible — its "
        "element hierarchy, nesting, ordering, and layout mechanics (flex/grid structure, the "
        "number and arrangement of columns/panels/cards, which pieces of content sit next to "
        "which). Copy its structure first, then adapt only what MUST change to compile and fit "
        "this business:\n"
        "   a) className tokens: swap only the specific color/utility classes that don't exist in "
        "this project's tailwind.config.ts for the closest equivalent token here — don't restyle "
        "beyond that.\n"
        "   b) unavailable imports: if the source imports a component library that isn't part of "
        "this project (shadcn/ui primitives like '@/components/ui/button', radix-ui primitives, "
        "or any package outside the whitelist above), reimplement that specific primitive inline "
        "with plain JSX/Tailwind so the surrounding structure is unchanged — don't redesign the "
        "layout around its absence.\n"
        "   c) placeholder content: swap in this business's real content per requirement 2 above.\n"
        "Do NOT simplify, flatten, merge, or drop sections of the source's structure beyond what "
        "(a)-(c) require, and do not invent a materially different layout 'inspired by' the "
        "source — the fetched code is the actual design to reproduce, not a mood board.\n\n"
        f"--- COMPONENT SOURCE (reproduce this structure faithfully; the raw code as given, "
        f"substituting only per requirement 5) ---\n{code}"
    )
    written, error = apply_edit_instruction(site_dir, instruction)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"ok": True, "changed_files": written})


DEPLOY_IGNORE_DIRS = {"node_modules", ".next", ".git", ".vercel"}
DEPLOY_IGNORE_FILES = {"npm-install.log", "dev-server.log", ".devserver.json"}
DEPLOY_STATUS = {}  # slug -> {"stage": str, "detail": str, "done": bool, "error": str|None}


def collect_deploy_files(site_dir):
    """Source files to upload for a Vercel build — everything except the
    heavy/local-only stuff (node_modules, build output, our own bookkeeping
    files). Vercel builds from source remotely, same as the `vercel` CLI."""
    files = []
    for path in site_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(site_dir)
        if any(part in DEPLOY_IGNORE_DIRS for part in rel.parts):
            continue
        if rel.name in DEPLOY_IGNORE_FILES or rel.name.startswith(".stale-"):
            continue
        files.append((rel.as_posix(), path))
    return files


def deploy_via_vercel_api(slug, site_dir):
    """Deploy `site_dir` straight through Vercel's REST API (no `vercel`
    CLI/npx involved): upload source as base64, then poll until the build
    finishes. Updates DEPLOY_STATUS[slug] throughout for the modal to poll."""
    status = {"stage": "collecting", "detail": "Reading site files...", "done": False, "error": None}
    DEPLOY_STATUS[slug] = status

    try:
        file_list = collect_deploy_files(site_dir)
        status["stage"] = "uploading"
        status["detail"] = f"Uploading {len(file_list)} files..."

        files_payload = []
        for rel_path, abs_path in file_list:
            data_b64 = base64.b64encode(abs_path.read_bytes()).decode("ascii")
            files_payload.append({"file": rel_path, "data": data_b64, "encoding": "base64"})

        resp = requests.post(
            "https://api.vercel.com/v13/deployments",
            headers={"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"},
            json={
                "name": slug,
                "files": files_payload,
                "projectSettings": {"framework": "nextjs"},
                "target": "production",
            },
            timeout=120,
        )
        if resp.status_code >= 300:
            status["error"] = f"Vercel API rejected the deployment (HTTP {resp.status_code}): {resp.text[:500]}"
            status["done"] = True
            return

        deployment = resp.json()
        deployment_id = deployment.get("id") or deployment.get("uid")
        deploy_url = "https://" + deployment["url"] if deployment.get("url") else None

        status["stage"] = "building"
        status["detail"] = "Vercel is building the site..."

        deadline = time.time() + 300
        ready_state = deployment.get("readyState", "QUEUED")
        while time.time() < deadline and ready_state not in ("READY", "ERROR", "CANCELED"):
            time.sleep(3)
            poll = requests.get(
                f"https://api.vercel.com/v13/deployments/{deployment_id}",
                headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
                timeout=30,
            )
            poll.raise_for_status()
            poll_data = poll.json()
            ready_state = poll_data.get("readyState", ready_state)
            deploy_url = "https://" + poll_data["url"] if poll_data.get("url") else deploy_url
            status["detail"] = f"Vercel is building the site... ({ready_state.lower()})"

        if ready_state != "READY":
            status["error"] = f"Deployment did not become ready (status: {ready_state})."
            status["done"] = True
            return

        status["stage"] = "ready"
        status["detail"] = deploy_url
        status["done"] = True
        status["demo_url"] = deploy_url
    except requests.RequestException as exc:
        status["error"] = f"Network error talking to Vercel: {exc}"
        status["done"] = True
    except Exception as exc:  # noqa: BLE001 - background thread, must not crash silently
        status["error"] = f"Unexpected error during deploy: {exc}"
        status["done"] = True


@app.route("/api/pipeline/deploy", methods=["POST"])
def api_deploy():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    lead = find_lead(read_leads(), slug)
    if not lead:
        return jsonify({"error": "lead not found"}), 404

    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not built yet"}), 400
    if not VERCEL_TOKEN:
        return jsonify({"error": "VERCEL_TOKEN not configured", "manual_dir": str(site_dir)}), 500

    deploy_via_vercel_api(slug, site_dir)
    status = DEPLOY_STATUS.get(slug, {})

    if status.get("error"):
        # The local site is untouched either way — deploy failing never
        # deletes or modifies it, so a manual `vercel deploy` always works.
        return jsonify({"error": status["error"], "manual_dir": str(site_dir)}), 500

    deploy_url = status.get("demo_url")
    with leads_transaction() as leads:
        lead = find_lead(leads, slug)
        if lead and deploy_url:
            lead["demo_url"] = deploy_url
    return jsonify({"demo_url": deploy_url})


@app.route("/api/pipeline/deploy_status/<slug>", methods=["GET"])
def api_deploy_status(slug):
    return jsonify(DEPLOY_STATUS.get(slug, {"stage": "idle", "detail": "", "done": True, "error": None}))


def lead_reason(lead):
    """One concrete, specific fact about why this lead needs a site."""
    website = (lead.get("website") or "").lower()
    email = (lead.get("email") or "").lower()
    if not website:
        if any(h in email for h in FREE_EMAIL_HINTS):
            return f"no website at all, and running the business off a {email.split('@')[-1]} address"
        return "no website at all right now"
    if any(h in website for h in FREE_BUILDER_HINTS):
        return f"currently on a free builder site ({website})"
    if any(h in email for h in FREE_EMAIL_HINTS):
        return f"has an old-style site but still using a {email.split('@')[-1]} address"
    return "a site that could use an update"


def generate_email(lead):
    signoff_name = OPERATOR_NAME or "[Your name]"
    signoff_phone = OPERATOR_PHONE or "[Your number]"
    if not _client:
        return {
            "subject": f"a website for {lead.get('name', 'your business')}",
            "body": (
                f"Hi, I built a free demo site for {lead.get('name','your business')} — "
                f"{lead.get('demo_url','')}\n\nNo pressure, just thought it might help.\n\n"
                f"{signoff_name}\n{signoff_phone}"
            ),
        }

    reason = lead_reason(lead)
    prompt = (
        "Write a cold email offering a free demo website you already built for this "
        "business. Write it exactly like a young Irish person texting a local business "
        "owner, not writing a marketing email. Rules:\n"
        "- Under 80 words total, body included\n"
        "- Start with 'Hi' (never 'Dear')\n"
        "- Mention this one specific, true thing about their business naturally: "
        f"{reason}\n"
        "- Include the demo link naturally in a sentence, not on its own line\n"
        f"- End with the sender's name and phone number on their own lines: "
        f"{signoff_name} / {signoff_phone}\n"
        "- No corporate or marketing language. Banned words/phrases: 'resonates', "
        "'leverage', 'leaving money on the table', 'digital presence', 'reach out', "
        "'circle back', 'synergy', 'game-changer', 'take your business to the next "
        "level', 'unlock', 'elevate'\n"
        "- No exclamation marks, no bullet points, no formal sign-off like 'Kind regards'\n\n"
        "Return strictly in this format:\nSUBJECT: <subject line>\nBODY:\n<email body>\n\n"
        f"Business name: {lead.get('name')}\n"
        f"Lead score (10=urgent need, no site at all): {lead.get('score')}\n"
        f"Demo URL: {lead.get('demo_url')}\n"
    )
    try:
        message = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        ).strip()
        subject_match = re.search(r"SUBJECT:\s*(.+)", text)
        body_match = re.search(r"BODY:\s*(.*)", text, re.DOTALL)
        subject = subject_match.group(1).strip() if subject_match else f"A free demo site for {lead.get('name')}"
        body = body_match.group(1).strip() if body_match else text
        return {"subject": subject, "body": body}
    except Exception:
        return {
            "subject": f"a website for {lead.get('name', 'your business')}",
            "body": (
                f"Hi, I built a free demo site for {lead.get('name','your business')} — "
                f"{lead.get('demo_url','')}\n\nNo pressure, just thought it might help.\n\n"
                f"{signoff_name}\n{signoff_phone}"
            ),
        }


@app.route("/api/emails", methods=["GET"])
def api_emails():
    leads = read_leads()
    pending = [l for l in leads if l.get("demo_built") == "Yes" and l.get("email_sent") != "Yes"]
    for lead in pending:
        preview = generate_email(lead)
        lead["email_subject"] = preview["subject"]
        lead["email_body"] = preview["body"]
    return jsonify({"leads": pending})


@app.route("/api/emails/mark_sent", methods=["POST"])
def api_mark_sent():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    with leads_transaction() as leads:
        lead = find_lead(leads, slug)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        lead["email_sent"] = "Yes"
    return jsonify({"lead": lead})


@app.route("/api/pipeline/update_status", methods=["POST"])
def api_update_status():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    field = data.get("field")
    value = data.get("value")
    if field not in {"replied", "sold", "email_sent", "demo_built"}:
        return jsonify({"error": "invalid field"}), 400
    with leads_transaction() as leads:
        lead = find_lead(leads, slug)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        lead[field] = value
    return jsonify({"lead": lead})


def open_browser():
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    ensure_db()
    SITES_DIR.mkdir(exist_ok=True)
    print("SiteForge running at localhost:5000")
    Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
