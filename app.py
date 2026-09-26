"""SiteForge v0.1 - local lead-gen / demo-site / outreach tool."""
import asyncio
import atexit
import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import uuid
import webbrowser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from difflib import SequenceMatcher
from pathlib import Path
from threading import Timer
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
LEADS_CSV = BASE_DIR / "leads.csv"  # legacy file, only read once for migration
LEADS_DB = BASE_DIR / "leads.db"
SITES_DIR = BASE_DIR / "sites"
TEMPLATE_SITE = SITES_DIR / "derek-doyle-electrical"

CSV_FIELDS = [
    "name", "phone", "email", "website", "location", "score", "years",
    "slug", "demo_built", "demo_url", "email_sent", "replied", "sold",
    "accent", "font", "radius",  # saved theme, re-applied on rebuild
    # From the Google Places search + enrichment:
    "place_id", "logo_path", "brand_colors", "rating", "review_count", "maps_url",
    "town", "county", "use_logo",
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
        # CREATE TABLE IF NOT EXISTS won't add columns to an existing table,
        # so add any field that's newer than the database.
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(leads)")}
        for f in CSV_FIELDS:
            if f not in existing_cols:
                conn.execute(f'ALTER TABLE leads ADD COLUMN "{f}" TEXT NOT NULL DEFAULT \'\'')
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


# ---------------------------------------------------------------------------
# Version history — a lightweight snapshot before every AI/manual edit, so
# any change (hotbar instruction, 21st.dev component add, etc.) can be
# undone. Only ever copies the specific things an edit can touch (src/,
# tailwind.config.ts, sections.json) — never node_modules, .next, or
# .history itself, since those aren't part of any snapshot's source paths.
# ---------------------------------------------------------------------------

HISTORY_DIRNAME = ".history"
MAX_SNAPSHOTS = 25
SNAPSHOT_PATHS = ["src", "tailwind.config.ts", "sections.json"]
_SNAPSHOT_TS_RE = re.compile(r"^\d{8}T\d{9}Z$")


def _new_snapshot_timestamp():
    return time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + f"{int((time.time() % 1) * 1000):03d}Z"


def snapshot_site(site_dir, label, source):
    """Copy the current src/, tailwind.config.ts and sections.json (if
    present) into sites/[slug]/.history/[timestamp]/, with a meta.json
    describing the snapshot. Best-effort: a snapshot failure must never
    block the edit it's guarding, so filesystem errors are swallowed."""
    try:
        timestamp = _new_snapshot_timestamp()
        snap_dir = site_dir / HISTORY_DIRNAME / timestamp
        snap_dir.mkdir(parents=True, exist_ok=True)
        for rel in SNAPSHOT_PATHS:
            src_path = site_dir / rel
            if not src_path.exists():
                continue
            dest_path = snap_dir / rel
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
        (snap_dir / "meta.json").write_text(
            json.dumps({"timestamp": timestamp, "label": (label or "")[:200], "source": source}),
            encoding="utf-8",
        )
        _prune_snapshots(site_dir)
        return timestamp
    except OSError:
        return None


def _prune_snapshots(site_dir):
    history_dir = site_dir / HISTORY_DIRNAME
    if not history_dir.exists():
        return
    snapshots = sorted((p for p in history_dir.iterdir() if p.is_dir()), key=lambda p: p.name)
    excess = len(snapshots) - MAX_SNAPSHOTS
    for old in snapshots[:max(excess, 0)]:
        rmtree_retry(old, attempts=3, delay=0.5)


def list_snapshots(site_dir):
    history_dir = site_dir / HISTORY_DIRNAME
    if not history_dir.exists():
        return []
    snapshots = []
    for snap_dir in history_dir.iterdir():
        if not snap_dir.is_dir():
            continue
        meta_path = snap_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        snapshots.append(meta)
    snapshots.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    return snapshots


def _sync_dir_exact(snap_dir, live_dir):
    """Make live_dir's contents exactly match snap_dir's by writing/deleting
    individual files in place — NOT by removing and recreating live_dir.

    Next.js dev's file watcher can lose track of a directory that gets
    swapped out and back in (confirmed live: it kept 404ing on '/' after a
    rename+recreate here, compiling '/_not-found' instead and never
    recovering without a manual dev-server restart). Every other edit path
    in this app already writes files in place one at a time and that's
    proven to trigger a clean recompile via wait_for_preview_ready, so
    restore follows the same shape instead of a directory-level swap.
    """
    snap_files = {}
    if snap_dir.exists():
        for p in snap_dir.rglob("*"):
            if p.is_file():
                snap_files[p.relative_to(snap_dir)] = p

    live_files = set()
    if live_dir.exists():
        for p in live_dir.rglob("*"):
            if p.is_file():
                live_files.add(p.relative_to(live_dir))

    for rel, src_path in snap_files.items():
        dest_path = live_dir / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)

    for rel in live_files - set(snap_files.keys()):
        try:
            (live_dir / rel).unlink()
        except OSError:
            pass

    if live_dir.exists():
        leftover_dirs = sorted(
            (p for p in live_dir.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts), reverse=True,
        )
        for d in leftover_dirs:
            try:
                d.rmdir()  # only succeeds if now empty
            except OSError:
                pass


def restore_snapshot(site_dir, timestamp):
    """Snapshot the current state (so restoring is itself undoable), then
    copy the chosen snapshot's files back over the live site. Returns
    (restored_label, error)."""
    if not _SNAPSHOT_TS_RE.match(timestamp or ""):
        return None, "invalid snapshot timestamp"
    snap_dir = site_dir / HISTORY_DIRNAME / timestamp
    meta_path = snap_dir / "meta.json"
    if not snap_dir.exists() or not meta_path.exists():
        return None, "snapshot not found"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "snapshot metadata is corrupt"

    snapshot_site(site_dir, "before restore", "restore")

    try:
        for rel in SNAPSHOT_PATHS:
            snap_path = snap_dir / rel
            live_path = site_dir / rel
            if rel == "src":
                _sync_dir_exact(snap_path, live_path)
            else:
                if snap_path.exists():
                    live_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(snap_path, live_path)
                elif live_path.exists():
                    live_path.unlink()
    except OSError as exc:
        return None, f"Could not restore snapshot: {exc}"

    slug = site_dir.name
    preview = RUNNING_PREVIEWS.get(slug)
    if preview:
        wait_for_preview_ready(preview["port"], timeout=60)

    return meta.get("label", ""), None


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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IE,en;q=0.9",
}


# ---------------------------------------------------------------------------
# Golden Pages — kept only as a fallback email source for leads that Google
# Places has no website for (see enrich_lead).
# ---------------------------------------------------------------------------

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


def fetch_results_page(session, what, where, page_num):
    """Fetch one page of goldenpages.ie business results (20 listings each),
    plus the "N results" total the page reports."""
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
        return [], None, f"Could not reach goldenpages.ie ({exc.__class__.__name__})."

    if resp.status_code in (429, 403):
        return [], None, "Rate limited by goldenpages.ie."
    try:
        resp.raise_for_status()
    except requests.RequestException:
        return [], None, f"goldenpages.ie returned an error (HTTP {resp.status_code})."

    total_count = None
    count_match = re.search(r"([\d,]+)\s+result", resp.text, re.I)
    if count_match:
        total_count = int(count_match.group(1).replace(",", ""))

    soup = BeautifulSoup(resp.text, "html.parser")
    parsed = []
    for card in soup.select(".listing_container"):
        title_el = card.select_one(".listing_title_link")
        if not title_el:
            continue
        name = re.sub(r"^\d+\.\s*", "", title_el.get_text(strip=True))  # strip "1." rank prefix
        if not name:
            continue
        phone_el = card.select_one(".link_listing_number")
        phone = phone_el.get("href", "").replace("tel:", "").strip() if phone_el else ""
        detail_link = card.select_one(".listing_base_link, .listing_title_link")
        detail_href = detail_link.get("href", "") if detail_link else ""
        parsed.append({
            "name": name,
            "phone": phone,
            "_detail_url": requests.compat.urljoin("https://www.goldenpages.ie/", detail_href) if detail_href else "",
        })
    return parsed, total_count, None


def _digits(text):
    return re.sub(r"\D", "", text or "")


