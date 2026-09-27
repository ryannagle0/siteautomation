"""Logo handling for SiteForge.

- extract_emblem(): pull the emblem (the graphic mark, without the baked-in
  lettering) out of a business's downloaded logo — projection-profile
  heuristics first, one Claude vision call only when they're unsure.
- generate_emblems(): six fallback emblems built as plain SVG (initials /
  Lucide trade icons), for businesses with no usable logo.
- write_favicons() / write_og_image(): favicon.ico, apple icon and the
  1200x630 share image, rendered with Pillow from whichever emblem is chosen.

Everything for one lead lives in data/logos/<key>/:
    original.png   the downloaded / uploaded logo, untouched
    emblem.png     cropped emblem, transparent, 12% padding, square
    emblem.svg     traced version (only for flat logos: <=8 colours, <60KB)
    meta.json      type, confidence, method, extracted text
    generated/1.svg … 6.svg, ai-1.svg … ai-3.svg
"""

import base64
import io
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import vtracer
except ImportError:  # optional: without it there's just no emblem.svg
    vtracer = None
try:
    import resvg_py
except ImportError:  # optional: without it SVG emblems can't become favicons
    resvg_py = None

EMBLEM_TYPES = ("emblem_and_text", "emblem_only", "text_only")
MAX_ORIGINAL_SIDE = 1024


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def hex_rgb(hex_):
    h = hex_.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(hex_):
    r, g, b = hex_rgb(hex_)
    return 0.299 * r + 0.587 * g + 0.114 * b


def contrast_fg(hex_):
    """White or near-black text/icon colour for a background colour."""
    return "#111111" if luminance(hex_) > 150 else "#FFFFFF"


