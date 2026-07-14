import { useEffect, useState } from "react";
import { suggestMove, evaluateAllActions, getAIStatus } from "../api";

export default function AIPanel({ enabled = false, onSuggestionClick = null }) {
  const [aiSuggestion, setAISuggestion] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiStatus, setAIStatus] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (enabled) {
      fetchAISuggestion();
    }
  }, [enabled]);

  const fetchAISuggestion = async () => {
    setLoading(true);
    setError(null);
    try {
      // Get AI status first
      try {
        const statusRes = await getAIStatus();
        setAIStatus(statusRes.data);
      } catch (e) {
        console.warn("Could not fetch AI status:", e);
      }

      // Get evaluation of all actions
      const evalRes = await evaluateAllActions();
      const evals = evalRes.data.evaluations || [];
      setEvaluations(evals);

      // Get best suggestion
      if (evals.length > 0) {
        const best = evals[0];
        setAISuggestion({
          action: best.action,
          win_probability: best.win_probability,
          confidence: best.confidence,
        });
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setError("AI not enabled");
      } else if (err.response?.status === 400) {
        setError(err.response.data.detail || "Invalid game state");
      } else {
        setError("Failed to get AI suggestion");
      }
      console.error("AI suggestion error:", err);
    }
    setLoading(false);
  };

  if (!enabled || !aiStatus?.enabled) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 shadow-lg rounded-xl p-5 border-2 border-purple-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-purple-900 flex items-center gap-2">
          <span className="text-xl">🤖</span>
          AI Assistant
          {aiStatus?.strategy_type && (
            <span className="text-xs font-normal text-purple-600 bg-purple-100 px-2 py-1 rounded-full">
              {aiStatus.strategy_type.replace("Strategy", "")}
            </span>
          )}
        </h2>
        <button
          onClick={fetchAISuggestion}
          disabled={loading}
          className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 transition"
        >
          {loading ? "⏳ Analyzing..." : "🔄 Refresh"}
        </button>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-3 py-2 rounded mb-3 text-sm">
          {error}
        </div>
      )}

      {/* Main suggestion */}
      {aiSuggestion && (
        <div className="bg-white rounded-lg p-4 mb-3 border-2 border-purple-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">
              Top Recommendation
            </span>
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
              #{1}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-bold text-purple-900">
                {aiSuggestion.action}
              </p>
              <p className="text-xs text-slate-500">Suggested move</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-green-600">
                {(aiSuggestion.win_probability * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-slate-500">Win probability</p>
            </div>
          </div>

          {/* Win probability bar */}
          <div className="mt-3 bg-slate-200 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-300"
              style={{
                width: `${Math.min(aiSuggestion.win_probability * 100, 100)}%`,
              }}
            />
          </div>

          {/* Click to use this action */}
          {onSuggestionClick && (
            <button
              onClick={() => onSuggestionClick(aiSuggestion.action)}
              className="mt-3 w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 transition active:scale-95"
            >
              ✓ Use This Move
            </button>
          )}
        </div>
      )}

      {/* Toggle details */}
      {evaluations.length > 1 && (
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="w-full px-3 py-2 text-sm text-purple-700 bg-purple-100 hover:bg-purple-200 rounded-lg transition font-medium"
        >
          {showDetails ? "▼ Hide" : "▶ Show"} All Options ({evaluations.length})
        </button>
      )}

      {/* Detailed evaluations */}
      {showDetails && evaluations.length > 0 && (
        <div className="mt-3 space-y-2 max-h-48 overflow-y-auto">
          {evaluations.map((evaluation, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border-l-4 ${
                evaluation.rank === 1
                  ? "bg-green-50 border-green-500 border-l-4"
                  : evaluation.rank === 2
                    ? "bg-yellow-50 border-yellow-500"
                    : evaluation.rank === 3
                      ? "bg-orange-50 border-orange-500"
                      : "bg-slate-50 border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-700">
                    #{evaluation.rank}
                  </span>
                  <span className="font-medium text-slate-800">
                    {evaluation.action}
                  </span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-slate-900">
                    {(evaluation.win_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Mini progress bar */}
              <div className="mt-1 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    evaluation.win_probability > 0.8
                      ? "bg-green-500"
                      : evaluation.win_probability > 0.5
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{
                    width: `${Math.min(evaluation.win_probability * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Model info */}
      {aiStatus && (
        <div className="mt-4 pt-3 border-t border-purple-200 text-xs text-slate-600">
          <div className="flex items-center justify-between">
            <span>Model: {aiStatus.evaluator_type || "N/A"}</span>
            <span>{aiStatus.has_model ? "✓ Loaded" : "✗ Not loaded"}</span>
          </div>
        </div>
      )}
    </div>
  );
}
