"""Parameter sweep for hazard calibration targets."""
import math
import sys
sys.path.insert(0, r"d:\Work\Projects\ResillienceAI\backend")

# Baseline component scores from live diagnostic (2026-07-04)
BASELINE = {
    "Singapore": {"event": 0.0, "fault_d": 120.0, "soil_lsi": 0.021, "n": 0},
    "Bangkok": {"event": 0.0, "fault_d": 120.0, "soil_lsi": 0.021, "n": 0},
    "Yangon": {"event_raw_sum": 6.2, "fault_d": 120.0, "soil_lsi": 0.021, "n": 47},
    "Mandalay": {"event_raw_sum": 8.5, "fault_d": 120.0, "soil_lsi": 0.021, "n": 94},
    "Tokyo": {"event_raw_sum": 12.0, "fault_d": 120.0, "soil_lsi": 0.934, "n": 1668},
    "San Francisco": {"event_raw_sum": 9.5, "fault_d": 10.72, "soil_lsi": 0.934, "n": 122},
}

TARGETS = {
    "Singapore": (10, 25),
    "Bangkok": (20, 40),
    "Yangon": (45, 60),
    "Mandalay": (55, 70),
    "Tokyo": (80, 95),
    "San Francisco": (75, 90),
}


def event_score(raw_sum, cap, rate):
    return cap * (1.0 - math.exp(-rate * raw_sum))


def fault_score(d, cap, decay):
    return cap * math.exp(-max(0.0, d) / decay)


def soil_score(lsi, cap):
    return cap * min(1.0, max(0.0, lsi))


def final_score(event, fault, soil, divisor):
    raw = event + fault + soil
    return 100.0 * (1.0 - math.exp(-raw / divisor))


def score_city(city, params):
    b = BASELINE[city]
    raw_sum = b.get("event_raw_sum", 0.0)
    ev = event_score(raw_sum, params["event_cap"], params["event_rate"])
    flt = fault_score(b["fault_d"], params["fault_cap"], params["fault_decay"])
    s = soil_score(b["soil_lsi"], params["soil_cap"])
    return final_score(ev, flt, s, params["final_div"])


best = None
best_miss = 999

for event_cap in [28, 30, 32]:
    for event_rate in [0.28, 0.32, 0.35, 0.38]:
        for fault_cap in [22, 24, 26]:
            for fault_decay in [42, 48, 55]:
                for final_div in [38, 42, 46, 50]:
                    params = {
                        "event_cap": event_cap,
                        "event_rate": event_rate,
                        "fault_cap": fault_cap,
                        "fault_decay": fault_decay,
                        "soil_cap": 20.0,
                        "final_div": final_div,
                    }
                    miss = 0
                    for city, (lo, hi) in TARGETS.items():
                        s = score_city(city, params)
                        if s < lo:
                            miss += lo - s
                        elif s > hi:
                            miss += s - hi
                    if miss < best_miss:
                        best_miss = miss
                        best = params.copy()
                        best_scores = {c: round(score_city(c, params), 1) for c in TARGETS}

print("Best params:", best)
print("Miss total:", best_miss)
for city in TARGETS:
    lo, hi = TARGETS[city]
    s = best_scores[city]
    ok = "OK" if lo <= s <= hi else "MISS"
    print(f"  {city:15} {s:5.1f}  target [{lo}-{hi}]  {ok}")