def save_original(img, out_dir):
    """Store an uploaded/downloaded logo as original.png (capped at 1024px)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    img = img.convert("RGBA")
    if max(img.size) > MAX_ORIGINAL_SIDE:
        img.thumbnail((MAX_ORIGINAL_SIDE, MAX_ORIGINAL_SIDE), Image.LANCZOS)
    img.save(out_dir / "original.png", "PNG")


def rasterize_svg(svg_text, size):
    if resvg_py is None:
        raise RuntimeError("resvg-py is not installed")
    png = resvg_py.svg_to_bytes(svg_string=svg_text, width=size, height=size)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def load_emblem_image(path, size=512):
    """An emblem file (png or svg) as a square RGBA image."""
    path = Path(path)
    if path.suffix.lower() == ".svg":
        return rasterize_svg(path.read_text(encoding="utf-8"), size)
    img = Image.open(path).convert("RGBA")
    return img.resize((size, size), Image.LANCZOS) if img.size != (size, size) else img


def _trim(img, threshold=16):
    alpha = np.array(img)[..., 3]
    ys, xs = np.nonzero(alpha > threshold)
    if not len(xs):
        return None
    return img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


# ---------------------------------------------------------------------------
# 1a. Normalise: key out a solid background, trim
# ---------------------------------------------------------------------------

def normalise(img, strict=False):
    """RGBA copy with a solid background made transparent (if the four
    corners agree on one colour) and trimmed to the visible pixels.
    strict=True keys out a wider colour range, and falls back to the most
    common border colour when the corners don't agree — for halos and
    off-white boxes the normal pass leaves behind. Returns (image|None, bg_removed)."""
    img = img.convert("RGBA")
    arr = np.array(img).astype(np.int16)
    h, w = arr.shape[:2]
    k = max(1, min(h, w) // 40)
    patches = [arr[:k, :k], arr[:k, -k:], arr[-k:, :k], arr[-k:, -k:]]
    means = [p.reshape(-1, 4).mean(axis=0) for p in patches]

    bg = None
    if all(m[3] > 200 for m in means):
        rgb = [m[:3] for m in means]
        if max(np.linalg.norm(a - b) for a in rgb for b in rgb) <= 20:
            bg = np.mean(rgb, axis=0)
    if bg is None and strict:
        border = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
        border = border[border[:, 3] > 200]
        if len(border) > (2 * (w + h)) * 0.5:
            colours, counts = np.unique((border[:, :3] // 8) * 8, axis=0, return_counts=True)
            if counts.max() > len(border) * 0.4:
                bg = colours[counts.argmax()].astype(float) + 4

    removed = False
    if bg is not None:
        lo, hi = (45, 110) if strict else (22, 60)
        dist = np.linalg.norm(arr[..., :3] - bg, axis=-1)
        keep = np.clip((dist - lo) / (hi - lo), 0, 1)  # soft edge for anti-aliasing
        arr[..., 3] = (arr[..., 3] * keep).astype(np.int16)
        removed = True
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    return _trim(out), removed


# ---------------------------------------------------------------------------
# 1b. Layout detection with projection profiles
# ---------------------------------------------------------------------------

def _runs(profile, min_gap):
    """(start, end) runs of True in a 1-D profile, merging runs separated
    by gaps shorter than min_gap."""
    idx = np.flatnonzero(profile)
    if not len(idx):
        return []
    runs, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev - 1 >= min_gap:
            runs.append((int(start), int(prev) + 1))
            start = i
        prev = i
    runs.append((int(start), int(prev) + 1))
    return runs


def _cluster(mask, x0, x1, y0, y1):
    """Tighten a region to its content and describe its shape."""
    sub = mask[y0:y1, x0:x1]
    rows, cols = np.flatnonzero(sub.any(axis=1)), np.flatnonzero(sub.any(axis=0))
    if not len(rows) or not len(cols):
        return None
    y0, y1 = y0 + int(rows[0]), y0 + int(rows[-1]) + 1
    x0, x1 = x0 + int(cols[0]), x0 + int(cols[-1]) + 1
    w, h = x1 - x0, y1 - y0
    return {
        "bbox": (x0, y0, w, h),
        "aspect": w / h,
        "hfrac": h / mask.shape[0],
        # separate shapes left-to-right: letters in a word, 1-2 for an emblem
        "pieces": len(_runs(mask[y0:y1, x0:x1].any(axis=0), 1)),
        "area": w * h,
    }


def _squareish(c):
    return 0.6 <= c["aspect"] <= 1.6


def _texty(c):
    return c["aspect"] >= 1.8 and c["pieces"] >= 3


def detect_layout(mask):
    """Find the emblem in a trimmed logo mask. Returns
    {type, bbox (x, y, w, h) or None, confidence 0-1}."""
    H, W = mask.shape
    whole = {"type": "emblem_only", "bbox": (0, 0, W, H)}

    cols = [c for c in (_cluster(mask, a, b, 0, H) for a, b in _runs(mask.any(axis=0), max(2, round(W * 0.04)))) if c]
    if len(cols) >= 2:
        # Side by side: emblem is the squarish cluster that's nearly full height.
        cands = [c for c in cols if _squareish(c) and c["hfrac"] >= 0.6]
        others = [c for c in cols if c not in cands]
        if len(cands) == 1:
            textlike = all(_texty(o) or o["hfrac"] < 0.6 for o in others)
            return {"type": "emblem_and_text", "bbox": cands[0]["bbox"], "confidence": 0.9 if textlike else 0.72}
        if len(cands) > 1:
            return {"type": "emblem_and_text", "bbox": cands[0]["bbox"], "confidence": 0.45}
        if all(_texty(c) for c in cols):
            return {"type": "text_only", "bbox": None, "confidence": 0.65}
        return {**whole, "confidence": 0.3}

    rows = [c for c in (_cluster(mask, 0, W, a, b) for a, b in _runs(mask.any(axis=1), max(2, round(H * 0.04)))) if c]
    if len(rows) >= 2:
        # Stacked: emblem above (or below) a wide, short text line.
        biggest = max(rows, key=lambda c: c["area"])
        rest = [c for c in rows if c is not biggest]
        if _squareish(biggest) and all(_texty(c) or c["aspect"] >= 2.5 for c in rest):
            return {"type": "emblem_and_text", "bbox": biggest["bbox"], "confidence": 0.85}
        if _squareish(biggest):
            return {"type": "emblem_and_text", "bbox": biggest["bbox"], "confidence": 0.55}
        if all(_texty(c) or c["aspect"] >= 2.5 for c in rows):
            return {"type": "text_only", "bbox": None, "confidence": 0.6}
        return {**whole, "confidence": 0.3}

    c = rows[0] if rows else _cluster(mask, 0, W, 0, H)
    if c is None:
        return {"type": "text_only", "bbox": None, "confidence": 0.0}
    if _squareish(c):
        return {**whole, "confidence": 0.9 if c["pieces"] <= 3 else 0.6}
    if _texty(c):
        return {"type": "text_only", "bbox": None, "confidence": 0.8 if c["pieces"] >= 4 else 0.6}
    return {**whole, "confidence": 0.4}


# ---------------------------------------------------------------------------
# 1c. Vision fallback (one Claude call)
# ---------------------------------------------------------------------------

def _json_from_text(text, opener="{", closer="}"):
    start, end = text.find(opener), text.rfind(closer)
    if start < 0 or end <= start:
        raise ValueError("no JSON in reply")
    return json.loads(text[start:end + 1])


def _log_usage(tag, resp):
    usage = getattr(resp, "usage", None)
    if usage:
        print(f"[{tag}] input tokens: {usage.input_tokens} (output: {usage.output_tokens})", flush=True)


def vision_layout(client, model, img):
    """Ask Claude where the emblem is. Returns {type, bbox, text}, bbox in img pixels."""
    view = img.copy()
    view.thumbnail((512, 512), Image.LANCZOS)
    scale = img.width / view.width
    # Put it on a backdrop that contrasts with the logo, so white-on-clear
    # logos aren't invisible.
    arr = np.array(view)
    opaque = arr[..., 3] > 128
    mean_lum = float((arr[opaque][:, :3] @ [0.299, 0.587, 0.114]).mean()) if opaque.any() else 0
    backdrop = Image.new("RGBA", view.size, (40, 40, 40, 255) if mean_lum > 170 else (245, 245, 245, 255))
    backdrop.alpha_composite(view)
    buf = io.BytesIO()
    backdrop.convert("RGB").save(buf, "PNG")

    prompt = (
        f"This is a business logo, {view.width}x{view.height} pixels. Reply with JSON only, no other text:\n"
        '{"type": "emblem_and_text" | "emblem_only" | "text_only", "emblem_bbox": [x, y, w, h], '
        '"text": "text found in logo", "generic_symbol": true | false, "confidence": 0.0-1.0}\n'
        "The emblem is the graphic mark or icon, not the lettering. emblem_bbox is in pixels of this "
        "image and must not include any lettering; use null for text_only. If a letter is drawn as "
        "the graphic mark itself (a monogram), that counts as the emblem. If this is a photograph or a "
        'website screenshot rather than a logo, reply {"type": "text_only", "emblem_bbox": null, '
        '"text": "", "not_a_logo": true}.\n'
        "generic_symbol is true when the graphic mark is a generic stock or clip-art symbol rather "
        "than something made for this business: recycling arrows, a globe, a check mark/tick, a "
        "generic swoosh, a plain house outline, a stock lightning bolt or lightbulb, a stock tree. "
        "confidence is how sure you are that this image is the business's own logo AND that the "
        "emblem_bbox is right."
    )
    resp = client.messages.create(
        model=model, max_tokens=300,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(buf.getvalue()).decode("ascii")}},
            {"type": "text", "text": prompt},
        ]}],
    )
    _log_usage("logo vision", resp)
    data = _json_from_text("".join(getattr(b, "text", "") for b in resp.content))
    kind = data.get("type")
    if kind not in EMBLEM_TYPES:
        raise ValueError(f"unexpected type {kind!r}")
    bbox = None
    if kind != "text_only":
        raw = data.get("emblem_bbox")
        if isinstance(raw, list) and len(raw) == 4 and all(isinstance(v, (int, float)) for v in raw):
            x, y, w, h = (v * scale for v in raw)
            x0, y0 = max(0, int(x)), max(0, int(y))
            x1, y1 = min(img.width, int(x + w + 0.5)), min(img.height, int(y + h + 0.5))
            if x1 - x0 >= 8 and y1 - y0 >= 8:
                bbox = (x0, y0, x1 - x0, y1 - y0)
        if bbox is None:
            if kind != "emblem_only":
                raise ValueError("no usable emblem_bbox")
            bbox = (0, 0, img.width, img.height)
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence"))))
    except (TypeError, ValueError):
        confidence = None
    return {"type": kind, "bbox": bbox, "text": str(data.get("text") or "")[:200],
            "not_a_logo": bool(data.get("not_a_logo")), "generic_symbol": bool(data.get("generic_symbol")),
            "confidence": confidence}


# ---------------------------------------------------------------------------
# 1d. Output: emblem.png, emblem.svg, meta.json
# ---------------------------------------------------------------------------

def _looks_like_photo(img):
    """Too many colours for 16 to represent well: a photo or screenshot."""
    small = img.convert("RGB")
    small.thumbnail((128, 128))
    px = np.array(small).reshape(-1, 3).astype(int)
    quant = np.array(small.quantize(colors=16).convert("RGB")).reshape(-1, 3).astype(int)
    return (np.linalg.norm(quant - px, axis=1) > 30).mean() > 0.15


def square_pad(img, pad=0.12, max_side=512):
    img = _trim(img) or img
    side = int(round(max(img.size) * (1 + 2 * pad)))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
    if side > max_side:
        canvas = canvas.resize((max_side, max_side), Image.LANCZOS)
    return canvas


SVG_FILL_RE = re.compile(r'fill="(#[0-9A-Fa-f]{6})"')


# vtracer is native code, and 0.6.15 on Python 3.14 segfaults on any
# keyword argument and on some transparent images — either would take the
# whole Flask server down. So it runs in a throwaway subprocess, on an
# opaque image, with positional arguments only:
# (in, out, colormode, hierarchical, mode, filter_speckle, color_precision, layer_difference)
_TRACE_CODE = (
    "import sys, vtracer\n"
    "vtracer.convert_image_to_svg_py(sys.argv[1], sys.argv[2], 'color', 'cutout', 'spline', 4, 8, 16)\n"
)
_KEY_COLOURS = [(255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 0, 0), (0, 0, 255)]
_PATH_RE = re.compile(r"<path\b[^>]*/>", re.S)


def trace_svg(emblem):
    """vtracer SVG of a flat-colour emblem, or None (photo-like emblem,
    too many colours, over 60KB, or the tracer failed). The emblem is
    snapped to its <=8 main colours first, which is what makes the trace
    clean. Transparent areas are painted a key colour the logo doesn't use,
    traced as cut-out shapes, and the key-coloured shapes dropped."""
    if vtracer is None:
        return None
    arr = np.array(emblem)
    opaque = arr[..., 3] > 128
    if not opaque.any():
        return None
    px = arr[opaque][:, :3]
    strip = Image.fromarray(px.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    quant = np.array(strip.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")).reshape(-1, 3)
    if (np.linalg.norm(quant.astype(int) - px.astype(int), axis=1) > 40).mean() > 0.03:
        return None  # gradients / photo — not a flat logo
    palette = np.unique(quant, axis=0).astype(int)
    key = max(_KEY_COLOURS, key=lambda k: np.linalg.norm(palette - np.array(k), axis=1).min())
    flat = np.empty(arr.shape[:2] + (3,), dtype=np.uint8)
    flat[:] = key
    flat[opaque] = quant

    import subprocess, sys, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src, dest = Path(tmp) / "in.png", Path(tmp) / "out.svg"
        Image.fromarray(flat, "RGB").save(src, "PNG")
        try:
            done = subprocess.run([sys.executable, "-c", _TRACE_CODE, str(src), str(dest)],
                                  capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0 or not dest.exists():
            print(f"[logo trace] vtracer failed (exit {done.returncode})", flush=True)
            return None
        svg = dest.read_text(encoding="utf-8")

    # vtracer averages colours slightly, so match the key by distance —
    # never so loosely that a real logo colour would match too.
    key_tolerance = min(90.0, np.linalg.norm(palette - np.array(key), axis=1).min() / 2)

    def keep(match):
        fill = SVG_FILL_RE.search(match.group(0))
        if not fill:
            return match.group(0)
        return "" if np.linalg.norm(np.array(hex_rgb(fill.group(1))) - key) < key_tolerance else match.group(0)

    svg = _PATH_RE.sub(keep, svg)
    size = re.search(r'<svg[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', svg)
    svg = svg[svg.find("<svg"):]  # drop the XML declaration + generator comment
    if size:  # scalable: viewBox instead of a fixed pixel size
        svg = re.sub(r'<svg\b[^>]*>', f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size.group(1)} {size.group(2)}">', svg, count=1)
    fills = set(c.upper() for c in SVG_FILL_RE.findall(svg))
    if not fills or len(fills) > 8 or len(svg.encode("utf-8")) >= 60_000:
        return None
    return svg


def read_meta(out_dir):
    try:
        return json.loads((Path(out_dir) / "meta.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def extract_emblem(out_dir, client=None, model=None, force_vision=False, strict_bg=False, source="download"):
    """Run the pipeline on out_dir/original.png. Returns meta."""
    out_dir = Path(out_dir)
    img = Image.open(out_dir / "original.png")
    img.load()
    norm, bg_removed = normalise(img, strict=strict_bg)

    for name in ("emblem.png", "emblem.svg"):
        (out_dir / name).unlink(missing_ok=True)

    meta = {"type": "text_only", "confidence": 0.0, "method": "heuristic", "text": "", "needs_check": True,
            "vision_failed": False, "bbox": None, "strict_bg": bool(strict_bg), "bg_removed": bg_removed,
            "has_svg": False, "source": source, "updated_at": time.time()}
    if norm is None:
        (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        return meta

    layout = detect_layout(np.array(norm)[..., 3] > 32)
    # A fully opaque rectangle with no solid background is often not a logo
    # at all — og:image photos and site screenshots get picked up as
    # "logos" — and even when it is one, the crop is a guess.
    if not bg_removed and (np.array(norm)[..., 3] > 200).mean() > 0.95:
        if _looks_like_photo(norm):
            layout = {"type": "text_only", "bbox": None, "confidence": 0.3, "not_a_logo": True}
        else:
            layout["confidence"] = min(layout["confidence"], 0.6)
    meta["confidence"] = round(layout["confidence"], 2)
    result = {"type": layout["type"], "bbox": layout["bbox"], "text": "", "not_a_logo": layout.get("not_a_logo", False)}
    # Vision also runs on every detected emblem (not only uncertain crops),
    # because only it can tell a real mark from a generic stock symbol.
    if force_vision or layout["confidence"] < 0.7 or (layout["type"] != "text_only" and client is not None):
        if client is not None and model:
            try:
                result = vision_layout(client, model, norm)
                meta["method"] = "vision"
            except Exception as exc:  # noqa: BLE001 - keep the heuristic answer
                print(f"[logo vision] failed: {exc}", flush=True)
                meta["vision_failed"] = True
        else:
            meta["vision_failed"] = True

    if result["not_a_logo"]:  # a photo/screenshot has no emblem, whatever else was said
        result.update(type="text_only", bbox=None)
    meta.update(type=result["type"], text=result["text"], bbox=result["bbox"], not_a_logo=result["not_a_logo"])
    if result.get("confidence") is not None:
        meta["confidence"] = round(result["confidence"], 2)
    meta["generic_symbol"] = bool(result.get("generic_symbol"))
    # Suspect: a stock symbol, or low confidence it's their real logo. The
    # site then defaults to the generated monogram and the card says "check".
    meta["suspect"] = result["type"] != "text_only" and (meta["generic_symbol"] or meta["confidence"] < 0.6)
    meta["needs_check"] = meta["suspect"] or (meta["method"] == "heuristic" and meta["confidence"] < 0.5 and meta["vision_failed"])
    if result["type"] != "text_only" and result["bbox"]:
        x, y, w, h = result["bbox"]
        emblem = square_pad(norm.crop((x, y, x + w, y + h)))
        emblem.save(out_dir / "emblem.png", "PNG")
        svg = trace_svg(emblem)
        if svg:
            (out_dir / "emblem.svg").write_text(svg, encoding="utf-8")
            meta["has_svg"] = True
    (out_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return meta


# ---------------------------------------------------------------------------
# 2. Generated emblems (plain SVG, no AI)
# ---------------------------------------------------------------------------

# Lucide icons (ISC licence), 24x24, drawn with stroke="currentColor".
LUCIDE = {
    "zap": '<path d="M15.914 4a1.5 1.5 0 00-2.474-1.561l-9 9A1.5 1.5 0 005.5 14h4.002a.5.5 0 01.471.666L8.086 20a1.5 1.5 0 002.475 1.56l9-9A1.5 1.5 0 0018.5 10h-3.997a.5.5 0 01-.472-.667z"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"/>',
    "house": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "leaf": '<path d="M11 20a10 10 0 0010-10 25.9 25.9 0 00-1.04-7.281 1 1 0 00-1.755-.325C15.833 5.5 13 5.5 9.8 6.1A7 7 0 0011 20"/><path d="M2 21a5 5 0 012.911-4.544C7.613 15.212 8.351 15.24 11 13"/>',
    "hammer": '<path d="m15 12-9.373 9.373a1 1 0 0 1-3.001-3L12 9"/><path d="m18 15 4-4"/><path d="m21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172v-.344a2 2 0 0 0-.586-1.414l-1.657-1.657A6 6 0 0 0 12.516 3H9l1.243 1.243A6 6 0 0 1 12 8.485V10l2 2h1.172a2 2 0 0 1 1.414.586L18.5 14.5"/>',
    "paint-roller": '<rect width="16" height="6" x="2" y="2" rx="2"/><path d="M10 16v-2a2 2 0 0 1 2-2h8a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect width="4" height="6" x="8" y="16" rx="1"/>',
    "flame": '<path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4"/>',
    "star": '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>',
}

# (keywords matched against the trade, then the business name) -> icon
TRADE_ICONS = [
    (("electric", "spark", "solar", "ev charg"), "zap"),
    (("plumb", "drain", "bathroom"), "wrench"),
    (("roof", "gutter", "slat"), "house"),
    (("landscap", "garden", "tree", "lawn"), "leaf"),
    (("build", "construct", "carpent", "joiner", "renovat", "extension"), "hammer"),
    (("paint", "decorat"), "paint-roller"),
    (("heat", "gas", "boiler", "oil", "stove"), "flame"),
]
INITIALS_STOPWORDS = {
    "ltd", "limited", "the", "and", "of", "co", "company", "group", "services", "service", "solutions",
    "electrical", "electric", "electrics", "electrician", "electricians", "plumbing", "plumber", "plumbers",
    "heating", "roofing", "roofers", "roofer", "landscaping", "landscapes", "landscaper", "building",
    "builders", "builder", "construction", "painting", "painters", "painter", "decorating", "decorators",
    "contractor", "contractors", "contracting", "engineering", "engineers", "ireland", "irl", "teo",
}
FONT_FAMILIES = {"geist": "Geist", "inter": "Inter", "plus-jakarta-sans": "Plus Jakarta Sans", "dm-sans": "DM Sans",
                 # section-library style presets (site_library.PRESETS)
                 "heritage": "Brygada 1918", "industrial": "Big Shoulders Display",
                 "clean-local": "Bricolage Grotesque", "bold": "Epilogue"}


def trade_icon(trade, name=""):
    """Lucide icon key for a trade (falling back to the business name), or None."""
    for text in (trade or "", name or ""):
        low = text.lower()
        for keywords, icon in TRADE_ICONS:
            if any(k in low for k in keywords):
                return icon
    return None


def initials(name):
    words = [w for w in re.split(r"[^0-9A-Za-zÀ-ÿ']+", name or "") if w]
    kept = [w for w in words if w.lower().strip("'") not in INITIALS_STOPWORDS]
    letters = "".join(w[0] for w in (kept or words)[:2]).upper()
    return letters or "?"


def default_variant(trade, name=""):
    return 5 if trade_icon(trade, name) else 1


def _font_stack(font_key):
    first = FONT_FAMILIES.get((font_key or "").lower())
    families = ([first] if first else []) + ["Geist", "Inter", "Segoe UI", "Arial", "Helvetica"]
    return ", ".join(f"'{f}'" for f in dict.fromkeys(families)) + ", sans-serif"


def emblem_svg(variant, name, trade, color, font_key=None):
    """One generated emblem (1-6) as an SVG string, 100x100."""
    bg = color if re.fullmatch(r"#[0-9A-Fa-f]{6}", color or "") else "#1D4ED8"
    fg = contrast_fg(bg)
    text = initials(name)
    icon = LUCIDE[trade_icon(trade, name) or "star"]
    font = _font_stack(font_key).replace('"', "'")
    size = 44 if len(text) > 1 else 54

    def letters(cx, cy, fs):
        return (f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" font-family="{font}" '
                f'font-weight="800" font-size="{fs}" letter-spacing="-1" fill="{fg}">{text}</text>')

    def glyph(x, y, box, stroke, width=2):
        s = box / 24
        return (f'<g transform="translate({x} {y}) scale({s:.4f})" fill="none" stroke="{stroke}" stroke-width="{width}" '
                f'stroke-linecap="round" stroke-linejoin="round">{icon}</g>')

    circle = f'<circle cx="50" cy="50" r="48" fill="{bg}"/>'
    square = f'<rect x="2" y="2" width="96" height="96" rx="22" fill="{bg}"/>'
    shield = f'<path d="M50 3 L91 15 V46 C91 71 73 88 50 97 C27 88 9 71 9 46 V15 Z" fill="{bg}"/>'
    body = {
        1: circle + letters(50, 51, size),
        2: square + letters(50, 51, size),
        3: shield + letters(50, 47, size - 6),
        4: circle + glyph(23, 23, 54, fg),
        5: square + glyph(23, 23, 54, fg),
        6: (f'<circle cx="45" cy="45" r="43" fill="{bg}"/>' + letters(45, 46, size - 4)
            + f'<circle cx="78" cy="78" r="19" fill="{fg}" stroke="{bg}" stroke-width="3"/>'
            + glyph(68, 68, 20, bg, 2.4)),
    }[variant]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">{body}</svg>'


def generate_emblems(out_dir, name, trade, color, font_key=None):
    gen = Path(out_dir) / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    for v in range(1, 7):
        (gen / f"{v}.svg").write_text(emblem_svg(v, name, trade, color, font_key), encoding="utf-8")


# ---------------------------------------------------------------------------
# Optional AI variants + SVG safety / recolouring
# ---------------------------------------------------------------------------

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
_UNSAFE_TAGS = {"script", "foreignObject", "image", "style", "iframe", "a", "audio", "video", "animate",
                "set", "animateTransform", "animateMotion"}


def sanitize_svg(text):
    """Parse an SVG and strip anything active or external. Returns the
    cleaned SVG string, or None if it isn't a valid SVG."""
    if not isinstance(text, str) or len(text) > 200_000 or "<!ENTITY" in text or "<!DOCTYPE" in text:
        return None
    try:
        root = ET.fromstring(text.strip())
    except ET.ParseError:
        return None
    if root.tag not in ("svg", f"{{{SVG_NS}}}svg"):
        return None
    for parent in list(root.iter()):
        for child in list(parent):
            if child.tag.split("}")[-1] in _UNSAFE_TAGS:
                parent.remove(child)
    for el in root.iter():
        if isinstance(el.tag, str) and not el.tag.startswith("{"):
            el.tag = f"{{{SVG_NS}}}{el.tag}"
        for attr in list(el.attrib):
            local = attr.split("}")[-1].lower()
            value = el.attrib[attr]
            if local.startswith("on") or (local == "href" and not value.startswith("#")) or "url(http" in value.replace(" ", "").lower():
                del el.attrib[attr]
    if "viewBox" not in root.attrib:
        root.set("viewBox", "0 0 100 100")
    return ET.tostring(root, encoding="unicode")