def _norm_name(text):
    text = re.sub(r"\b(ltd|limited|t/a|the|electrical|services|contractors?)\b", " ", (text or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def goldenpages_email_for(lead):
    """Find this business's Golden Pages listing (same phone number, or a
    name similarity over 0.7) and return the email from its detail page."""
    session = requests.Session()
    where = lead.get("town") or lead.get("county") or ""
    results, _, error = fetch_results_page(session, lead.get("name", ""), where, 1)
    if error or not results:
        return ""
    phone_tail = _digits(lead.get("phone"))[-7:]
    target = _norm_name(lead.get("name"))
    match = None
    for r in results:
        if phone_tail and len(phone_tail) == 7 and _digits(r["phone"]).endswith(phone_tail):
            match = r
            break
        if match is None and SequenceMatcher(None, target, _norm_name(r["name"])).ratio() > 0.7:
            match = r
    if match and match.get("_detail_url"):
        return fetch_detail_email(session, match["_detail_url"])
    return ""


# ---------------------------------------------------------------------------
# Google Places API (New) search
# ---------------------------------------------------------------------------

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
# Kept minimal on purpose: every field in the mask is billed, and the
# phone/website fields push the call into a pricier tier.
PLACES_FIELD_MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.nationalPhoneNumber", "places.websiteUri", "places.rating",
    "places.userRatingCount", "places.location", "places.businessStatus",
    "places.googleMapsUri", "nextPageToken",
])
CACHE_TTL_SECONDS = 30 * 24 * 3600  # Google allows caching Places content for 30 days
PLACES_CACHE_DIR = BASE_DIR / "cache" / "places"
QUERY_CACHE_DIR = BASE_DIR / "cache" / "queries"
LOGOS_DIR = BASE_DIR / "static" / "logos"
COUNTIES = json.loads((BASE_DIR / "data" / "ireland_counties.json").read_text(encoding="utf-8"))
TRADE_PRESETS = ["Electrician", "Plumber", "Roofer", "Heating Engineer", "Painter", "Landscaper", "Builder"]
_PLACE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,300}$")


class PlacesError(Exception):
    pass


def _cache_read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - data.get("cached_at", 0) > CACHE_TTL_SECONDS:
        return None
    return data


def _cache_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def _place_cache_path(place_id):
    return PLACES_CACHE_DIR / f"{place_id}.json"


def _save_place(place):
    """Cache a place's search data, keeping any enrichment already stored."""
    path = _place_cache_path(place["id"])
    existing = _cache_read(path) or {}
    existing["place"] = place
    existing["cached_at"] = time.time()
    _cache_write(path, existing)


def places_text_search(text_query, center):
    """Every page (Google stops at ~60 results) for one query. A repeat of
    the same query within 30 days is served entirely from cache.
    Returns (places, api_calls)."""
    qkey = hashlib.sha1(text_query.lower().encode("utf-8")).hexdigest()
    cached = _cache_read(QUERY_CACHE_DIR / f"{qkey}.json")
    if cached:
        places = []
        for pid in cached["ids"]:
            entry = _cache_read(_place_cache_path(pid))
            if not entry:
                break
            places.append(entry["place"])
        else:
            return places, 0

    places, calls, token = [], 0, None
    for _ in range(3):
        body = {"textQuery": text_query, "regionCode": "IE", "pageSize": 20}
        if center:
            body["locationBias"] = {"circle": {
                "center": {"latitude": center[0], "longitude": center[1]}, "radius": 15000.0,
            }}
        if token:
            body["pageToken"] = token
        try:
            resp = requests.post(PLACES_SEARCH_URL, json=body, timeout=15, headers={
                "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY, "X-Goog-FieldMask": PLACES_FIELD_MASK,
            })
        except requests.RequestException as exc:
            raise PlacesError(f"Could not reach Google Places ({exc.__class__.__name__})")
        calls += 1
        data = resp.json() if resp.content else {}
        if resp.status_code != 200:
            message = (data.get("error") or {}).get("message") or f"HTTP {resp.status_code}"
            raise PlacesError(f"Google Places error: {message}")
        for place in data.get("places", []):
            places.append(place)
            _save_place(place)
        token = data.get("nextPageToken")
        if not token:
            break

    _cache_write(QUERY_CACHE_DIR / f"{qkey}.json",
                 {"query": text_query, "ids": [p["id"] for p in places], "cached_at": time.time()})
    return places, calls


_ALL_TOWNS = {t[0].lower(): t[0] for c in COUNTIES.values() for t in c["towns"]}
_NOT_A_TOWN_RE = re.compile(
    r"\b(park|estate|road|rd|street|business|centre|center|unit|industrial|lane|avenue|ave|"
    r"court|house|drive|way|square|place|close|grove|green|terrace)\b", re.I)


def _infer_town(address, county, fallback):
    """A known town in the address, else the segment just before "Co. X"
    (if it doesn't look like a street/estate/business park), else the town
    we searched."""
    parts = [p.strip() for p in (address or "").split(",")]
    for part in parts:
        if part.lower() in _ALL_TOWNS:
            return _ALL_TOWNS[part.lower()]
        if re.fullmatch(r"Dublin \d{1,2}[Ww]?", part):
            return part
    for i, part in enumerate(parts):
        if part.lower().startswith("co. ") and i > 0:
            candidate = parts[i - 1]
            if not _NOT_A_TOWN_RE.search(candidate) and not re.search(r"\d", candidate):
                return candidate
            break
    return fallback


def place_to_lead(place, county, town_hint):
    return {
        "place_id": place["id"],
        "name": (place.get("displayName") or {}).get("text", ""),
        "phone": place.get("nationalPhoneNumber", ""),
        "email": "",
        "website": place.get("websiteUri", ""),
        "location": place.get("formattedAddress", ""),
        "town": _infer_town(place.get("formattedAddress"), county, town_hint),
        "county": county,
        "rating": place.get("rating"),
        "review_count": place.get("userRatingCount") or 0,
        "maps_url": place.get("googleMapsUri", ""),
        "business_status": place.get("businessStatus", ""),
        "logo_path": "",
        "brand_colors": [],
        "quality": {},
        "enrich_status": "pending",
    }


# ---------------------------------------------------------------------------
# Enrichment — website email / logo / brand colours / quality signals, or a
# Golden Pages email for leads with no site. Runs in the background.
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ROLE_EMAIL_PREFIXES = ("info", "contact", "hello", "enquiries", "enquiry", "office", "admin", "sales", "bookings", "mail")
JUNK_EMAIL_HINTS = ("example.", "sentry", "wixpress", "domain.com", "email.com", "yourname", "yourdomain",
                    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "@2x", "godaddy", "schema.org")
HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
BRAND_VAR_RE = re.compile(r"--[\w-]*(?:brand|primary|accent)[\w-]*\s*:\s*(#[0-9a-fA-F]{3,6})\b", re.I)
COPYRIGHT_RE = re.compile(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", re.I)
CONSTRUCTION_RE = re.compile(r"under construction|coming soon|site is being (?:built|updated)", re.I)
BUILDER_SIGNATURES = {"wix": ("wix.com", "wixstatic.com"), "webador": ("webador",),
                      "godaddysites": ("godaddysites", "wsimg.com"), "weebly": ("weebly",)}
ENRICH_POOL = ThreadPoolExecutor(max_workers=6)


def _fetch_page(url, max_bytes=2_000_000):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True, stream=True)
        if resp.status_code >= 400:
            return None, None
        content = resp.raw.read(max_bytes, decode_content=True)
        encoding = resp.encoding or "utf-8"
        return content.decode(encoding, errors="ignore"), resp.url
    except (requests.RequestException, OSError):
        return None, None


def pick_email(candidates):
    seen, clean = set(), []
    for raw in candidates:
        email = raw.strip().strip(".").lower()
        if not EMAIL_RE.fullmatch(email) or any(h in email for h in JUNK_EMAIL_HINTS) or email in seen:
            continue
        seen.add(email)
        clean.append(email)
    for email in clean:
        if email.split("@")[0] in ROLE_EMAIL_PREFIXES:
            return email
    return clean[0] if clean else ""


def _hex_rgb(hex_):
    h = hex_.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _is_neutral(rgb):
    r, g, b = rgb
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return lum > 235 or lum < 22 or (max(rgb) - min(rgb)) < 28


