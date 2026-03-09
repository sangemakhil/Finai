import { useState } from "react";
import api from "../lib/api";

export default function SipCalculator() {
  const [monthly, setMonthly] = useState(500);
  const [years, setYears] = useState(10);
  const [rate, setRate] = useState(12);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function compute() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.post("/calculate/sip", { monthly: +monthly, years: +years, rate: +rate });
      setResult(res.data);
    } catch (e) {
      setError(e?.response?.data?.message || e.message || "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-2xl font-semibold">SIP Calculator</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm mb-1">Monthly Contribution ($)</label>
          <input
            type="number"
            className="w-full rounded-md bg-gray-900 border border-gray-800 px-3 py-2 focus:ring-2 focus:ring-indigo-600"
            value={monthly}
            onChange={(e) => setMonthly(e.target.value)}
            min={0}
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Years</label>
          <input
            type="number"
            className="w-full rounded-md bg-gray-900 border border-gray-800 px-3 py-2 focus:ring-2 focus:ring-indigo-600"
            value={years}
            onChange={(e) => setYears(e.target.value)}
            min={0}
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Annual Return (%)</label>
          <input
            type="number"
            className="w-full rounded-md bg-gray-900 border border-gray-800 px-3 py-2 focus:ring-2 focus:ring-indigo-600"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            min={0}
            step="0.1"
          />
        </div>
      </div>

      <button
        onClick={compute}
        disabled={loading}
        className="rounded-md bg-indigo-600 hover:bg-indigo-500 transition-colors px-4 py-2 font-medium disabled:opacity-60"
      >
        {loading ? "Calculating…" : "Calculate"}
      </button>

      {error && (
        <div className="rounded-md bg-red-950/60 border border-red-800 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 space-y-2">
          <div className="text-sm text-gray-300">Monthly: ${result.result.monthly.toFixed(2)}</div>
          <div className="text-sm text-gray-300">Years: {result.result.years}</div>
          <div className="text-sm text-gray-300">Rate: {result.result.rate}%</div>
          <div className="text-lg font-semibold">
            Projected Future Value: ${result.result.future_value.toLocaleString()}
          </div>
          <div className="text-sm text-gray-400">{result.answer_text}</div>
        </div>
      )}
    </div>
  );
}
