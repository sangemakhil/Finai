import { useState } from "react";
import { chatApi } from "../lib/api";

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! Ask about your SIP totals, NAV, or projections." },
  ]);
  const [loading, setLoading] = useState(false);
  const [lastError, setLastError] = useState("");

  const userId = localStorage.getItem("userId") || "u123";

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setLastError("");
    setLoading(true);
    try {
      const data = await chatApi({ userId, query: q });
      const reply =
        (data && data.answer_text) ||
        "No answer_text returned by backend.";
      setMessages((m) => [
        ...m,
        { role: "assistant", text: reply },
        ...(data?.facts
          ? [{ role: "assistant", text: `Facts: ${JSON.stringify(data.facts)}` }]
          : []),
      ]);
    } catch (e) {
      const msg =
        e?.response?.data?.message ||
        e?.message ||
        "Network/Server error.";
      setLastError(msg);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Error: ${msg}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold mb-4">Chat</h1>

      <div className="rounded-lg border border-gray-800 bg-gray-900 h-[60vh] p-4 overflow-y-auto space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-md text-sm ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-100"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400">Thinking…</div>}
      </div>

      {lastError && (
        <div className="mt-3 text-sm rounded-md border border-red-800 bg-red-950/50 px-3 py-2 text-red-300">
          {lastError}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          className="flex-1 rounded-md bg-gray-900 border border-gray-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 resize-none"
          placeholder='E.g., "SIP total in 2024 vs 2023 for HDFC Equity Growth"'
        />
        <button
          onClick={send}
          disabled={loading}
          className="rounded-md bg-indigo-600 hover:bg-indigo-500 transition-colors px-4 py-2 font-medium disabled:opacity-60"
        >
          Send
        </button>
      </div>
    </div>
  );
}
