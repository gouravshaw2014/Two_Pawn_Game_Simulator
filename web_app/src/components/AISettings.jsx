import { useEffect, useState } from "react";
import {
  getAIStatus,
  initAI,
  setAIStrategy,
  setAIEnabled,
  getAvailableModels,
  getAvailableStrategies,
} from "../api";

export default function AISettings({ onStatusChange = null }) {
  const [aiStatus, setAIStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [strategies, setStrategies] = useState({});
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedStrategy, setSelectedStrategy] = useState("greedy");
  const [strategyParams, setStrategyParams] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load initial data
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [statusRes, modelsRes, strategiesRes] = await Promise.all([
        getAIStatus().catch(() => null),
        getAvailableModels().catch(() => null),
        getAvailableStrategies().catch(() => null),
      ]);

      if (statusRes?.data) {
        setAIStatus(statusRes.data);
      }
      if (modelsRes?.data?.models) {
        setModels(modelsRes.data.models);
        if (modelsRes.data.models.length > 0) {
          setSelectedModel(modelsRes.data.models[0].path);
        }
      }
      if (strategiesRes?.data) {
        setStrategies(strategiesRes.data);
      }
    } catch (err) {
      console.error("Failed to load AI config:", err);
    }
  };

  const handleInitAI = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await initAI(selectedModel, selectedStrategy, true);
      setSuccess("AI initialized successfully!");

      // Refresh status
      const statusRes = await getAIStatus();
      setAIStatus(statusRes.data);
      onStatusChange?.(statusRes.data);

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const message = err.response?.data?.detail || "Failed to initialize AI";
      setError(message);
      console.error("Init AI error:", err);
    }
    setLoading(false);
  };

  const handleStrategyChange = async (newStrategy, params = {}) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await setAIStrategy(newStrategy, params.temperature, params.epsilon);
      setSelectedStrategy(newStrategy);
      setStrategyParams(params);
      setSuccess("Strategy updated!");

      // Refresh status
      const statusRes = await getAIStatus();
      setAIStatus(statusRes.data);
      onStatusChange?.(statusRes.data);

      setTimeout(() => setSuccess(null), 2000);
    } catch (err) {
      const message = err.response?.data?.detail || "Failed to change strategy";
      setError(message);
    }
    setLoading(false);
  };

  const handleToggleAI = async (enabled) => {
    setLoading(true);
    try {
      await setAIEnabled(enabled);

      // Refresh status
      const statusRes = await getAIStatus();
      setAIStatus(statusRes.data);
      onStatusChange?.(statusRes.data);
    } catch (err) {
      console.error("Toggle AI error:", err);
    }
    setLoading(false);
  };

  const strategyInfo = selectedStrategy ? strategies[selectedStrategy] : null;

  return (
    <div className="bg-white shadow-lg rounded-xl p-6 border border-slate-200 space-y-4">
      <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
        <span>⚙️</span>
        AI Configuration
      </h2>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-2 rounded-lg text-sm">
          ❌ {error}
        </div>
      )}
      {success && (
        <div className="bg-green-100 border border-green-300 text-green-700 px-4 py-2 rounded-lg text-sm">
          ✓ {success}
        </div>
      )}

      {/* AI Status Badge */}
      {aiStatus && (
        <div className="flex items-center gap-2 p-3 bg-slate-100 rounded-lg">
          <span
            className={`w-3 h-3 rounded-full ${aiStatus.enabled ? "bg-green-500" : "bg-red-500"}`}
          />
          <span className="font-medium text-slate-700">
            AI is {aiStatus.enabled ? "Enabled" : "Disabled"}
          </span>
          <span className="text-xs text-slate-600 ml-auto">
            {aiStatus.evaluator_type} •{" "}
            {aiStatus.strategy_type?.replace("Strategy", "")}
          </span>
        </div>
      )}

      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Select Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          disabled={loading || models.length === 0}
          className="w-full px-4 py-2 border border-slate-300 rounded-lg text-slate-700 bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50"
        >
          {models.length === 0 ? (
            <option value="">No models available</option>
          ) : (
            models.map((model) => (
              <option key={model.path} value={model.path}>
                {model.name} - {model.filename}
              </option>
            ))
          )}
        </select>
        <p className="text-xs text-slate-500 mt-1">
          Select a trained ML model to use for move evaluation
        </p>
      </div>

      {/* Strategy Selection */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Decision Strategy
        </label>
        <div className="grid grid-cols-2 gap-2 mb-3">
          {Object.entries(strategies).map(([key, strategy]) => (
            <button
              key={key}
              onClick={() => handleStrategyChange(key)}
              disabled={loading}
              className={`p-3 rounded-lg border-2 transition text-sm font-medium ${
                selectedStrategy === key
                  ? "border-purple-500 bg-purple-50 text-purple-700"
                  : "border-slate-300 bg-white text-slate-700 hover:border-slate-400"
              } disabled:opacity-50`}
            >
              <div>{strategy.name}</div>
              <div className="text-xs opacity-70 mt-1">
                {strategy.description}
              </div>
            </button>
          ))}
        </div>

        {/* Strategy Parameters */}
        {strategyInfo?.parameters && strategyInfo.parameters.length > 0 && (
          <div className="bg-slate-50 p-3 rounded-lg space-y-2 mb-3">
            {strategyInfo.parameters.map((param) => (
              <div key={param.name}>
                <label className="text-xs font-medium text-slate-700">
                  {param.name}
                  <span className="text-slate-500 ml-2">
                    (default: {param.default})
                  </span>
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="5"
                  step="0.1"
                  defaultValue={param.default}
                  onChange={(e) => {
                    const newParams = {
                      ...strategyParams,
                      [param.name]: parseFloat(e.target.value),
                    };
                    setStrategyParams(newParams);
                  }}
                  className="w-full"
                />
                <div className="text-xs text-slate-600 mt-1">
                  Current:{" "}
                  {(strategyParams[param.name] || param.default).toFixed(2)}
                </div>
              </div>
            ))}

            <button
              onClick={() =>
                handleStrategyChange(selectedStrategy, strategyParams)
              }
              disabled={loading}
              className="w-full mt-2 px-3 py-2 bg-slate-600 text-white rounded text-xs font-medium hover:bg-slate-700 disabled:opacity-50"
            >
              Apply Parameters
            </button>
          </div>
        )}
      </div>

      {/* Initialize Button */}
      <button
        onClick={handleInitAI}
        disabled={loading || models.length === 0}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 transition"
      >
        {loading ? "⏳ Initializing..." : "🚀 Initialize AI"}
      </button>

      {/* Enable/Disable Toggle */}
      {aiStatus?.available && (
        <div className="border-t pt-4">
          <button
            onClick={() => handleToggleAI(!aiStatus.enabled)}
            disabled={loading}
            className={`w-full px-4 py-2 rounded-lg font-medium transition ${
              aiStatus.enabled
                ? "bg-red-100 text-red-700 hover:bg-red-200"
                : "bg-green-100 text-green-700 hover:bg-green-200"
            } disabled:opacity-50`}
          >
            {aiStatus.enabled ? "🛑 Disable AI" : "✓ Enable AI"}
          </button>
        </div>
      )}
    </div>
  );
}