# Site-builder UI colours that leak into every site built with them.
BUILDER_UI_COLORS = {"#116DFF", "#3899EC", "#0070F3"}


def _distinct_colors(hexes, limit=4):
    picked = []
    for hex_ in hexes:
        rgb = _hex_rgb(hex_)
        if _is_neutral(rgb) or "#{:02X}{:02X}{:02X}".format(*rgb) in BUILDER_UI_COLORS:
            continue
        if all(sum((a - b) ** 2 for a, b in zip(rgb, _hex_rgb(p))) ** 0.5 > 48 for p in picked):
            picked.append("#{:02X}{:02X}{:02X}".format(*rgb))
        if len(picked) == limit:
            break
    return picked


def logo_colors(img):
    """Dominant colours of a logo via quantize(8), ignoring transparent,
    near-white, near-black and low-saturation pixels."""
    rgba = img.convert("RGBA")
    rgba.thumbnail((128, 128))
    pixels = [p[:3] for p in rgba.getdata() if p[3] > 128 and not _is_neutral(p[:3])]
    if not pixels:
        return []
    flat = Image.new("RGB", (len(pixels), 1))
    flat.putdata(pixels)
    quant = flat.quantize(colors=8)
    palette = quant.getpalette()
    counts = sorted(quant.getcolors() or [], reverse=True)
    return ["#{:02X}{:02X}{:02X}".format(*palette[i * 3:i * 3 + 3]) for _, i in counts]


def find_logo_candidates(soup, base_url):
    touch, logo_imgs, og, icons = [], [], [], []
    for link in soup.find_all("link", href=True):
        rels = [r.lower() for r in (link.get("rel") or [])]
        if any(r.startswith("apple-touch-icon") for r in rels):
            touch.append(link["href"])
        elif "icon" in rels:
            icons.append(link["href"])
    for img in soup.find_all("img"):
        attrs = " ".join([img.get("src", ""), img.get("alt", ""), " ".join(img.get("class", [])), img.get("id", "")])
        if "logo" in attrs.lower():
            src = img.get("src") or img.get("data-src") or (img.get("srcset") or "").split(" ")[0]
            if src:
                logo_imgs.append(src)
    meta = soup.find("meta", property="og:image")
    if meta and meta.get("content"):
        og.append(meta["content"])
    urls = []
    for c in touch + logo_imgs + og + icons:
        if c and not c.startswith("data:"):
            urls.append(requests.compat.urljoin(base_url, c))
    return urls


def download_logo(candidates, place_id):
    """First candidate that's a real raster image (SVGs can't be read by
    Pillow) is saved as static/logos/<place_id>.png. Returns (url, image)."""
    for url in candidates:
        if urlparse(url).path.lower().endswith(".svg"):
            continue
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, stream=True)
            if resp.status_code >= 400:
                continue
            data = resp.raw.read(3_000_000, decode_content=True)
            img = Image.open(io.BytesIO(data))
            img.load()
        except (requests.RequestException, OSError, Image.DecompressionBombError):
            continue
        if min(img.size) < 16:
            continue
        img = img.convert("RGBA")
        img.thumbnail((256, 256))
        LOGOS_DIR.mkdir(parents=True, exist_ok=True)
        img.save(LOGOS_DIR / f"{place_id}.png", "PNG")
        return f"/static/logos/{place_id}.png", img
    return "", None


def analyse_site(website, place_id):
    """Fetch the homepage + /contact (8s timeout each) and pull email, logo,
    brand colours and site-quality signals."""
    home_html, final_url = _fetch_page(website)
    if home_html is None:
        return {"email": "", "logo_path": "", "brand_colors": [], "quality": {"reachable": False}}
    contact_html, _ = _fetch_page(requests.compat.urljoin(final_url, "/contact"))
    soup = BeautifulSoup(home_html, "html.parser")

    emails = []
    for html in (home_html, contact_html or ""):
        page = BeautifulSoup(html, "html.parser") if html is not home_html else soup
        emails += [a["href"][7:].split("?")[0] for a in page.select("a[href^='mailto:']")]
    email = pick_email(emails) or pick_email(EMAIL_RE.findall(home_html + " " + (contact_html or "")))

    logo_path, logo_img = download_logo(find_logo_candidates(soup, final_url), place_id)

    css_text = "\n".join(s.get_text() for s in soup.find_all("style"))
    css_text += "\n" + "\n".join(el.get("style", "") for el in soup.find_all(style=True))
    for link in [l for l in soup.find_all("link", href=True) if "stylesheet" in [r.lower() for r in (l.get("rel") or [])]][:2]:
        sheet, _ = _fetch_page(requests.compat.urljoin(final_url, link["href"]), max_bytes=1_000_000)
        css_text += "\n" + (sheet or "")
    theme = soup.find("meta", attrs={"name": "theme-color"})
    ordered = []
    if theme and HEX_COLOR_RE.fullmatch((theme.get("content") or "").strip()):
        ordered.append(theme["content"].strip())
    ordered += BRAND_VAR_RE.findall(css_text)
    if logo_img is not None:
        ordered += logo_colors(logo_img)
    ordered += [c for c, _ in Counter(h.upper() for h in HEX_COLOR_RE.findall(css_text)).most_common(20)]

    text = soup.get_text(" ", strip=True)
    years = [int(y) for y in COPYRIGHT_RE.findall(home_html) if 1995 <= int(y) <= time.gmtime().tm_year + 1]
    headline = " ".join(el.get_text(" ", strip=True) for el in soup.find_all(["title", "h1"]))
    haystack = (final_url + home_html[:200_000]).lower()
    quality = {
        "reachable": True,
        "https": final_url.startswith("https://"),
        "viewport": soup.find("meta", attrs={"name": "viewport"}) is not None,
        "copyright_year": max(years) if years else None,
        "builder": next((name for name, sigs in BUILDER_SIGNATURES.items() if any(s in haystack for s in sigs)), None),
        "under_construction": bool(CONSTRUCTION_RE.search(headline) or (len(text) < 800 and CONSTRUCTION_RE.search(text))),
    }
    return {"email": email, "logo_path": logo_path, "brand_colors": _distinct_colors(ordered), "quality": quality}


def score_place_lead(lead):
    """10 no site + email · 9 no site, phone only · 8 free builder or under
    construction · 7 copyright before 2020 or no viewport meta · 5 current
    site · 0 closed, or custom-domain email with a modern site."""
    if lead.get("business_status") and lead["business_status"] != "OPERATIONAL":
        return 0
    email = (lead.get("email") or "").lower()
    if not lead.get("website"):
        return 10 if email else 9
    q = lead.get("quality") or {}
    if not q.get("reachable", True):
        return 5  # couldn't load it — don't guess either way
    if q.get("builder") or q.get("under_construction"):
        return 8
    outdated = (q.get("copyright_year") and q["copyright_year"] < 2020) or q.get("viewport") is False
    if outdated:
        return 7
    site_host = (urlparse(lead["website"]).hostname or "").lower().removeprefix("www.")
    email_domain = email.split("@")[-1] if "@" in email else ""
    if email_domain and site_host and email_domain.endswith(site_host) and q.get("https"):
        return 0
    return 5


def enrich_lead(lead):
    """Returns the fields to merge into a lead. Results are cached with the
    place for 30 days, so re-running a search doesn't re-scrape anything."""
    path = _place_cache_path(lead["place_id"])
    entry = _cache_read(path) or {"place": {}, "cached_at": time.time()}
    cached = entry.get("enrichment")
    if cached and time.time() - cached.get("enriched_at", 0) < CACHE_TTL_SECONDS:
        result = dict(cached)
    else:
        if lead.get("website"):
            result = analyse_site(lead["website"], lead["place_id"])
        else:
            result = {"email": goldenpages_email_for(lead), "logo_path": "", "brand_colors": [], "quality": {}}
        result["enriched_at"] = time.time()
        entry["enrichment"] = result
        _cache_write(path, entry)
    result.pop("enriched_at", None)
    result["brand_colors"] = _distinct_colors(result.get("brand_colors") or [])
    if result.get("logo_path") and not (LOGOS_DIR / f"{lead['place_id']}.png").exists():
        result["logo_path"] = ""
    merged = {**lead, **result}
    result["score"] = score_place_lead(merged)
    result["enrich_status"] = "done"
    return result


