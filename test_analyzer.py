"""Sanity test: run analyzer.analyze() against a few real GPX files and
print the key numbers. Run with `python test_analyzer.py` to confirm the
ported analyzer produces sensible values.
"""
import os
import sys

import analyzer

CANDIDATES_WIN = r"C:\Users\Dominik\Desktop\Backups mobitel\Russian Topo Maps\Russian Topo Maps"
CANDIDATES_LIN = "/storage/emulated/0/Download/Russian Topo Maps"


def find_gpx():
    """Find any .gpx files in known locations."""
    import glob
    paths = []
    for base in [CANDIDATES_WIN, CANDIDATES_LIN, r"C:\Claude"]:
        if not os.path.isdir(base):
            continue
        for ext in ("*.gpx", "*.GPX"):
            paths.extend(glob.glob(os.path.join(base, ext)))
    return sorted(set(paths))


def main():
    files = find_gpx()
    if not files:
        print("No .gpx files found in known locations; skipping test.")
        return 0
    failures = 0
    for path in files:
        print(f"\n=== {os.path.basename(path)} ===")
        try:
            r = analyzer.analyze(path)
        except Exception as ex:
            print(f"  ERROR: {ex}")
            failures += 1
            continue
        if not r["ok"]:
            print(f"  ERROR: {r['error']}")
            failures += 1
            continue
        c = r["calories"]
        print(f"  Trip: {r['start']}-{r['end']} ({r['elapsed_hm']} h, {r['distance_km']:.2f} km)")
        print(f"  Riding: {r['riding_min']:.1f} min, avg {r['avg_riding_kmh']:.1f} km/h")
        if r["has_ele"]:
            print(f"  Elevation: gain {r['gain_m']:.0f} m, loss {r['loss_m']:.0f} m, "
                  f"net {r['net_m']:+.0f} m")
        print(f"  Calories: {c['full']:.0f} kcal "
              f"(gross {c['gross']:.0f} + EPOC {c['epoc']:.0f}, "
              f"BMR {c['bmr']:.0f}, delta {c['delta']:.0f}, "
              f"{c['n_chunks']} chunks)")
        print(f"  Pauses: {r['n_stops']} ({r['stop_min']:.1f} min total)")
        print(f"  Track: {r['start_loc']}  ->  {r['end_loc']}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
