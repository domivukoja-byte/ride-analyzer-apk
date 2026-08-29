"""Ride analyzer core.

Verbatim port of the analysis logic from final_gpx_pydroid.py, with the
analyze() function refactored to return a structured dict instead of printing
so the UI can render it.
"""

import math
import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from bisect import bisect_left, bisect_right
from traceback import format_exc


# ---- time zone (Croatia local, +02 in September) ----
CEST = timezone(timedelta(hours=2))


# ---- physics constants (defaults; the UI can override via settings) ----
RIDER_WEIGHT_KG  = 70
BIKE_WEIGHT_KG   = 10
RIDER_HEIGHT_CM  = 178
RIDER_AGE        = 23
RIDER_MALE       = True

BMR_KCAL = (10 * RIDER_WEIGHT_KG + 6.25 * RIDER_HEIGHT_CM
            - 5 * RIDER_AGE + (5 if RIDER_MALE else -161))

CRR              = 0.004
CDA              = 0.45
RHO              = 1.225
DRIVETRAIN_ETA   = 0.97
EFF_GROSS        = 0.22
EPOC_FACTOR      = 0.10
KM_SPLIT         = 1000
ELE_SMOOTH       = 50
ELE_MAX_M        = 2500

# ---- pause detection ----
SLOW_V     = 1.0
MIN_STOP_S = 8
JUMP_M     = 30.0
MERGE_S    = 45
GLUE_S     = 120
GLUE_M     = 150
PAUSE_LOC_S = 120
REPORT_MIN_S = 60


# ---- known places (works offline) ----
KNOWN_PLACES = [
    ("Home", 45.7885, 16.0057, 45.7902, 16.0098),
    ("Gradec", 45.8005, 15.9943, 45.8019, 15.9971),
    ("Sljeme", 45.8978, 15.9452, 45.9007, 15.9500),
    ("Zagreb, Croatia", 45.7619, 15.8792, 45.8477, 16.0677),
    ("Varaždin, Croatia", 46.2902, 16.3214, 46.3195, 16.3652),
    ("Ogulin, Croatia", 45.2569, 15.2105, 45.2750, 15.2465),
    ("Senj, Croatia", 44.9806, 14.8953, 44.9961, 14.9153),
    ("Nagykanizsa, Hungary", 46.4417, 16.9731, 46.4876, 17.0458),
    ("Budapest, Hungary", 47.3622, 18.9009, 47.5746, 19.2138),
]