def ai_emblems(client, model, name, trade, colors):
    """One Claude call for 3 simple flat emblems. Returns only the ones
    that parse as SVG."""
    palette = ", ".join(colors[:3]) if colors else "the business's brand colours"
    prompt = (
        f'Design 3 simple, flat SVG emblems (logo marks) for a {trade or "trade"} business called "{name}". '
        f"Rules: no text or letters; at most 3 colours ({palette}); viewBox=\"0 0 100 100\"; basic shapes and "
        "paths only; each must be a valid standalone SVG with xmlns. Reply with a JSON array of 3 SVG strings "
        "and nothing else."
    )
    resp = client.messages.create(model=model, max_tokens=4000, messages=[{"role": "user", "content": prompt}])
    _log_usage("logo ai variants", resp)
    items = _json_from_text("".join(getattr(b, "text", "") for b in resp.content), "[", "]")
    svgs = [sanitize_svg(s) for s in items if isinstance(s, str)]
    return [s for s in svgs if s][:3]


_COLOR_ATTR_RE = re.compile(r'\b(fill|stroke|stop-color)="(?!none|transparent|url\()([^"]+)"', re.I)
_COLOR_STYLE_RE = re.compile(r'\b(fill|stroke|stop-color)\s*:\s*(?!none|transparent|url\()([^;"]+)', re.I)


