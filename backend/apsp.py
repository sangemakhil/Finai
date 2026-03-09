# app.py (WITH LOGGING)
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
import csv
from textstat import flesch_reading_ease

# -------------------------------
# Config
# -------------------------------
EVAL_MODE = os.getenv("EVAL_MODE", "hybrid")    # hybrid or baseline
LOG_FILE = f"eval_{EVAL_MODE}.csv"

# Create logging file if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query", "response", "facts", "time_taken_sec", "clarity_score"])


def log_eval(query, response, facts, duration):
    clarity = flesch_reading_ease(response) if response else 0
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([query, response, json.dumps(facts), duration, clarity])


# -------------------------------
# Flask App
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
    # Parse intent once
    # -------------------------------------------------------
    p = parse_intent(q)
    intent = p.intent
    facts = None

    # Fuzzy lookup
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
    # DATA INTENTS
    # -------------------------------------------------------
    if intent == "sip_summary":
        from db import sip_total_year
        from calc import yoy_pct

        if not p.fund_name:
            return jsonify({"message": "Please specify a fund name."}), 400

        year = p.year or datetime.now().year
        fid = _fund_id_lookup(p.fund_name)
        if not fid:
            return jsonify({"message": f"Fund '{p.fund_name}' not found."}), 404

        this_year = sip_total_year(1, fid, year)
        facts = {
            "type": "sip_summary",
            "year": year,
            "fund_name": p.fund_name,
            "total_this": float(this_year["total"] or 0),
        }

        if p.compare_to_last_year:
            prev = sip_total_year(1, fid, year - 1)
            facts["total_prev"] = float(prev["total"] or 0)
            from calc import yoy_pct
            facts["yoy"] = yoy_pct(facts["total_this"], facts["total_prev"])

    elif intent == "latest_nav":
        from db import latest_nav
        if not p.fund_name:
            return jsonify({"message": "Please specify a fund name."}), 400

        fid = _fund_id_lookup(p.fund_name)
        if not fid:
            return jsonify({"message": f"Fund '{p.fund_name}' not found."}), 404

        nav = latest_nav(fid)
        facts = {
            "type": "latest_nav",
            "fund_name": p.fund_name,
            "date": nav["date"],
            "nav_value": nav["nav_value"],
        }

    # -------------------------------------------------------
    # Generate answer
    # -------------------------------------------------------
    if facts is not None:
        use_llm = (EVAL_MODE == "hybrid")
        answer, used_llm, llm_err = explain_answer(q, facts, use_llm)
        duration = time.time() - t0

        SESSION.add(sid, "assistant", answer)
        log_eval(q, answer, facts, duration)

        return jsonify({
            "answer_text": answer,
            "facts": facts,
            "meta": {"mode": EVAL_MODE, "llm_used": used_llm, "llm_error": llm_err},
        })

    # -------------------------------------------------------
    # GENERAL QUERIES
    # -------------------------------------------------------
    if EVAL_MODE == "baseline":
        answer = "I do not understand. Please ask SIP or NAV questions."
        duration = time.time() - t0
        SESSION.add(sid, "assistant", answer)
        log_eval(q, answer, {}, duration)

        return jsonify({"answer_text": answer, "facts": {}, "meta": {"mode": "baseline"}})

    # HYBRID → general LLM
    messages = [
        {"role": "system", "content": "You are a helpful finance assistant. "
            "Always answer in **2–3 short sentences max**. "
            "Do not provide long explanations, lists, disclaimers, or extended paragraphs. "
            "Be crisp, direct, and beginner-friendly."},
        *SESSION.get(sid),
        {"role": "user", "content": q},
    ]

    try:
        out = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": "gemma3:1b", "messages": messages, "stream": False},
            timeout=60
        ).json()
        answer = out["message"]["content"]
        llm_used = True
    except Exception as e:
        answer = "Sorry, I could not answer."
        llm_used = False

    duration = time.time() - t0
    SESSION.add(sid, "assistant", answer)
    log_eval(q, answer, {}, duration)

    return jsonify({
        "answer_text": answer,
        "facts": {},
        "meta": {"mode": "hybrid", "llm_used": llm_used},
    })


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

    app.run(host="localhost", port=5001, debug=True)