def _hav(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _check_saved_places(lat, lon):
    for name, mn_lat, mn_lon, mx_lat, mx_lon in KNOWN_PLACES:
        if mn_lat < lat < mx_lat and mn_lon < lon < mx_lon:
            return f"{name} ({lat:.4f}, {lon:.4f})"
    return None


# ---- reverse geocoding (Nominatim, with cache) ----
_geo_cache = {}
_geo_online = True


def reverse_geocode(lat, lon, silent=True):
    """Return nearest town/city; appends precise coords. Falls back to
    coordinates only when offline (Nominatim unreachable).

    silent=True swallows prints; the UI handles its own error display.
    """
    global _geo_online
    saved = _check_saved_places(lat, lon)
    if saved:
        return saved
    if not _geo_online:
        return f"{lat:.4f}, {lon:.4f}"
    key = (round(lat, 3), round(lon, 3))
    if key in _geo_cache:
        place = _geo_cache[key]
    else:
        try:
            q = urllib.parse.urlencode({"lat": lat, "lon": lon, "zoom": 14,
                                        "format": "jsonv2", "accept-language": "en"})
            req = urllib.request.Request(
                "https://nominatim.openstreetmap.org/reverse?" + q,
                headers={"User-Agent": "ride-analyzer-android/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
            addr = data.get("address", {})
            place = (addr.get("village") or addr.get("town") or addr.get("city")
                     or addr.get("municipality") or addr.get("hamlet") or addr.get("suburb"))
            country = addr.get("country", "")
            if place and country:
                place = f"{place}, {country}"
            elif not place:
                dn = data.get("display_name", "")
                place = ", ".join(p.strip() for p in dn.split(",")[:3]) or None
            _geo_cache[key] = place
            time.sleep(1.1)  # 1 req/s
        except Exception:
            _geo_online = False
            if not silent:
                print("  (no internet - showing coordinates instead of place names)")
            return f"{lat:.4f}, {lon:.4f}"
    if not place:
        return f"{lat:.4f}, {lon:.4f}"
    return f"{place} ({lat:.4f}, {lon:.4f})"


def _lname(tag):
    return tag.rsplit('}', 1)[-1]


def _hm(sec):
    h = int(sec // 3600)
    m = int(round((sec % 3600) / 60))
    if m == 60:
        h += 1
        m = 0
    return f"{h}:{m:02d}"


def _fmt_time(dt):
    return dt.astimezone(CEST).strftime("%H:%M:%S")


def apply_settings(settings):
    """Update physics constants from a settings dict (from settings_store).

    settings keys (defaults shown): rider_weight_kg=70, bike_weight_kg=10,
    rider_height_cm=178, rider_age=23, rider_male=True, crr=0.004, cda=0.45,
    epoc_factor=0.10, ele_smooth=50, ele_max_m=2500.
    """
    global RIDER_WEIGHT_KG, BIKE_WEIGHT_KG, RIDER_HEIGHT_CM, RIDER_AGE
    global RIDER_MALE, BMR_KCAL, CRR, CDA, EPOC_FACTOR, ELE_SMOOTH, ELE_MAX_M
    RIDER_WEIGHT_KG = float(settings.get("rider_weight_kg", 70))
    BIKE_WEIGHT_KG  = float(settings.get("bike_weight_kg", 10))
    RIDER_HEIGHT_CM = float(settings.get("rider_height_cm", 178))
    RIDER_AGE       = int(settings.get("rider_age", 23))
    RIDER_MALE      = bool(settings.get("rider_male", True))
    BMR_KCAL = (10 * RIDER_WEIGHT_KG + 6.25 * RIDER_HEIGHT_CM
                - 5 * RIDER_AGE + (5 if RIDER_MALE else -161))
    CRR         = float(settings.get("crr", 0.004))
    CDA         = float(settings.get("cda", 0.45))
    EPOC_FACTOR = float(settings.get("epoc_factor", 0.10))
    ELE_SMOOTH  = int(settings.get("ele_smooth", 50))
    ELE_MAX_M   = float(settings.get("ele_max_m", 2500))


def get_default_settings():
    return {
        "rider_weight_kg": RIDER_WEIGHT_KG,
        "bike_weight_kg": BIKE_WEIGHT_KG,
        "rider_height_cm": RIDER_HEIGHT_CM,
        "rider_age": RIDER_AGE,
        "rider_male": RIDER_MALE,
        "crr": CRR,
        "cda": CDA,
        "epoc_factor": EPOC_FACTOR,
        "ele_smooth": ELE_SMOOTH,
        "ele_max_m": ELE_MAX_M,
    }


def list_gpx_files(folder):
    """Return sorted list of .gpx filenames in folder. None if unreadable."""
    try:
        return sorted(f for f in os.listdir(folder) if f.lower().endswith(".gpx"))
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
        return None


def analyze(path):
    """Analyze a single GPX file. Returns a dict (or raises on unrecoverable
    parse error) ready to be rendered by the UI.

    The dict has the following keys:
      ok: bool
      error: str or None
      filename: str
      has_ele: bool
      start: str (HH:MM:SS local)
      end: str (HH:MM:SS local)
      elapsed_hm: str
      distance_km: float
      total_s: float
      ride_s: float
      riding_min: float
      avg_riding_kmh: float
      gain_m, loss_m, net_m: float or None
      start_loc: str
      end_loc: str
      n_stops: int
      stop_min: float
      n_micro: int
      n_dropout: int
      n_end_artifact: int
      pauses: list of {start, end, dur_min, loc}
      calories: {full, gross, epoc, bmr, delta, n_chunks, epoc_factor}
    """
    try:
        apply_settings(_current_settings())
        tree = ET.parse(path)
    except Exception as ex:
        return {"ok": False, "error": f"Could not parse: {ex}",
                "filename": os.path.basename(path)}

    pts = []
    for trkpt in tree.getroot().iter():
        if _lname(trkpt.tag) != "trkpt":
            continue
        t = s = e = None
        for child in trkpt:
            n = _lname(child.tag)
            if n == "time":
                t = child.text
            elif n == "speed":
                s = child.text
            elif n == "ele":
                e = child.text
        if t is None:
            continue
        pts.append((datetime.fromisoformat(t.replace("Z", "+00:00")),
                    float(trkpt.get("lat")), float(trkpt.get("lon")),
                    float(s) if s is not None else None,
                    float(e) if e is not None else None))
    pts.sort(key=lambda p: p[0])

    if not pts:
        return {"ok": False, "error": "No trkpts with <time> in this file",
                "filename": os.path.basename(path)}

    t0, t1 = pts[0][0], pts[-1][0]
    total_s = (t1 - t0).total_seconds()
    dist_total = sum(_hav(pts[i][1], pts[i][2], pts[i + 1][1], pts[i + 1][2])
                     for i in range(len(pts) - 1))

    def dist(i, j):
        return _hav(pts[i][1], pts[i][2], pts[j][1], pts[j][2])

    # unified non-movement detection
    events = []
    for i in range(len(pts) - 1):
        dt = (pts[i + 1][0] - pts[i][0]).total_seconds()
        if dt >= MIN_STOP_S:
            d = dist(i, i + 1)
            if d < JUMP_M:
                events.append((pts[i][0], pts[i + 1][0], "",
                               pts[i][1], pts[i][2], pts[i + 1][1], pts[i + 1][2]))

    run = None
    for i in range(1, len(pts)):
        dt = (pts[i][0] - pts[i - 1][0]).total_seconds()
        d = dist(i - 1, i)
        if dt < MIN_STOP_S and d / max(dt, 1e-9) < SLOW_V:
            if run:
                run[1], run[2], run[5], run[6] = pts[i][0], run[2] + d, pts[i][1], pts[i][2]
            else:
                run = [pts[i - 1][0], pts[i][0], d,
                       pts[i - 1][1], pts[i - 1][2], pts[i][1], pts[i][2]]
        else:
            if run:
                events.append((run[0], run[1], "",
                               run[3], run[4], run[5], run[6]))
            run = None
    if run:
        events.append((run[0], run[1], "", run[3], run[4], run[5], run[6]))

    # merge
    events.sort(key=lambda e: e[0])
    merged = []
    for e in events:
        if merged:
            m = merged[-1]
            gap = (e[0] - m[1]).total_seconds()
            d_between = _hav(m[5], m[6], e[3], e[4])
            if gap <= MERGE_S or (gap <= GLUE_S and d_between < GLUE_M):
                parts = []
                for p in (m[2] + "; " + e[2]).split(";"):
                    p = p.strip()
                    if p and p not in parts:
                        parts.append(p)
                merged[-1] = (m[0], max(m[1], e[1]), "; ".join(parts),
                              m[3], m[4], e[5], e[6])
                continue
        merged.append(list(e))

    stops = [e for e in merged if (e[1] - e[0]).total_seconds() >= MIN_STOP_S]
    end_artifact = [e for e in stops if (t1 - e[1]).total_seconds() <= 15]
    stops = [e for e in stops if e not in end_artifact]

    n_micro = sum(1 for e in stops if (e[1] - e[0]).total_seconds() < REPORT_MIN_S)
    n_end_artifact = len(end_artifact)
    stops = [e for e in stops if (e[1] - e[0]).total_seconds() >= REPORT_MIN_S]

    n_dropout = sum(1 for i in range(len(pts) - 1)
                    if (pts[i + 1][0] - pts[i][0]).total_seconds() >= MIN_STOP_S
                    and dist(i, i + 1) >= JUMP_M)

    times = [p[0] for p in pts]

    # build pause list with location for long pauses
    pauses = []
    for ev in stops:
        a, b = ev[0], ev[1]
        dur_s = (b - a).total_seconds()
        loc = ""
        if dur_s >= PAUSE_LOC_S:
            i = bisect_right(times, a) - 1
            if i >= 0:
                loc = reverse_geocode(pts[i][1], pts[i][2])
        pauses.append({
            "start": _fmt_time(a),
            "end": _fmt_time(b),
            "dur_min": round(dur_s / 60, 1),
            "loc": loc,
        })

    stop_s = sum((ev[1] - ev[0]).total_seconds() for ev in stops)
    ride_s = total_s - stop_s

    # elevation
    has_ele = any(p[4] is not None for p in pts)
    gain = loss = 0.0
    if has_ele:
        clean = [p[4] if (p[4] is not None and p[4] <= ELE_MAX_M) else None
                 for p in pts]
        if len(clean) > ELE_SMOOTH * 2:
            half = ELE_SMOOTH
            smoothed = []
            for i in range(len(clean)):
                lo, hi = max(0, i - half), min(len(clean), i + half + 1)
                window = [e for e in clean[lo:hi] if e is not None]
                smoothed.append(sum(window) / len(window) if window else None)
        else:
            smoothed = clean
        prev_e = None
        for e in smoothed:
            if e is None:
                continue
            if prev_e is not None:
                d = e - prev_e
                if d > 0:
                    gain += d
                elif d < 0:
                    loss -= d
            prev_e = e
    net = (gain - loss) if has_ele else None

    # calorie chunks
    G = 9.8067
    M_TOT_KG = RIDER_WEIGHT_KG + BIKE_WEIGHT_KG
    BMR_H = BMR_KCAL / 24.0

    def chunk_mech_joules(m_chunk, t_chunk, dE_chunk):
        v = m_chunk / t_chunk
        grade = max(-0.25, min(0.25, dE_chunk / m_chunk if has_ele else 0.0))
        theta = math.atan(grade)
        f_grav = M_TOT_KG * G * math.sin(theta)
        f_roll = CRR * M_TOT_KG * G * math.cos(theta)
        f_aero = 0.5 * RHO * CDA * v * v
        p_wheel = max(0.0, v * (f_grav + f_roll + f_aero))
        return p_wheel * t_chunk / DRIVETRAIN_ETA

    mech_joules = 0.0
    chunk_m = chunk_t = chunk_dE = 0.0
    chunk_e0 = None
    n_chunks = 0
    for i in range(len(pts) - 1):
        dm = dist(i, i + 1)
        dt = (pts[i + 1][0] - pts[i][0]).total_seconds()
        if dt <= 0:
            continue
        if chunk_e0 is None:
            chunk_e0 = pts[i][4]
        chunk_m += dm
        chunk_t += dt
        if pts[i + 1][4] is not None and chunk_e0 is not None:
            chunk_dE += (pts[i + 1][4] - chunk_e0)
            chunk_e0 = pts[i + 1][4]
        elif pts[i + 1][4] is not None:
            chunk_e0 = pts[i + 1][4]
        if chunk_m >= KM_SPLIT:
            if chunk_t > 0 and chunk_m > 0:
                mech_joules += chunk_mech_joules(chunk_m, chunk_t, chunk_dE)
                n_chunks += 1
            chunk_m = chunk_t = chunk_dE = 0.0
            chunk_e0 = pts[i + 1][4]
    if chunk_m > 0 and chunk_t > 0:
        mech_joules += chunk_mech_joules(chunk_m, chunk_t, chunk_dE)
        n_chunks += 1

    mech_kcal = mech_joules / 4184.0
    gross_kcal = mech_kcal / EFF_GROSS
    bmr_kcal = BMR_H * (ride_s / 3600.0)
    epoc_kcal = gross_kcal * EPOC_FACTOR
    full_ride_kcal = gross_kcal + epoc_kcal
    delta_vs_rest = full_ride_kcal - bmr_kcal

    s_loc = reverse_geocode(pts[0][1], pts[0][2])
    e_loc = reverse_geocode(pts[-1][1], pts[-1][2])

    return {
        "ok": True,
        "error": None,
        "filename": os.path.basename(path),
        "has_ele": has_ele,
        "start": _fmt_time(t0),
        "end": _fmt_time(t1),
        "elapsed_hm": _hm(total_s),
        "distance_km": dist_total / 1000.0,
        "total_s": total_s,
        "ride_s": ride_s,
        "riding_min": ride_s / 60.0,
        "avg_riding_kmh": (dist_total * 3.6 / ride_s) if ride_s > 0 else 0.0,
        "gain_m": gain if has_ele else None,
        "loss_m": loss if has_ele else None,
        "net_m": net,
        "start_loc": s_loc or "",
        "end_loc": e_loc or "",
        "n_stops": len(stops),
        "stop_min": stop_s / 60.0,
        "n_micro": n_micro,
        "n_dropout": n_dropout,
        "n_end_artifact": n_end_artifact,
        "pauses": pauses,
        "calories": {
            "full": full_ride_kcal,
            "gross": gross_kcal,
            "epoc": epoc_kcal,
            "bmr": bmr_kcal,
            "delta": delta_vs_rest,
            "n_chunks": n_chunks,
            "epoc_factor": 1 + EPOC_FACTOR,
        },
    }


# ---- internal: get current settings for analyze() ----
_settings_provider = None

def set_settings_provider(fn):
    """Inject a callable returning the current settings dict.
    Called by main.py at startup. Defaults to module-level constants."""
    global _settings_provider
    _settings_provider = fn

def _current_settings():
    if _settings_provider is None:
        return get_default_settings()
    try:
        s = _settings_provider()
        return s if isinstance(s, dict) else get_default_settings()
    except Exception:
        return get_default_settings()
