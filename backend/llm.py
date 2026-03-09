# llm.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"

def _call_ollama(prompt: str, model: str = MODEL, timeout: int = 90) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()

def _template_answer(user_query: str, facts: dict) -> str:
    t = facts.get("type")
    if t == "sip_summary":
        y = facts.get("year")
        fund = facts.get("fund_name", "the fund")
        this_total = facts.get("total_this", 0.0) or 0.0
        prev_total = facts.get("total_prev")
        yoy = facts.get("yoy")
        if prev_total is not None and yoy is not None:
            return (
                f"In {y}, you contributed ${this_total:.0f} to {fund}. "
                f"Last year was ${prev_total:.0f}, so you are {yoy:.1f}% fu."
            )
        return f"In {y}, you contributed ${this_total:.0f} to {fund}."
    if t == "latest_nav":
        fund = facts.get("fund_name", "the fund")
        d = facts.get("date")
        v = facts.get("nav_value")
        if d and v is not None:
            return f"The latest NAV for {fund} is {float(v):.2f} (as of {d})."
        return "I couldn’t find a latest NAV for the selected fund."
    if t == "sip_projection":
        monthly = facts.get("monthly", 0.0) or 0.0
        years = facts.get("years", 0)
        rate = facts.get("rate", 0.0) or 0.0
        fv = facts.get("fv", 0.0) or 0.0
        return (
            f"If you invest ${monthly:.0f}/mo for {years} years at {rate}% annually, "
            f"your corpus could reach about ${fv:.0f}."
        )
    return "Here is your result."

def explain_answer(user_query: str, facts: dict, use_llm: bool = True):
    """
    Returns: (text, llm_used: bool, llm_error: str|None)
    """

    if not use_llm:
        txt = _template_answer(user_query, facts)
        return txt, False, None

    system = (
        "You are a concise financial assistant.\n"
        "Follow these rules strictly:\n"
        "1. Use ONLY the provided facts when numbers/dates are needed.\n"
        "2. DO NOT reveal or mention 'facts', 'JSON', or any system logic.\n"
        "3. DO NOT generate section titles or labels (no 'Fact-based answer', no bullets).\n"
        "4. If the user asks multiple questions, answer ALL of them in a single smooth paragraph.\n"
        "5. Keep the answer short (1–3 sentences) unless the user explicitly asks for more.\n"
        "6. If a required number is missing from the facts, say you need more information.\n"
    )

    user_content = (
        f"User question: {user_query}\n"
        f"Facts you must rely on: {facts}\n"
        "Write a natural, beginner-friendly answer in one short paragraph."
    )

    prompt = f"{system}\n\n{user_content}"

    try:
        txt = _call_ollama(prompt).strip()
        return txt, True, None
    except Exception as e:
        # fallback template
        txt = _template_answer(user_query, facts)
        return txt, False, str(e)