# ---------------------------------------------------------------------------
# Search jobs: results return immediately, enrichment streams in via polling
# ---------------------------------------------------------------------------

SEARCH_JOBS = {}  # job_id -> {"leads": {place_id: lead}, "total", "done", "created"}
_jobs_lock = threading.Lock()


def _prune_jobs():
    cutoff = time.time() - 3600
    for job_id in [j for j, job in SEARCH_JOBS.items() if job["created"] < cutoff]:
        SEARCH_JOBS.pop(job_id, None)


def _pipeline_index():
    leads = read_leads()
    return {l["place_id"] for l in leads if l.get("place_id")}, {l["slug"] for l in leads}


def _run_enrichment(job_id, place_id):
    with _jobs_lock:
        job = SEARCH_JOBS.get(job_id)
        lead = dict(job["leads"][place_id]) if job else None
    if lead is None:
        return
    try:
        updates = enrich_lead(lead)
    except Exception as exc:  # noqa: BLE001 - one bad site must not stall the rest
        print(f"[enrich] {lead.get('name')}: {exc}", flush=True)
        updates = {"enrich_status": "failed", "score": score_place_lead(lead)}
    with _jobs_lock:
        job = SEARCH_JOBS.get(job_id)
        if job:
            job["leads"][place_id].update(updates)
            job["done"] += 1
    _sync_enrichment_to_pipeline(place_id, updates)


def _sync_enrichment_to_pipeline(place_id, updates):
    """If this lead was added to the pipeline before enrichment finished,
    fill in what we found (never overwriting anything already there)."""
    if not any(updates.get(k) for k in ("email", "logo_path", "brand_colors")):
        return
    with leads_transaction() as leads:
        lead = next((l for l in leads if l.get("place_id") == place_id), None)
        if not lead:
            return
        if updates.get("email") and not lead.get("email"):
            lead["email"] = updates["email"]
        if updates.get("logo_path") and not lead.get("logo_path"):
            lead["logo_path"] = updates["logo_path"]
            if not lead.get("use_logo"):
                lead["use_logo"] = "Yes"
        if updates.get("brand_colors") and not lead.get("brand_colors"):
            lead["brand_colors"] = ",".join(updates["brand_colors"])
        if "score" in updates:
            lead["score"] = str(updates["score"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/regions", methods=["GET"])
def api_regions():
    return jsonify({
        "trades": TRADE_PRESETS,
        "provinces": ["Leinster", "Munster", "Connacht", "Ulster"],
        "counties": {name: {"province": c["province"], "towns": [t[0] for t in c["towns"]]}
                     for name, c in sorted(COUNTIES.items())},
    })


@app.route("/api/search", methods=["POST"])
def api_search():
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "GOOGLE_MAPS_API_KEY is not set in .env"}), 500
    data = request.get_json(force=True) or {}
    trade = (data.get("trade") or "").strip()
    counties = [c for c in (data.get("counties") or []) if c in COUNTIES]
    town = (data.get("town") or "").strip()
    no_website_only = bool(data.get("no_website_only"))
    try:
        min_rating = float(data.get("min_rating") or 0)
    except (TypeError, ValueError):
        min_rating = 0
    if not trade:
        return jsonify({"error": "Enter a trade to search for"}), 400
    if not counties and not town:
        return jsonify({"error": "Pick at least one county, or type a town"}), 400

    # (text query, county, town name, lat/lng centre) — Google caps each query
    # at ~60 results, so a county-wide search runs one query per main town.
    queries = []
    if town:
        county = counties[0] if counties else ""
        match = next((t for c in ([county] if county else COUNTIES) for t in COUNTIES[c]["towns"]
                      if t[0].lower() == town.lower()), None)
        if not county and match:
            county = next(c for c in COUNTIES if match in COUNTIES[c]["towns"])
        where = f"{town}, {county}, Ireland" if county else f"{town}, Ireland"
        queries.append((f"{trade} in {where}", county, town, (match[1], match[2]) if match else None))
    else:
        for county in counties:
            for name, lat, lng in COUNTIES[county]["towns"]:
                queries.append((f"{trade} in {name}, {county}, Ireland", county, name, (lat, lng)))

    api_calls, errors, found = 0, [], {}

    def run(q):
        return q, places_text_search(q[0], q[3])

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(run, q) for q in queries]
        for future in as_completed(futures):
            try:
                (text_query, county, town_name, _), (places, calls) = future.result()
            except PlacesError as exc:
                errors.append(str(exc))
                continue
            api_calls += calls
            for place in places:
                if place.get("businessStatus", "OPERATIONAL") != "OPERATIONAL" or place["id"] in found:
                    continue
                found[place["id"]] = place_to_lead(place, county, town_name)

    print(f"[search] '{trade}' {counties or town}: {len(queries)} queries, {api_calls} Places API calls, "
          f"{len(found)} unique places", flush=True)
    if not found and errors:
        return jsonify({"error": errors[0]}), 502

    leads = list(found.values())
    if no_website_only:
        leads = [l for l in leads if not l["website"]]
    if min_rating:
        leads = [l for l in leads if (l["rating"] or 0) >= min_rating]

    pipeline_ids, pipeline_slugs = _pipeline_index()
    for lead in leads:
        lead["in_pipeline"] = lead["place_id"] in pipeline_ids or slugify(lead["name"]) in pipeline_slugs
        lead["score"] = score_place_lead(lead)

    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _prune_jobs()
        SEARCH_JOBS[job_id] = {"leads": {l["place_id"]: l for l in leads}, "total": len(leads),
                               "done": 0, "created": time.time()}
    for lead in leads:
        ENRICH_POOL.submit(_run_enrichment, job_id, lead["place_id"])

    return jsonify({
        "job_id": job_id,
        "results": leads,
        "queries": len(queries),
        "api_calls": api_calls,
        "warning": errors[0] if errors else None,
    })


