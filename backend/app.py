from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, ValidationError, field_validator
from intents import parse_intent
from db import init_db, seed_db, get_user_by_email, fund_id_by_name
from calc import sip_future_value
from session_mem import SESSION
from llm import explain_answer
from datetime import datetime
import threading
import json
import os
import time
import requests

# -------------------------------
# Config
# -------------------------------
EVAL_MODE = os.getenv("EVAL_MODE", "hybrid")            # "hybrid" or "baseline"
SYSTEM_PROMPT = (
    "You are FinSight, a concise finance assistant.\n"
    "- Use user-specific facts only when provided by tools.\n"
    "- If a database lookup is needed, output a JSON plan (see spec) and wait for results.\n"
    "- If no lookup is needed, answer directly.\n"
    "- Be brief (1–4 sentences). No financial advice; speak generally.\n"
    "Output format:\n"
    "{ \"need_db\": true|false, \"intent\": \"...\", \"slots\": { ... }, \"question_restate\": \"...\" }\n"
)

# -------------------------------
# App
# -------------------------------
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["http://localhost:5173"]}})

# -------------------------------
# Models
# -------------------------------
class LoginIn(BaseModel):
    email: str
    password: str

class ChatIn(BaseModel):
    user_id: int | str
    query: str

class SipCalcIn(BaseModel):
    monthly: float
    years: int
    rate: float  # annual %

    @field_validator("monthly", "years", "rate")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("must be >= 0")
        return v

# -------------------------------
# Routes
# -------------------------------
@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = LoginIn(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"message": "Invalid payload", "errors": e.errors()}), 400

    u = get_user_by_email(data.email)
    if not u or data.password != "demo":  # demo-only auth
        return jsonify({"message": "Invalid credentials"}), 401
    return jsonify({"user": {"id": u["id"], "email": u["email"]}}), 200


@app.route("/calculate/sip", methods=["POST"])
def calc_sip():
    try:
        data = SipCalcIn(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"message": "Invalid payload", "errors": e.errors()}), 400

    fv = sip_future_value(data.monthly, data.years, data.rate)
    out = {"monthly": data.monthly, "years": data.years, "rate": data.rate, "future_value": fv}

    # In hybrid, we can ask LLM to phrase the projection; in baseline we keep it templated in explain_answer
    txt, used_llm, llm_err = explain_answer(
        "sip projection",
        {"type": "sip_projection", "monthly": data.monthly, "years": data.years, "rate": data.rate, "fv": fv},
        use_llm=(EVAL_MODE == "hybrid")
    )
    return jsonify({"result": out, "answer_text": txt,
                    "meta": {"mode": EVAL_MODE, "llm_used": used_llm, "llm_error": llm_err}})