def _silhouette(svg, color):
    svg = _COLOR_ATTR_RE.sub(lambda m: f'{m.group(1)}="{color}"', svg)
    return _COLOR_STYLE_RE.sub(lambda m: f"{m.group(1)}:{color}", svg)


def _backdrop(root):
    """The first drawn shape, if it's a rect/circle covering most of the
    viewBox — the emblem's tile, as opposed to the mark drawn on it."""
    try:
        _, _, vw, vh = (float(v) for v in re.split(r"[\s,]+", root.get("viewBox", "").strip()))
    except ValueError:
        return None
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("svg", "g", "defs", "title", "desc"):
            continue
        if (el.get("fill") or "").lower() in ("none", "transparent"):
            return None  # an outline, not a tile
        try:
            if tag == "rect" and float(el.get("width", 0)) >= 0.8 * vw and float(el.get("height", 0)) >= 0.8 * vh:
                return el
            if tag == "circle" and float(el.get("r", 0)) >= 0.4 * min(vw, vh):
                return el
        except ValueError:
            pass
        return None  # the first shape isn't a tile
    return None


def recolor_svg(svg, color):
    """Recolour an SVG emblem to one colour. If it's a mark on a tile
    (backdrop rect/circle), the tile takes the colour and the mark gets the
    contrasting white/near-black, so it stays visible; otherwise every
    fill/stroke becomes the colour (a silhouette)."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return _silhouette(svg, color)
    tile = _backdrop(root)
    if tile is None:
        return _silhouette(svg, color)
    fg = contrast_fg(color)
    parents = {child: parent for parent in root.iter() for child in parent}
    drawable = {"path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "text"}
    tile_fill = (tile.get("fill") or "").lower()
    for el in root.iter():
        # the tile, and details drawn in the tile's own colour (cut-outs), take the colour
        same_as_tile = tile_fill and (el.get("fill") or "").lower() == tile_fill
        paint = color if el is tile or same_as_tile else fg
        if el.tag.split("}")[-1] in drawable and not el.get("fill") and "fill" not in (el.get("style") or ""):
            node, inherited = parents.get(el), False
            while node is not None and not inherited:
                inherited = bool(node.get("fill"))
                node = parents.get(node)
            if not inherited:  # default black fill — would vanish on a dark tile
                el.set("fill", paint)
        for attr in ("fill", "stroke", "stop-color"):
            value = el.get(attr)
            if value and value.lower() not in ("none", "transparent") and not value.startswith("url("):
                el.set(attr, paint)
        if el.get("style"):
            el.set("style", _COLOR_STYLE_RE.sub(lambda m: f"{m.group(1)}:{paint}", el.get("style")))
    return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
# 4. Favicon + share image
# ---------------------------------------------------------------------------

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
_REGULAR_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _font(size, bold=True):
    for path in (_FONT_CANDIDATES if bold else _REGULAR_CANDIDATES):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _dominant_rgb(img):
    arr = np.array(img)
    px = arr[arr[..., 3] > 128][:, :3]
    return tuple(int(v) for v in np.median(px, axis=0)) if len(px) else (0, 0, 0)


def write_favicons(emblem, brand_color, ico_path, apple_path, on_brand_square):
    """favicon.ico (16/32/48, transparent) and a 180px apple touch icon.
    iOS paints transparent icons black, so the apple icon sits on a square:
    brand colour for generated emblems, and for extracted ones when they
    contrast with it (else white)."""
    ico = square_pad(emblem, pad=0.04, max_side=256).resize((256, 256), Image.LANCZOS)
    ico.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    bg = hex_rgb(brand_color)
    if not on_brand_square:
        dom = _dominant_rgb(emblem)
        if sum((a - b) ** 2 for a, b in zip(dom, bg)) ** 0.5 < 110:
            bg = (255, 255, 255)
    tile = Image.new("RGBA", (180, 180), bg + (255,))
    mark = emblem.resize((150, 150) if on_brand_square else (132, 132), Image.LANCZOS)
    tile.alpha_composite(mark, ((180 - mark.width) // 2, (180 - mark.height) // 2))
    tile.convert("RGB").save(apple_path, "PNG")


def _wrap(draw, text, font, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def write_og_image(emblem, name, town, brand_color, out_path):
    """1200x630: brand-colour background, emblem on a white tile at the
    left (240px), business name large on the right with the town below."""
    W, H = 1200, 630
    bg = hex_rgb(brand_color)
    fg = hex_rgb(contrast_fg(brand_color))
    img = Image.new("RGBA", (W, H), bg + (255,))
    draw = ImageDraw.Draw(img)

    tile_x, tile_y, tile = 90, (H - 300) // 2, 300
    draw.rounded_rectangle((tile_x, tile_y, tile_x + tile, tile_y + tile), radius=44, fill=(255, 255, 255, 255))
    mark = emblem.resize((240, 240), Image.LANCZOS)
    img.alpha_composite(mark, (tile_x + 30, tile_y + 30))

    left, max_w = 460, W - 460 - 80
    for size in (86, 76, 66, 58, 50, 44):
        font = _font(size)
        lines = _wrap(draw, name, font, max_w)
        if len(lines) <= 3 and all(draw.textlength(l, font=font) <= max_w for l in lines):
            break
    lines = lines[:3]
    town_font = _font(36, bold=False)
    line_h = int(size * 1.12)
    block_h = line_h * len(lines) + (24 + 40 if town else 0)
    y = (H - block_h) // 2
    for line in lines:
        draw.text((left, y), line, font=font, fill=fg + (255,))
        y += line_h
    if town:
        draw.text((left, y + 24), town, font=town_font, fill=fg + (200,))
    img.convert("RGB").save(out_path, "PNG", optimize=True)