@app.route("/api/search/status/<job_id>", methods=["GET"])
def api_search_status(job_id):
    with _jobs_lock:
        job = SEARCH_JOBS.get(job_id)
        if not job:
            return jsonify({"error": "search expired — run it again"}), 404
        return jsonify({"results": list(job["leads"].values()), "done": job["done"],
                        "total": job["total"], "finished": job["done"] >= job["total"]})


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
        existing_place_ids = {l["place_id"] for l in leads if l.get("place_id")}
        existing_slugs = {l["slug"] for l in leads}
        for lead in new_rows:
            key = (lead.get("name", ""), lead.get("email", ""))
            place_id = lead.get("place_id") or ""
            if key in existing_keys or (place_id and place_id in existing_place_ids):
                continue
            # Two different businesses can share a name; keep slugs unique.
            base_slug = slugify(lead.get("name", ""))
            slug, n = base_slug, 2
            while slug in existing_slugs:
                slug, n = f"{base_slug}-{n}", n + 1
            colors = lead.get("brand_colors") or []
            logo_path = lead.get("logo_path", "")
            leads.append({
                "name": lead.get("name", ""),
                "phone": lead.get("phone", ""),
                "email": lead.get("email", ""),
                "website": lead.get("website", ""),
                "location": lead.get("location", ""),
                "score": str(lead.get("score", "")),
                "years": lead.get("years", ""),
                "slug": slug,
                "demo_built": "No",
                "demo_url": "",
                "email_sent": "No",
                "replied": "No",
                "sold": "No",
                "place_id": place_id,
                "logo_path": logo_path,
                "brand_colors": ",".join(colors) if isinstance(colors, list) else str(colors),
                "rating": "" if lead.get("rating") is None else str(lead.get("rating")),
                "review_count": str(lead.get("review_count") or ""),
                "maps_url": lead.get("maps_url", ""),
                "town": lead.get("town", ""),
                "county": lead.get("county", ""),
                "use_logo": "Yes" if logo_path else "No",
            })
            existing_keys.add(key)
            existing_slugs.add(slug)
            if place_id:
                existing_place_ids.add(place_id)
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

    # Google Places leads carry a clean town; a full postal address reads
    # badly in copy ("Unit W3F1, ... W91 K2PK's electrician"). The full
    # address is still used for geocoding above, where precision helps.
    town_name = lead.get("town") or lead.get("location", "") or "Ireland"
    replacements = {
        "{{BUSINESS_NAME}}": lead.get("name", "") or "Your Business",
        "{{TOWN}}": town_name,
        "{{EMAIL}}": lead.get("email", "") or "",
        "{{OWNER_FIRST_NAME}}": owner_first_name(lead.get("name", "")),
        "{{SLUG}}": lead["slug"],
        "{{PHONE_DISPLAY}}": phone["display"] or "Call us",
        "{{PHONE_TEL}}": phone["tel"],
        "{{PHONE_INTL}}": phone["intl"],
        "{{PHONE_WA}}": phone["wa"],
        "{{LAT}}": repr(lat),
        "{{LNG}}": repr(lng),
        "{{HERO_HEADLINE}}": hero_headline(town_name, lead.get("years", "")),
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

    try:
        # Their brand colour is the starting accent; an explicitly saved
        # theme (from the Theme panel) takes precedence over it.
        brand_accent = first_usable_brand_color(lead.get("brand_colors"))
        if brand_accent and not lead.get("accent"):
            apply_accent(dest, brand_accent)
        apply_saved_theme(dest, lead)
        apply_brand_logo(dest, lead)
    except (ThemeError, OSError) as exc:
        return jsonify({"step": "theme", "error": f"Could not apply the theme/logo: {exc}"}), 500

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


def apply_edit_instruction(site_dir, instruction, layout_image=None, layout_image_media_type=None,
                            history_label=None, history_source="edit", scope_files=None):
    """Send the site's content files + an instruction to Claude and write
    back whatever files it changes. Returns (changed_files, error).

    layout_image: optional base64-encoded screenshot/mockup used as a literal
    layout reference (e.g. colour-coded boxes the user explains in
    `instruction`, like "blue box = hero, green box = services").

    history_label/history_source: describe this edit for version history —
    a snapshot of the site's current state is taken right before writing,
    so this edit (whatever triggered it: hotbar instruction, component add,
    etc.) can be undone. Defaults to the instruction text itself.

    scope_files: when given (e.g. a selected section's file + shared design
    tokens/icons), ONLY these files are sent to Claude and ONLY these paths
    may be written back — anything else in the response is rejected. This
    is what makes a section-scoped edit actually cheaper: fewer input
    tokens, and no risk of a scoped edit accidentally touching an unrelated
    file. Defaults to the full CONTENT_FILES bundle."""
    if not _client:
        return None, "ANTHROPIC_API_KEY not configured"

    allowed_files = scope_files or CONTENT_FILES
    bundle = []
    for rel in allowed_files:
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
        + ("" if scope_files else
        "You MAY create a brand-new file (e.g. splitting a section into its own "
        "src/components/SomeName.tsx) if that's the cleanest way to do the change — just make "
        "sure you also include and fully write that new file in your response, not only the file "
        "that imports it. An import with no corresponding file breaks the build "
        "('Module not found'). New files must be under src/components/.\n\n")
        + "Some components (e.g. Reviews.tsx) are async Server Components that `await` server-side "
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
        + (
            "The user selected a single section to edit, so you are ONLY shown that section's "
            "file plus the shared color tokens (tailwind.config.ts) and icon set (icons.tsx) — "
            "not the rest of the site. Only respond with changes to these exact files; you "
            "cannot create new files or touch any other component in a scoped edit like this.\n\n"
            if scope_files else ""
        )
        + "Respond with ONLY a JSON array (no markdown fences, no commentary) of objects "
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
        usage = getattr(message, "usage", None)
        if usage:
            scope_note = f"scoped to {scope_files}" if scope_files else "full site"
            print(f"[apply_edit_instruction] input tokens: {usage.input_tokens} "
                  f"(output: {usage.output_tokens}) — {scope_note}", flush=True)
    except Exception as exc:
        return None, str(exc)

    changed_files = extract_json_array(text)
    if changed_files is None:
        if truncated:
            return None, ("Claude's response was cut off (too many files changed at once). "
                           "Try a more targeted edit, e.g. one section at a time.")
        return None, "Claude returned invalid JSON"

    # Snapshot the pre-edit state now, right before it's overwritten — this
    # is what an Undo restores back to.
    snapshot_site(site_dir, history_label or instruction, history_source)

    written = []
    for item in changed_files:
        rel = item.get("path", "")
        content = item.get("content")
        if content is None:
            continue
        if scope_files is not None:
            if rel not in scope_files:
                continue
        elif rel not in CONTENT_FILES and not is_safe_new_component_path(rel):
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


# Maps a clicked-in-preview slot name (from EditBridge's data-slot attribute)
# to its component file, for section-scoped edits.
SLOT_FILE_MAP = {
    "nav": "src/components/Nav.tsx",
    "hero": "src/components/Hero.tsx",
    "trust": "src/components/TrustBar.tsx",
    "services": "src/components/Services.tsx",
    "about": "src/components/About.tsx",
    "process": "src/components/Process.tsx",
    "reviews": "src/components/Reviews.tsx",
    "contact": "src/components/Contact.tsx",
    "footer": "src/components/Footer.tsx",
}
SLOT_SCOPE_EXTRA_FILES = ["tailwind.config.ts", "src/components/icons.tsx"]


@app.route("/api/pipeline/edit_site", methods=["POST"])
def api_edit_site():
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    instruction = (data.get("instruction") or "").strip()
    image = data.get("image")  # optional base64 layout reference (no data: prefix)
    image_media_type = data.get("image_media_type") or "image/png"
    slot = (data.get("slot") or "").strip().lower()
    if not instruction:
        return jsonify({"error": "instruction is required"}), 400

    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not found"}), 404

    scope_files = None
    label = instruction
    if slot:
        slot_file = SLOT_FILE_MAP.get(slot)
        if not slot_file:
            return jsonify({"error": f"unknown slot: {slot}"}), 400
        scope_files = [slot_file] + SLOT_SCOPE_EXTRA_FILES
        label = f"[{slot}] {instruction}"

    written, error = apply_edit_instruction(
        site_dir, instruction, image, image_media_type,
        history_label=label, history_source="hotbar edit",
        scope_files=scope_files,
    )
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"ok": True, "changed_files": written})


# rel path -> (root JSX tag, slot name), for both the initial template edit
# and backfilling already-built sites.
SLOT_ROOT_TAG = {
    "src/components/Nav.tsx": ("header", "nav"),
    "src/components/Hero.tsx": ("section", "hero"),
    "src/components/TrustBar.tsx": ("section", "trust"),
    "src/components/Services.tsx": ("section", "services"),
    "src/components/About.tsx": ("section", "about"),
    "src/components/Process.tsx": ("section", "process"),
    "src/components/Reviews.tsx": ("section", "reviews"),
    "src/components/Contact.tsx": ("section", "contact"),
    "src/components/Footer.tsx": ("footer", "footer"),
}
EDIT_BRIDGE_SOURCE_PATH = TEMPLATE_SITE / "src" / "components" / "EditBridge.tsx"


def _inject_data_slot(content, tag, slot):
    """Add data-slot="<slot>" to the first <tag ...> that doesn't already
    have one. Returns (new_content, changed)."""
    if f'data-slot="{slot}"' in content:
        return content, False
    pattern = re.compile(rf"<{tag}\b(?![^>]*\bdata-slot=)")
    new_content, n = pattern.subn(f'<{tag} data-slot="{slot}"', content, count=1)
    return new_content, n > 0


