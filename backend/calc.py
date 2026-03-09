def yoy_pct(curr: float, prev: float):
    if prev is None or prev == 0:
        return None
    return round(100.0 * (curr - prev) / prev, 2)

def sip_future_value(monthly: float, years: int, annual_rate_pct: float):
    r = (annual_rate_pct / 100.0) / 12.0
    n = years * 12
    fv = 0.0
    for _ in range(n):
        fv = (fv + monthly) * (1 + r)
    return round(fv, 2)