@app.route("/chat", methods=["POST"])
def chat():
    t0 = time.time()

    # ---- Parse request ----
    try:
        payload = ChatIn(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"message": "Invalid payload", "errors": e.errors()}), 400

    sid = str(payload.user_id or "default")
    q = payload.query.strip()
    if not q:
        return jsonify({"message": "Missing 'query'"}), 400

    SESSION.add(sid, "user", q)

    # -------------------------------------------------------
    # Parse intent ONCE (no duplication)
    # -------------------------------------------------------
    p = parse_intent(q)
    intent = p.intent

    # We will fill this if DB lookup is needed
    facts = None

    # Centralized fuzzy ID lookup
    def _fund_id_lookup(name: str):
        try:
            from db import fund_id_by_fuzzy
            fid = fund_id_by_fuzzy(name)
            if fid:
                return fid
        except Exception:
            pass
        return fund_id_by_name(name)

    # -------------------------------------------------------
    # 1) DATA INTENT HANDLING (same for baseline + hybrid)
    # -------------------------------------------------------
    if intent == "sip_summary":
        from db import sip_total_year
        from calc import yoy_pct

        if not p.fund_name:
            return jsonify({"message": "Please specify a fund name (e.g., '... for HDFC Equity Growth')."}), 400

        year = p.year or datetime.now().year
        fid = _fund_id_lookup(p.fund_name)
        if not fid:
            return jsonify({"message": f"Fund '{p.fund_name}' not found."}), 404

        this_year = sip_total_year(user_id=1, fund_id=fid, year=year)

        facts = {
            "type": "sip_summary",
            "year": year,
            "fund_name": p.fund_name,
            "total_this": float(this_year["total"] or 0),
            "wants_evaluation": getattr(p, "wants_evaluation", False),
        }

        if p.compare_to_last_year and year > 2000:
            prev = sip_total_year(user_id=1, fund_id=fid, year=year - 1)
            facts["total_prev"] = float(prev["total"] or 0)
            facts["yoy"] = yoy_pct(facts["total_this"], facts["total_prev"])

    elif intent == "latest_nav":
        from db import latest_nav as latest_nav_fn

        if not p.fund_name:
            return jsonify({"message": "Please specify a fund for latest NAV."}), 400
        fid = _fund_id_lookup(p.fund_name)
        if not fid:
            return jsonify({"message": f"Fund '{p.fund_name}' not found."}), 404

        nav = latest_nav_fn(fid)
        if not nav:
            return jsonify({"message": "No NAV data available"}), 404

        facts = {
            "type": "latest_nav",
            "fund_name": p.fund_name,
            "date": nav["date"],
            "nav_value": nav["nav_value"],
        }

    elif intent == "sip_projection":
        # purely template
        facts = {}
        answer = (
            "For projections, use the SIP calculator to input monthly amount, years, and rate."
        )
        SESSION.add(sid, "assistant", answer)
        return jsonify({
            "answer_text": answer,
            "facts": {},
            "meta": {"mode": EVAL_MODE, "llm_used": False},
        })

    # -------------------------------------------------------
    # 2) HYBRID or BASELINE ANSWERING LOGIC
    # -------------------------------------------------------
    if facts is not None:
        use_llm = (EVAL_MODE == "hybrid")

        # ask LLM or template
        answer, used_llm, llm_err = explain_answer(
            user_query=q,
            facts=facts,
            use_llm=use_llm
        )

        SESSION.add(sid, "assistant", answer)
        return jsonify({
            "answer_text": answer,
            "facts": facts,
            "meta": {"mode": EVAL_MODE, "llm_used": used_llm, "llm_error": llm_err},
        })

    # -------------------------------------------------------
    # 3) NON-DATA GENERAL QUERIES
    # -------------------------------------------------------
    if EVAL_MODE == "baseline":
        # deterministic fallback
        answer = (
            "I do not understand. Please ask data questions such as "
            "'SIP total in 2024 for HDFC Equity Growth' or "
            "'latest NAV for HDFC Equity Growth'."
        )
        SESSION.add(sid, "assistant", answer)
        return jsonify({
            "answer_text": answer,
            "facts": {},
            "meta": {"mode": "baseline", "llm_used": False},
        })

    # hybrid general
    messages = [{"role": "system", "content": "You are a helpful finance assistant chatbot on a finance management page. "
            "Always answer in **2–3 short sentences, max 100 words** in context to finance. "
            "Do not provide long explanations, lists, disclaimers, or extended paragraphs. "
            "Be crisp, direct, and beginner-friendly."}]
    messages.extend(SESSION.get(sid))
    messages.append({"role": "user", "content": q})

    try:
        out = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "gemma3:1b", "messages": messages, "stream": False},
            timeout=60
        ).json()
        answer = out["message"]["content"]
        llm_used = True
        llm_err = None
    except Exception as e:
        answer = "Sorry, I couldn’t generate a response right now."
        llm_used = False
        llm_err = str(e)

    SESSION.add(sid, "assistant", answer)

    return jsonify({
        "answer_text": answer,
        "facts": {},
        "meta": {"mode": "hybrid", "llm_used": llm_used, "llm_error": llm_err},
    })

#helpers
def build_messages(session_id, user_msg):
    history = SESSION.get(session_id)
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_msg}]
    return msgs

def _warmup_llm():
    try:
        # Warm the summarizer path; planner warmup is optional and off by default
        explain_answer("warmup",
                       {"type": "sip_summary", "year": 2024, "fund_name": "Warmup Fund", "total_this": 0},
                       use_llm=(EVAL_MODE == "hybrid"))
        print("[warmup] LLM warmed")
    except Exception as e:
        print("[warmup] LLM warmup failed:", e)

@app.route("/chat/reset", methods=["POST"])
def reset_chat():
    data = request.get_json()
    sid = str(data.get("user_id", "default"))
    SESSION.reset(sid)
    return jsonify({"message": f"Session {sid} cleared"})

@app.route("/_init_db", methods=["POST"])
def init_db_route():
    init_db()
    seed_db()
    return jsonify({"status": "ok"})

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    try:
        init_db()
        seed_db()
    except Exception as e:
        print("DB init/seed error:", e)
    threading.Thread(target=_warmup_llm, daemon=True).start()
    app.run(host="localhost", port=5001, debug=True)