def backfill_slot_markers(site_dir):
    """Apply the data-slot / EditBridge template changes to an
    already-built site so section-scoped editing works there too.
    Idempotent — safe to run repeatedly or on a site that already has it.
    Returns the list of relative paths it changed."""
    changed = []

    for rel, (tag, slot) in SLOT_ROOT_TAG.items():
        fp = site_dir / rel
        if not fp.exists():
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except OSError:
            continue
        new_content, did_change = _inject_data_slot(content, tag, slot)
        if did_change:
            fp.write_text(new_content, encoding="utf-8")
            changed.append(rel)

    edit_bridge_dest = site_dir / "src" / "components" / "EditBridge.tsx"
    if not edit_bridge_dest.exists() and EDIT_BRIDGE_SOURCE_PATH.exists():
        edit_bridge_dest.write_text(
            EDIT_BRIDGE_SOURCE_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        changed.append("src/components/EditBridge.tsx")

    layout_path = site_dir / "src" / "app" / "layout.tsx"
    if layout_path.exists():
        layout = layout_path.read_text(encoding="utf-8")
        if "EditBridge" not in layout:
            import_line = 'import { EditBridge } from "@/components/EditBridge";\n'
            last_import = None
            for m in re.finditer(r'^import .+;$', layout, re.MULTILINE):
                last_import = m
            if last_import:
                insert_at = last_import.end()
                layout = layout[:insert_at] + "\n" + import_line.rstrip("\n") + layout[insert_at:]
            else:
                layout = import_line + layout

            layout, n = re.subn(r"(<body[^>]*>)", r"\1\n        <EditBridge />", layout, count=1)
            if n:
                layout_path.write_text(layout, encoding="utf-8")
                changed.append("src/app/layout.tsx")

    return changed


@app.route("/api/admin/backfill_slots", methods=["POST"])
def api_backfill_slots():
    """Apply data-slot markers + EditBridge to every already-built site
    (the master template is edited directly, not through this route, but
    re-running it there too is harmless since it's idempotent)."""
    results = {}
    for site_dir in SITES_DIR.iterdir():
        if not site_dir.is_dir() or not (site_dir / "src").exists():
            continue
        try:
            results[site_dir.name] = backfill_slot_markers(site_dir)
        except OSError as exc:
            results[site_dir.name] = [f"error: {exc}"]
    return jsonify({"results": results})


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
    component_name = (data.get("component_name") or "").strip()
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
    written, error = apply_edit_instruction(
        site_dir, instruction,
        history_label=f"add: {component_name or section}", history_source="component",
    )
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"ok": True, "changed_files": written})


@app.route("/api/history/<slug>", methods=["GET"])
def api_history_list(slug):
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not found"}), 404
    return jsonify({"snapshots": list_snapshots(site_dir)})


@app.route("/api/history/<slug>/restore", methods=["POST"])
def api_history_restore(slug):
    data = request.get_json(force=True) or {}
    timestamp = data.get("timestamp")
    site_dir = SITES_DIR / slug
    if not site_dir.exists():
        return jsonify({"error": "site not found"}), 404
    if not timestamp:
        return jsonify({"error": "timestamp is required"}), 400

    label, error = restore_snapshot(site_dir, timestamp)
    if error:
        return jsonify({"error": error}), 400

    sync_saved_theme_from_files(site_dir)

    slug_preview = RUNNING_PREVIEWS.get(slug)
    return jsonify({"ok": True, "label": label, "preview_port": slug_preview["port"] if slug_preview else None})


# ---------------------------------------------------------------------------
# Theme panel — colours / fonts / corners as direct, instant file edits.
# Deliberately never calls Claude: every change is a precise rewrite of one
# value in a known place.
# ---------------------------------------------------------------------------

class ThemeError(Exception):
    pass


PALETTE_PRESETS = {
    "Electric": "#1D4ED8",
    "Flame": "#FF5200",
    "Forest": "#16A34A",
    "Slate": "#475569",
    "Crimson": "#C41E3A",
    "Gold": "#D4A017",
}
# Tokens that are structural (backgrounds, text, lines), never the accent.
NEUTRAL_COLOR_TOKENS = {
    "base", "navy", "ink", "grey", "gray", "background", "foreground",
    "muted-foreground", "accent-foreground", "white", "black",
}
_HEX6_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_COLOR_ENTRY_RE = re.compile(
    r"""(?P<key>[A-Za-z_][\w-]*|"[^"]+"|'[^']+')\s*:\s*"""
    r"""(?P<val>\{|["'](?P<hex>#[0-9A-Fa-f]{3,8})["'])"""
)


def _next_font_preset(key, import_name):
    return (
        "// Written by SiteForge's theme panel — choose a different font there to replace this file.\n"
        f'import {{ {import_name} }} from "next/font/google";\n\n'
        f'const font = {import_name}({{ subsets: ["latin"], variable: "--font-body", display: "swap" }});\n\n'
        f'export const FONT_PRESET = "{key}";\n'
        "export const fontClassName = font.variable;\n"
        "export const fontStyle: Record<string, string> = {};\n"
        "export const fontStylesheet: string | null = null;\n"
    )


# key -> (label, complete src/fonts.ts). Every preset exports the same four
# names, which is the whole contract layout.tsx relies on.
FONT_PRESETS = {
    "geist": ("Geist", (
        "// Written by SiteForge's theme panel — choose a different font there to replace this file.\n"
        "// Geist isn't in Next 14.2's next/font/google list, so it's loaded straight from Google Fonts.\n\n"
        'export const FONT_PRESET = "geist";\n'
        'export const fontClassName = "";\n'
        "export const fontStyle: Record<string, string> = {\n"
        "  \"--font-body\": \"'Geist', system-ui, sans-serif\",\n"
        "};\n"
        "export const fontStylesheet: string | null =\n"
        '  "https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap";\n'
    )),
    "inter": ("Inter", _next_font_preset("inter", "Inter")),
    "plus-jakarta-sans": ("Plus Jakarta Sans", _next_font_preset("plus-jakarta-sans", "Plus_Jakarta_Sans")),
    "dm-sans": ("DM Sans", _next_font_preset("dm-sans", "DM_Sans")),
}
DEFAULT_FONT_PRESET = "inter"


def _match_brace(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _expand_hex(hex_):
    h = hex_.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return "#" + h[:6].upper()


def parse_color_tokens(config_text):
    """Every hex colour in tailwind.config.ts's `colors` object, as
    {path, label, hex, start, end}. start/end are the offsets of the hex
    literal itself, so a change rewrites exactly that value and nothing
    else in the file."""
    m = re.search(r"\bcolors\s*:\s*\{", config_text)
    if not m:
        return []
    open_idx = m.end() - 1
    close_idx = _match_brace(config_text, open_idx)
    if close_idx == -1:
        return []

    tokens = []
    pos = open_idx + 1
    while True:
        em = _COLOR_ENTRY_RE.search(config_text, pos, close_idx)
        if not em:
            break
        key = em.group("key").strip("\"'")
        if em.group("val") != "{":
            tokens.append({"path": key, "label": key, "hex": em.group("hex"),
                           "start": em.start("hex"), "end": em.end("hex")})
            pos = em.end()
            continue
        sub_open = em.end() - 1
        sub_close = _match_brace(config_text, sub_open)
        if sub_close == -1:
            break
        spos = sub_open + 1
        while True:
            sm = _COLOR_ENTRY_RE.search(config_text, spos, sub_close)
            if not sm:
                break
            if sm.group("val") == "{":  # nested deeper than token.shade — not a swatch
                deeper = _match_brace(config_text, sm.end() - 1)
                spos = deeper + 1 if deeper != -1 else sub_close
                continue
            sub = sm.group("key").strip("\"'")
            tokens.append({
                "path": f"{key}.{sub}",
                "label": key if sub == "DEFAULT" else f"{key}-{sub}",
                "hex": sm.group("hex"), "start": sm.start("hex"), "end": sm.end("hex"),
            })
            spos = sm.end()
        pos = sub_close + 1
    return tokens


def detect_accent_token(site_dir, tokens):
    """The accent is whichever non-neutral colour token the components use
    most as a background — `blue` in the template, but a re-themed site
    (e.g. one switched to `orange`) is detected correctly too."""
    candidates = []
    for t in tokens:
        name = t["path"].split(".")[0]
        if name not in NEUTRAL_COLOR_TOKENS and name not in candidates:
            candidates.append(name)
    if not candidates:
        return None
    corpus = "".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in (site_dir / "src").rglob("*.tsx")
    )

    def usage(name):
        return len(re.findall(rf"(?<![\w-])bg-{re.escape(name)}(?![\w-])", corpus))

    return max(candidates, key=usage)


def _luminance(hex_):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.299 * r + 0.587 * g + 0.114 * b


def _darken(hex_, factor=0.78):
    h = hex_.lstrip("#")
    r, g, b = (max(0, min(255, round(int(h[i:i + 2], 16) * factor))) for i in (0, 2, 4))
    return f"#{r:02X}{g:02X}{b:02X}"


