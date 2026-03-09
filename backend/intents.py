import re
from dataclasses import dataclass
from typing import Optional

YEAR_RX = re.compile(r"\b(20\d{2})\b", re.I)

@dataclass
class ParsedIntent:
    intent: str          # sip_summary | latest_nav | nav_trend | sip_projection | explain_general | unknown
    fund_name: Optional[str] = None
    year: Optional[int] = None
    compare_to_last_year: bool = False

def parse_intent(q: str) -> ParsedIntent:
    ql = q.lower().strip()
    intent = "unknown"

    if "sip" in ql and ("total" in ql or "contribution" in ql):
        intent = "sip_summary"
    elif "latest" in ql and "nav" in ql:
        intent = "latest_nav"
    elif "nav" in ql and ("trend" in ql or "last" in ql or "past" in ql):
        intent = "nav_trend"
    elif any(w in ql for w in ["project", "projection", "future value", "fv"]):
        intent = "sip_projection"
    elif "what is nav" in ql or ("what" in ql and "nav" in ql):
        intent = "explain_general"

    year = None
    m = YEAR_RX.search(q)
    if m:
        year = int(m.group(1))

    compare = bool(re.search(r"\b(vs|versus|compare|ahead|behind)\b", ql, re.I))

    # crude fund capture: after 'for' or quoted
    fund_name = None
    m = re.search(r'for\s+([A-Za-z0-9 \-\&]+)', q, re.I)
    if m:
        fund_name = m.group(1).strip().rstrip("?.,")
    else:
        m2 = re.search(r'"([^"]+)"', q)
        if m2:
            fund_name = m2.group(1).strip()

    return ParsedIntent(intent=intent, fund_name=fund_name, year=year, compare_to_last_year=compare)
