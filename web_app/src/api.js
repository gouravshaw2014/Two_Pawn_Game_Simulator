import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Game endpoints
export const startGame = (rules, initial) =>
  axios.post(`${API_BASE_URL}/start`, { rules, initial });

export const playAction = (action) =>
  axios.post(`${API_BASE_URL}/action`, { action });

// AI endpoints
export const getAIStatus = () => axios.get(`${API_BASE_URL}/ai/status`);

export const initAI = (modelPath, strategy = "greedy", enable = true) =>
  axios.post(`${API_BASE_URL}/ai/init`, {
    model_path: modelPath,
    strategy,
    enable,
  });

export const suggestMove = (gameState = null, validActions = null) =>
  axios.post(`${API_BASE_URL}/ai/suggest`, {
    game_state: gameState,
    valid_actions: validActions,
  });

export const evaluateAllActions = (gameState = null, validActions = null) =>
  axios.post(`${API_BASE_URL}/ai/evaluate`, {
    game_state: gameState,
    valid_actions: validActions,
  });

export const setAIStrategy = (strategy, temperature = null, epsilon = null) => {
  const payload = { strategy };
  if (temperature !== null) payload.temperature = temperature;
  if (epsilon !== null) payload.epsilon = epsilon;
  return axios.post(`${API_BASE_URL}/ai/strategy`, payload);
};

export const setAIEnabled = (enabled) =>
  axios.post(`${API_BASE_URL}/ai/enable`, { enabled });

export const getAvailableModels = () =>
  axios.get(`${API_BASE_URL}/ai/models/available`);

export const getAvailableStrategies = () =>
  axios.get(`${API_BASE_URL}/ai/strategies/available`);