def _config_path(site_dir):
    return site_dir / "tailwind.config.ts"


def _set_token_hex(site_dir, path, hex_):
    cfg = _config_path(site_dir)
    text = cfg.read_text(encoding="utf-8")
    token = next((t for t in parse_color_tokens(text) if t["path"] == path), None)
    if not token:
        raise ThemeError(f"colour token '{path}' not found in tailwind.config.ts")
    cfg.write_text(text[:token["start"]] + hex_.upper() + text[token["end"]:], encoding="utf-8")


def _accent_info(site_dir):
    tokens = parse_color_tokens(_config_path(site_dir).read_text(encoding="utf-8"))
    accent = detect_accent_token(site_dir, tokens)
    if not accent:
        raise ThemeError("couldn't find an accent colour token in tailwind.config.ts")
    paths = {t["path"] for t in tokens}
    default_path = f"{accent}.DEFAULT" if f"{accent}.DEFAULT" in paths else accent
    dark_path = f"{accent}.dark" if f"{accent}.dark" in paths else None
    return accent, default_path, dark_path, paths


def ensure_accent_foreground(site_dir, accent, fg_hex):
    """Make sure an `accent-foreground` token exists (set to fg_hex), and
    that text sitting directly on an accent-filled element uses it instead
    of a hard-coded text-white — so auto-contrast actually reaches buttons."""
    cfg = _config_path(site_dir)
    text = cfg.read_text(encoding="utf-8")
    if any(t["path"] == "accent-foreground" for t in parse_color_tokens(text)):
        _set_token_hex(site_dir, "accent-foreground", fg_hex)
    else:
        new_text, n = re.subn(
            r"(\bcolors\s*:\s*\{)(\s*\n)([ \t]*)",
            rf'\1\2\3"accent-foreground": "{fg_hex}",\n\3',
            text, count=1,
        )
        if not n:
            raise ThemeError("couldn't add accent-foreground to tailwind.config.ts")
        cfg.write_text(new_text, encoding="utf-8")

    # Only unprefixed classes: a plain bg-<accent> fill with plain text-white
    # on the same element. Hover/group-hover variants are left alone.
    bg_re = re.compile(rf"(?<![\w:/-])bg-{re.escape(accent)}(?![\w/-])")
    white_re = re.compile(r"(?<![\w:/-])text-white(?![\w/-])")

    def fix_class(match):
        classes = match.group(1)
        if bg_re.search(classes) and white_re.search(classes):
            return f'className="{white_re.sub("text-accent-foreground", classes)}"'
        return match.group(0)

    for path in (site_dir / "src").rglob("*.tsx"):
        src = path.read_text(encoding="utf-8")
        new_src = re.sub(r'className="([^"]*)"', fix_class, src)
        if new_src != src:
            path.write_text(new_src, encoding="utf-8")


def apply_accent(site_dir, hex_):
    accent, default_path, dark_path, _ = _accent_info(site_dir)
    _set_token_hex(site_dir, default_path, hex_)
    if dark_path:  # keep hover states (bg-<accent>-dark) in the same family
        _set_token_hex(site_dir, dark_path, _darken(hex_))
    fg = "#111111" if _luminance(hex_) > 150 else "#FFFFFF"
    ensure_accent_foreground(site_dir, accent, fg)
    return accent


def ensure_radius_scaffolding(site_dir):
    """Route the `rounded-sharp` radius (used by every button and card)
    through a --radius CSS variable in globals.css."""
    cfg = _config_path(site_dir)
    text = cfg.read_text(encoding="utf-8")
    current_px = "4"
    if "var(--radius)" not in text:
        m = re.search(r"""(sharp\s*:\s*)["'](\d+(?:\.\d+)?)px["']""", text)
        if not m:
            raise ThemeError("this site's tailwind.config.ts has no rounded-sharp radius to control")
        current_px = m.group(2)
        cfg.write_text(text[:m.start()] + m.group(1) + '"var(--radius)"' + text[m.end():], encoding="utf-8")

    css_path = site_dir / "src" / "app" / "globals.css"
    css = css_path.read_text(encoding="utf-8")
    if "--radius:" not in css:
        new_css, n = re.subn(r":root\s*\{", f":root {{\n  --radius: {current_px}px;", css, count=1)
        if not n:
            new_css = css + f"\n:root {{\n  --radius: {current_px}px;\n}}\n"
        css_path.write_text(new_css, encoding="utf-8")


def apply_radius(site_dir, px):
    ensure_radius_scaffolding(site_dir)
    css_path = site_dir / "src" / "app" / "globals.css"
    css = css_path.read_text(encoding="utf-8")
    css_path.write_text(re.sub(r"--radius:\s*[^;]+;", f"--radius: {px}px;", css, count=1), encoding="utf-8")


def ensure_font_scaffolding(site_dir):
    """Move layout.tsx from importing its font directly to importing it
    from src/fonts.ts, so switching fonts is just overwriting that one file.
    Everything is validated before anything is written, so a customised
    layout fails cleanly instead of being half-migrated."""
    fonts_path = site_dir / "src" / "fonts.ts"
    layout_path = site_dir / "src" / "app" / "layout.tsx"
    layout = layout_path.read_text(encoding="utf-8")
    if "@/fonts" in layout and fonts_path.exists():
        return

    new_layout = re.sub(r'import\s*\{\s*Inter\s*\}\s*from\s*"next/font/google";\s*\n', "", layout, count=1)
    new_layout, n_const = re.subn(r"const inter = Inter\(\{[\s\S]*?\}\);\s*\n", "", new_layout, count=1)
    new_layout, n_cls = re.subn(
        r"className=\{inter\.variable\}",
        "className={fontClassName} style={fontStyle as React.CSSProperties}",
        new_layout, count=1,
    )
    new_layout, n_imp = re.subn(
        r'(import "\./globals\.css";)',
        r'\1' + '\nimport { fontClassName, fontStyle, fontStylesheet } from "@/fonts";',
        new_layout, count=1,
    )
    new_layout, n_head = re.subn(
        r"<head>",
        "<head>\n        {fontStylesheet && <link rel=\"stylesheet\" href={fontStylesheet} />}",
        new_layout, count=1,
    )
    if not (n_const and n_cls and n_imp and n_head):
        raise ThemeError("this site's layout.tsx has been customised, so fonts can't be switched automatically")

    cfg = _config_path(site_dir)
    cfg_text = cfg.read_text(encoding="utf-8").replace("var(--font-inter)", "var(--font-body)")

    css_path = site_dir / "src" / "app" / "globals.css"
    css = css_path.read_text(encoding="utf-8")
    if "--font-heading" not in css:
        css += (
            "\n@layer base {\n"
            "  h1, h2, h3, h4, h5, h6 {\n"
            "    font-family: var(--font-heading, var(--font-body)), system-ui, sans-serif;\n"
            "  }\n"
            "}\n"
        )

    layout_path.write_text(new_layout, encoding="utf-8")
    cfg.write_text(cfg_text, encoding="utf-8")
    css_path.write_text(css, encoding="utf-8")
    if not fonts_path.exists():
        fonts_path.write_text(FONT_PRESETS[DEFAULT_FONT_PRESET][1], encoding="utf-8")


def apply_font(site_dir, key):
    ensure_font_scaffolding(site_dir)
    (site_dir / "src" / "fonts.ts").write_text(FONT_PRESETS[key][1], encoding="utf-8")


def read_theme(site_dir):
    cfg_text = _config_path(site_dir).read_text(encoding="utf-8")
    tokens = parse_color_tokens(cfg_text)
    accent = detect_accent_token(site_dir, tokens)

    font = None
    fonts_path = site_dir / "src" / "fonts.ts"
    if fonts_path.exists():
        m = re.search(r'FONT_PRESET\s*=\s*"([\w-]+)"', fonts_path.read_text(encoding="utf-8"))
        font = m.group(1) if m else None

    radius = None
    css_path = site_dir / "src" / "app" / "globals.css"
    m = re.search(r"--radius:\s*(\d+(?:\.\d+)?)px", css_path.read_text(encoding="utf-8")) if css_path.exists() else None
    if not m:
        m = re.search(r"""sharp\s*:\s*["'](\d+(?:\.\d+)?)px["']""", cfg_text)
    if m:
        radius = round(float(m.group(1)))

    return {
        "tokens": [{"path": t["path"], "label": t["label"], "hex": _expand_hex(t["hex"])} for t in tokens],
        "accent": accent,
        "accent_path": (f"{accent}.DEFAULT" if any(t["path"] == f"{accent}.DEFAULT" for t in tokens) else accent)
        if accent else None,
        "font": font,
        "radius": radius,
        "palettes": [{"name": k, "hex": v} for k, v in PALETTE_PRESETS.items()],
        "fonts": [{"key": k, "label": v[0]} for k, v in FONT_PRESETS.items()],
    }


