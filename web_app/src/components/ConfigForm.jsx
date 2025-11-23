import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../api";

export default function ConfigForm() {
  const navigate = useNavigate();

  const availableColors = ["Red", "Blue", "Green"];

  const defaultNodeCount = 8;

  const DEFAULT_GRAPH = [
    [0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]

  ];



  const DEFAULT_VERTEX_COLORS = [
    "Red",
    "Red",
    "Blue",
    "Red",
    "Blue",
    "Green",
    "Blue",
    "Green"
  ];

  const inputBox =
    "w-full px-3 py-2 bg-white border border-slate-300 rounded-xl shadow-sm " +
    "focus:ring-2 focus:ring-indigo-400 focus:outline-none transition";

  // STATE ---------------------------
  const [ownership, setOwnership] = useState("MVPP");
  const [rule, setRule] = useState("optional-grabbing");
  const [kValue, setKValue] = useState(2);

  const [nodeCount, setNodeCount] = useState(defaultNodeCount);
  const [matrix, setMatrix] = useState(DEFAULT_GRAPH);
  const [vertexColors, setVertexColors] = useState(DEFAULT_VERTEX_COLORS);

  const [startVertex, setStartVertex] = useState("0");
  const [targetVertex, setTargetVertex] = useState("7");

  const [p1Pawns, setP1Pawns] = useState(["Red", "Green"]);
  const [p2Pawns, setP2Pawns] = useState(["Blue"]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const m = Array.from({ length: nodeCount }, () => Array(nodeCount).fill(0));
    // set a default graph for better usability
    for (let i = 0; i < nodeCount; i++) {
      for (let j = 0; j < DEFAULT_GRAPH[i].length; j++) {
        if (DEFAULT_GRAPH[i][j] === 1) m[i][j] = 1;
      }
    }
    setMatrix(m);

    const vc = Array.from(
      { length: nodeCount },
      (_, i) => DEFAULT_VERTEX_COLORS[i]
    );
    setVertexColors(vc);
  }, []);

  const handleNodeCountChange = (value) => {
    const n = Number(value);
    setNodeCount(n);

    const newMatrix = Array.from({ length: n }, () => Array(n).fill(0));
    setMatrix(newMatrix);

    setVertexColors(Array.from({ length: n }, () => ""));
  };

  const handleMatrixToggle = (r, c) => {
    const newMatrix = matrix.map((row) => [...row]);
    newMatrix[r][c] = newMatrix[r][c] ? 0 : 1;
    setMatrix(newMatrix);
  };

  const convertMatrixToAdjList = () => {
    const adj = {};
    for (let i = 0; i < nodeCount; i++) {
      adj[String(i)] = [];
      for (let j = 0; j < nodeCount; j++) {
        if (matrix[i][j] === 1) adj[String(i)].push(String(j));
      }
    }
    return adj;
  };

  const buildOwnership = () => {
    const dict = {};
    for (let i = 0; i < nodeCount; i++) dict[String(i)] = vertexColors[i];
    return dict;
  };

  const toggleP1Pawn = (color) =>
    setP1Pawns((prev) =>
      prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color]
    );

  const toggleP2Pawn = (color) =>
    setP2Pawns((prev) =>
      prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color]
    );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        rules: {
          graph: convertMatrixToAdjList(),
          pawn_ownership: buildOwnership(),
          target_vertex: targetVertex,
          grabbing_rule: rule,
          k_grab_limit: rule === "k-grabbing" ? Number(kValue) : 0,
        },
        initial: {
          start_vertex: startVertex,
          p1_initial_pawns: p1Pawns,
          p2_initial_pawns: p2Pawns,
        },
      };

      const res = await axios.post(`${API_BASE_URL}/start`, payload);

      localStorage.setItem("game_state", JSON.stringify(res.data));
      localStorage.setItem("target_vertex", payload.rules.target_vertex);

      navigate("/simulator");
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }

    setLoading(false);
  };

  // -----------------------------------
  // UI
  // -----------------------------------
  return (
    <form onSubmit={handleSubmit} className="space-y-10">
      {/* GENERAL SETTINGS */}
      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          General Settings
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Ownership Model
            </label>
            <select
              value={ownership}
              onChange={(e) => setOwnership(e.target.value)}
              className={inputBox}
            >
              <option value="OVPP">One Vertex per Pawn (OVPP)</option>
              <option value="MVPP">Multiple Vertices per Pawn (MVPP)</option>
              <option value="OMVPP">Overlapping Vertices (OMVPP)</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Grabbing Rule
            </label>
            <select
              value={rule}
              onChange={(e) => setRule(e.target.value)}
              className={inputBox}
            >
              <option value="always-grabbing">Always Grabbing</option>
              <option value="always-grabbing-or-giving">
                Always Grabbing or Giving
              </option>
              <option value="optional-grabbing">Optional Grabbing</option>
              <option value="k-grabbing">K-Grabbing</option>
            </select>
          </div>

          {rule === "k-grabbing" && (
            <div>
              <label className="block font-medium text-slate-700 mb-1">
                K Value
              </label>
              <input
                type="number"
                value={kValue}
                onChange={(e) => setKValue(Number(e.target.value))}
                className={inputBox}
              />
            </div>
          )}
        </div>
      </div>

      {/* GRAPH SETUP */}
      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Graph Setup
        </h2>

        <div className="flex items-center gap-4 mb-4">
          <label className="font-medium text-slate-700">Nodes:</label>
          <input
            type="number"
            min="2"
            value={nodeCount}
            onChange={(e) => handleNodeCountChange(e.target.value)}
            className={`${inputBox} w-28`}
          />
        </div>

        <div className="overflow-auto border rounded-xl p-3 bg-slate-50">
          <div
            className="grid gap-1"
            style={{ gridTemplateColumns: `repeat(${nodeCount + 1}, 40px)` }}
          >
            <div />
            {Array.from({ length: nodeCount }, (_, j) => (
              <div key={j} className="text-center font-bold">
                {j}
              </div>
            ))}

            {matrix.map((row, i) => (
              <div key={i} className="contents">
                <div className="text-center font-bold">{i}</div>

                {row.map((cell, j) => (
                  <button
                    key={`${i}-${j}`}
                    type="button"
                    onClick={() => handleMatrixToggle(i, j)}
                    className={
                      "w-10 h-10 rounded-md border transition " +
                      (cell
                        ? "bg-indigo-500 text-white"
                        : "bg-white hover:bg-slate-200")
                    }
                  >
                    {cell}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* VERTEX COLORS*/}

      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Vertex Colors
        </h2>

        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: nodeCount }, (_, i) => (
            <div
              key={i}
              className="flex items-center justify-between gap-2 p-3 bg-slate-50 rounded-xl border shadow-sm"
            >
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-700 w-6 text-center">
                  {i}
                </span>

                {/* Color preview dot (no new components, just a span) */}
                <span
                  className="w-4 h-4 rounded-full border border-slate-300"
                  style={{ background: vertexColors[i] || "transparent" }}
                />
              </div>

              <select
                value={vertexColors[i]}
                onChange={(e) => {
                  const arr = [...vertexColors];
                  arr[i] = e.target.value;
                  setVertexColors(arr);
                }}
                className="
                  w-32 px-3 py-2
                bg-slate-100
                  border border-slate-300
                  rounded-xl
                  shadow
                text-slate-700 text-sm font-medium
                  focus:ring-2 focus:ring-indigo-500
                hover:bg-slate-200
                  transition"
              >
                <option value="">Color</option>
                {availableColors.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </div>

      {/* START/TARGET */}

      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Game Settings
        </h2>

        <div className="grid grid-cols-4 gap-4 items-center">
          {/* Start Vertex */}
          <label className="font-medium text-slate-700">Start Vertex</label>
          <select
            value={startVertex}
            onChange={(e) => setStartVertex(e.target.value)}
            className="
        w-full px-3 py-2 
        border border-slate-300 rounded-xl 
        bg-white shadow-sm 
        text-slate-700 text-sm font-medium 
        focus:outline-none focus:ring-2 focus:ring-indigo-500
        hover:border-indigo-400 transition
      "
          >
            {Array.from({ length: nodeCount }, (_, i) => (
              <option key={i} value={String(i)}>
                {i}
              </option>
            ))}
          </select>

          {/* Target Vertex */}
          <label className="font-medium text-slate-700">Target Vertex</label>
          <select
            value={targetVertex}
            onChange={(e) => setTargetVertex(e.target.value)}
            className="
        w-full px-3 py-2 
        border border-slate-300 rounded-xl 
        bg-white shadow-sm 
        text-slate-700 text-sm font-medium 
        focus:outline-none focus:ring-2 focus:ring-indigo-500
        hover:border-indigo-400 transition
      "
          >
            {Array.from({ length: nodeCount }, (_, i) => (
              <option key={i} value={String(i)}>
                {i}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* PAWNS */}
      {/* <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Pawn Assignment
        </h2>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-slate-700 mb-2">Player 1</h3>
            {availableColors.map((color) => (
              <label key={color} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={p1Pawns.includes(color)}
                  onChange={() => toggleP1Pawn(color)}
                />
                {color}
              </label>
            ))}
          </div>

          <div>
            <h3 className="font-medium text-slate-700 mb-2">Player 2</h3>
            {availableColors.map((color) => (
              <label key={color} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={p2Pawns.includes(color)}
                  onChange={() => toggleP2Pawn(color)}
                />
                {color}
              </label>
            ))}
          </div>
        </div>
      </div> */}

      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Pawn Assignment
        </h2>

        <div className="grid grid-cols-2 gap-6">
          {/* Player 1 */}
          <div>
            <h3 className="font-medium text-slate-700 mb-3">Player 1</h3>

            <div className="flex flex-wrap gap-2">
              {availableColors.map((color) => {
                const active = p1Pawns.includes(color);
                return (
                  <div
                    key={color}
                    onClick={() => toggleP1Pawn(color)}
                    className={`
                px-3 py-1.5 rounded-xl cursor-pointer text-sm font-medium
                border transition select-none
                ${
                  active
                    ? "bg-indigo-600 text-white border-indigo-600 shadow-md"
                    : "bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200"
                }
              `}
                  >
                    {color}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Player 2 */}
          <div>
            <h3 className="font-medium text-slate-700 mb-3">Player 2</h3>

            <div className="flex flex-wrap gap-2">
              {availableColors.map((color) => {
                const active = p2Pawns.includes(color);
                return (
                  <div
                    key={color}
                    onClick={() => toggleP2Pawn(color)}
                    className={`
                px-3 py-1.5 rounded-xl cursor-pointer text-sm font-medium
                border transition select-none
                ${
                  active
                    ? "bg-rose-600 text-white border-rose-600 shadow-md"
                    : "bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200"
                }
              `}
                  >
                    {color}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {error && <p className="text-red-500 text-center font-medium">{error}</p>}
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 flex justify-items-center text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md font-semibold transition"
        >
          {loading ? "Starting..." : "Start Game"}
        </button>
      </div>
    </form>
  );
}