def apply_saved_theme(site_dir, lead):
    """Re-apply a lead's saved theme to a freshly cloned site (rebuilds
    start from the template, so without this they'd lose it)."""
    accent = (lead.get("accent") or "").strip()
    font = (lead.get("font") or "").strip()
    radius = (lead.get("radius") or "").strip()
    if _HEX6_RE.match(accent):
        apply_accent(site_dir, accent)
    if font in FONT_PRESETS:
        apply_font(site_dir, font)
    if radius.isdigit() and 0 <= int(radius) <= 20:
        apply_radius(site_dir, int(radius))


def sync_saved_theme_from_files(site_dir):
    """After an undo/restore, make the lead's saved theme match what's on
    disk again — otherwise a rebuild would re-apply a theme that was undone.
    Only touches leads that have a saved theme; untouched leads stay on the
    template defaults."""
    try:
        theme = read_theme(site_dir)
    except OSError:
        return
    accent_hex = next((t["hex"] for t in theme["tokens"] if t["path"] == theme["accent_path"]), "")
    with leads_transaction() as leads:
        lead = find_lead(leads, site_dir.name)
        if not lead or not any(lead.get(k) for k in ("accent", "font", "radius")):
            return
        lead["accent"] = accent_hex
        lead["font"] = theme["font"] or ""
        lead["radius"] = "" if theme["radius"] is None else str(theme["radius"])


def first_usable_brand_color(brand_colors):
    """First brand colour that works as a button accent — not so light or
    dark that it'd disappear against the site's backgrounds."""
    colors = brand_colors.split(",") if isinstance(brand_colors, str) else (brand_colors or [])
    for c in colors:
        c = c.strip()
        if _HEX6_RE.match(c) and 25 < _luminance(c) < 225:
            return c.upper()
    return None


def apply_brand_logo(site_dir, lead):
    """Copy the lead's logo into public/ and point src/brand.ts at it when
    "Use their logo" is on; otherwise clear it. Sites built before the
    template had brand.ts are left alone (returns False)."""
    brand_ts = site_dir / "src" / "brand.ts"
    if not brand_ts.exists():
        return False
    logo_src = LOGOS_DIR / f"{lead.get('place_id')}.png" if lead.get("place_id") else None
    use = lead.get("use_logo") == "Yes" and logo_src is not None and logo_src.exists()
    if use:
        shutil.copy2(logo_src, site_dir / "public" / "brand-logo.png")
    value = '"/brand-logo.png"' if use else "null"
    text = brand_ts.read_text(encoding="utf-8")
    brand_ts.write_text(re.sub(r"BRAND_LOGO: string \| null = [^;]+;", f"BRAND_LOGO: string | null = {value};", text),
                        encoding="utf-8")
    return True


def _resolve_site_dir(slug):
    """SITES_DIR/<slug>, refusing anything that would resolve outside it."""
    site_dir = (SITES_DIR / (slug or "")).resolve()
    if site_dir.parent != SITES_DIR.resolve() or not site_dir.is_dir():
        return None
    return site_dir


@app.route("/api/theme/<slug>", methods=["GET"])
def api_theme_get(slug):
    site_dir = _resolve_site_dir(slug)
    if not site_dir:
        return jsonify({"error": "site not found"}), 404
    try:
        return jsonify(read_theme(site_dir))
    except OSError as exc:
        return jsonify({"error": f"couldn't read theme: {exc}"}), 500


@app.route("/api/theme/<slug>", methods=["POST"])
def api_theme_set(slug):
    site_dir = _resolve_site_dir(slug)
    if not site_dir:
        return jsonify({"error": "site not found"}), 404
    data = request.get_json(force=True) or {}
    kind = data.get("kind")

    # Validate fully before snapshotting, so a bad request leaves no trace.
    saved = {}
    if kind in ("accent", "color"):
        hex_ = (data.get("hex") or "").strip()
        if not _HEX6_RE.match(hex_):
            return jsonify({"error": "hex must look like #RRGGBB"}), 400
        hex_ = hex_.upper()
    if kind == "accent":
        preset_name = next((k for k, v in PALETTE_PRESETS.items() if v.upper() == hex_), None)
        label = f"theme: {preset_name or hex_}"
    elif kind == "color":
        path = data.get("path") or ""
        try:
            _, accent_default_path, _, paths = _accent_info(site_dir)
        except ThemeError as exc:
            return jsonify({"error": str(exc)}), 400
        if path not in paths:
            return jsonify({"error": f"unknown colour token '{path}'"}), 400
        label = f"theme: {path} {hex_}"
    elif kind == "font":
        key = data.get("font")
        if key not in FONT_PRESETS:
            return jsonify({"error": "unknown font preset"}), 400
        label = f"theme: font {FONT_PRESETS[key][0]}"
    elif kind == "radius":
        try:
            px = int(data.get("radius"))
        except (TypeError, ValueError):
            return jsonify({"error": "radius must be a number"}), 400
        if not 0 <= px <= 20:
            return jsonify({"error": "radius must be 0-20px"}), 400
        label = f"theme: corners {px}px"
    else:
        return jsonify({"error": "kind must be accent, color, font or radius"}), 400

    snapshot_site(site_dir, label, "theme")
    try:
        if kind == "accent":
            apply_accent(site_dir, hex_)
            saved["accent"] = hex_
        elif kind == "color":
            if path == accent_default_path:  # picking the accent directly still gets auto-contrast
                apply_accent(site_dir, hex_)
                saved["accent"] = hex_
            else:
                _set_token_hex(site_dir, path, hex_)
        elif kind == "font":
            apply_font(site_dir, key)
            saved["font"] = key
        elif kind == "radius":
            apply_radius(site_dir, px)
            saved["radius"] = str(px)
    except ThemeError as exc:
        return jsonify({"error": str(exc)}), 400
    except OSError as exc:
        return jsonify({"error": f"couldn't write theme files: {exc}"}), 500

    if saved:
        with leads_transaction() as leads:
            lead = find_lead(leads, site_dir.name)
            if lead:
                lead.update(saved)

    return jsonify({"ok": True, "label": label, "theme": read_theme(site_dir)})


DEPLOY_IGNORE_DIRS = {"node_modules", ".next", ".git", ".vercel", HISTORY_DIRNAME}
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


@app.route("/api/pipeline/use_logo", methods=["POST"])
def api_use_logo():
    """Toggle "Use their logo". If the site's already built from the
    current template, the change is applied straight away (snapshotted
    first); otherwise it takes effect on the next build."""
    data = request.get_json(force=True) or {}
    slug = data.get("slug")
    value = "Yes" if data.get("value") else "No"
    with leads_transaction() as leads:
        lead = find_lead(leads, slug)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        lead["use_logo"] = value
        lead = dict(lead)

    applied = False
    site_dir = _resolve_site_dir(slug)
    if site_dir and (site_dir / "src" / "brand.ts").exists():
        snapshot_site(site_dir, f"logo: {'on' if value == 'Yes' else 'off'}", "logo")
        applied = apply_brand_logo(site_dir, lead)
    return jsonify({"lead": lead, "applied": applied})


def open_browser(port):
    webbrowser.open(f"http://localhost:{port}")


# Runs on import too (not just `python app.py`), so a production WSGI server
# (gunicorn, per the Procfile) that imports this module directly still gets
# the database/sites-folder set up — the __main__ block below never runs
# under gunicorn.
ensure_db()
SITES_DIR.mkdir(exist_ok=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"SiteForge running at localhost:{port}")
    if not os.environ.get("PORT"):
        # Only auto-open a local browser for local dev — meaningless (and
        # unwanted) when running as a deployed service.
        Timer(1.0, open_browser, args=(port,)).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
