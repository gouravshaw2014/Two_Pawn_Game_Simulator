// import { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import axios from "axios";
// import { API_BASE_URL } from "../api";

// export default function ConfigForm() {
//   const navigate = useNavigate();

//   const availableColors = [
//     "Red",
//     "Blue",
//     "Green",
//   ];

  


//   // core configs
//   const [ownership, setOwnership] = useState("OVPP");
//   const [rule, setRule] = useState("always-grabbing");
//   const [kValue, setKValue] = useState(2);

//   // graph vertex count + matrix
//   const [nodeCount, setNodeCount] = useState(7);
//   const [matrix, setMatrix] = useState(createMatrix(4));
//   const [vertexColors, setVertexColors] = useState(
//     Array.from({ length: nodeCount }, () => "")
//   );

//   // game vertices
//   const [startVertex, setStartVertex] = useState("0");
//   const [targetVertex, setTargetVertex] = useState("6");

//   // pawn distributions
//   const [p1Pawns, setP1Pawns] = useState(["Red", "Blue", "Green"]);
//   const [p2Pawns, setP2Pawns] = useState([]);

//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);

//   function createMatrix(n) {
//     return Array.from({ length: n }, () => Array(n).fill(0));
//   }

//   const handleMatrixToggle = (r, c) => {
//     const newMatrix = matrix.map((row) => row.slice());
//     newMatrix[r][c] = newMatrix[r][c] ? 0 : 1;
//     setMatrix(newMatrix);
//   };

//   const handleNodeCountChange = (n) => {
//     const value = Number(n);
//     setNodeCount(value);
//     setMatrix(createMatrix(value));
//     setVertexColors(Array.from({ length: value }, () => ""));
//   };

//   const convertMatrixToAdjList = () => {
//     const adjList = {};
//     for (let i = 0; i < nodeCount; i++) {
//       adjList[String(i)] = [];
//       for (let j = 0; j < nodeCount; j++) {
//         if (matrix[i][j] === 1) {
//           adjList[String(i)].push(String(j));
//         }
//       }
//     }
//     return adjList;
//   };

//   const toggleP1Pawn = (color) => {
//     setP1Pawns((prev) =>
//       prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color]
//     );
//   };

//   const toggleP2Pawn = (color) => {
//     setP2Pawns((prev) =>
//       prev.includes(color) ? prev.filter((c) => c !== color) : [...prev, color]
//     );
//   };


//   const buildOwnership = () => {
//     const dict = {};
//     for (let i = 0; i < nodeCount; i++) {
//       if (!vertexColors[i]) {
//         throw new Error(`Vertex ${i} has no assigned color`);
//       }
//       dict[String(i)] = vertexColors[i];
//     }
//     return dict;
//   };



//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError(null);
//     setLoading(true);

//     try {
//       const graph = convertMatrixToAdjList();

//       if (!graph[startVertex]) throw new Error("Invalid start vertex");
//       if (!graph[targetVertex]) throw new Error("Invalid target vertex");

//       const payload = {
//         rules: {
//           graph,
//           pawn_ownership: buildOwnership(), // <-- ADD THIS
//           target_vertex: targetVertex,
//           grabbing_rule: rule,
//           k_grab_limit: rule === "k-grabbing" ? Number(kValue) : 0,
//         },
//         initial: {
//           start_vertex: startVertex,
//           p1_initial_pawns: p1Pawns, // array (no split)
//           p2_initial_pawns: p2Pawns, // array (no split)
//         },
//       };

//       const response = await axios.post(`${API_BASE_URL}/start`, payload);

//       localStorage.setItem("game_state", JSON.stringify(response.data));
//       localStorage.setItem("target_vertex", payload.rules.target_vertex);


//       navigate("/simulator");
//     } catch (err) {
//       setError(err.response?.data?.error || err.message);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <form onSubmit={handleSubmit} className="space-y-6 p-4">
//       {/* Ownership Model */}
//       <div>
//         <label className="block font-medium">Ownership Model</label>
//         <select
//           value={ownership}
//           onChange={(e) => setOwnership(e.target.value)}
//           className="border p-2 rounded-lg w-full"
//         >
//           <option value="OVPP">One Vertex per Pawn (OVPP)</option>
//           <option value="MVPP">Multiple Vertices per Pawn (MVPP)</option>
//           <option value="OMVPP">Overlapping Vertices (OMVPP)</option>
//         </select>
//       </div>

//       {/* Grabbing Rule */}
//       <div>
//         <label className="block font-medium">Grabbing Rule</label>
//         <select
//           value={rule}
//           onChange={(e) => setRule(e.target.value)}
//           className="border p-2 rounded-lg w-full"
//         >
//           <option value="always-grabbing">Always Grabbing</option>
//           <option value="always-grabbing-or-giving">
//             Always Grabbing or Giving
//           </option>
//           <option value="optional-grabbing">Optional Grabbing</option>
//           <option value="k-grabbing">K-Grabbing</option>
//         </select>
//       </div>

//       {rule === "k-grabbing" && (
//         <div>
//           <label className="block font-medium">K Value</label>
//           <input
//             type="number"
//             min="1"
//             value={kValue}
//             onChange={(e) => setKValue(Number(e.target.value))}
//             className="border p-2 rounded-lg w-full"
//           />
//         </div>
//       )}

//       {/* Graph Editor */}
//       <div>
//         <label className="block font-medium mb-1">
//           Graph (Adjacency Matrix)
//         </label>
//         <div className="flex gap-3 items-center">
//           <span>Nodes:</span>
//           <input
//             type="number"
//             min="2"
//             value={nodeCount}
//             onChange={(e) => handleNodeCountChange(e.target.value)}
//             className="border p-1 rounded w-20"
//           />
//         </div>

//         <div
//           className="mt-4 grid gap-1"
//           style={{ gridTemplateColumns: `repeat(${nodeCount + 1}, 40px)` }}
//         >
//           <div></div>
//           {Array.from({ length: nodeCount }, (_, j) => (
//             <div key={`h-${j}`} className="text-center font-bold">
//               {j}
//             </div>
//           ))}

//           {matrix.map((row, i) => (
//             <>
//               <div key={`r-${i}`} className="text-center font-bold self-center">
//                 {i}
//               </div>
//               {row.map((cell, j) => (
//                 <button
//                   type="button"
//                   key={`${i}-${j}`}
//                   onClick={() => handleMatrixToggle(i, j)}
//                   className={`w-10 h-10 border ${
//                     cell ? "bg-green-500" : "bg-gray-200"
//                   }`}
//                 >
//                   {cell}
//                 </button>
//               ))}
//             </>
//           ))}
//         </div>
//       </div>

//       {/* Vertex Colors */}
//       <div>
//         <label className="block font-medium mb-1">
//           Assign Color to Every Vertex
//         </label>

//         <div className="grid gap-3">
//           {Array.from({ length: nodeCount }, (_, i) => (
//             <div key={i} className="flex items-center gap-3">
//               <span className="font-medium w-6">{i}</span>

//               <select
//                 value={vertexColors[i]}
//                 onChange={(e) => {
//                   const newColors = [...vertexColors];
//                   newColors[i] = e.target.value;
//                   setVertexColors(newColors);
//                 }}
//                 className="border p-1 rounded w-40"
//               >
//                 <option value="">-- Select Color --</option>
//                 {availableColors.map((c) => (
//                   <option key={c} value={c}>
//                     {c}
//                   </option>
//                 ))}
//               </select>
//             </div>
//           ))}
//         </div>
//       </div>

//       {/* Start and Target Vertices */}
//       <div>
//         <label className="block font-medium">Start Vertex</label>
//         <select
//           value={startVertex}
//           onChange={(e) => setStartVertex(e.target.value)}
//           className="border p-2 rounded w-full"
//         >
//           {Array.from({ length: nodeCount }, (_, i) => (
//             <option key={i} value={String(i)}>
//               {i}
//             </option>
//           ))}
//         </select>
//       </div>
//       <div>
//         <label className="block font-medium">Target Vertex</label>
//         <select
//           value={targetVertex}
//           onChange={(e) => setTargetVertex(e.target.value)}
//           className="border p-2 rounded w-full"
//         >
//           {Array.from({ length: nodeCount }, (_, i) => (
//             <option key={i} value={String(i)}>
//               {i}
//             </option>
//           ))}
//         </select>
//       </div>

//       {/* Pawn Inputs */}
//       {/* P1 Pawn Colors */}
//       <div>
//         <label className="block font-medium mb-1">P1 Pawn Colors</label>
//         <div className="grid grid-cols-2 gap-2">
//           {availableColors.map((color) => (
//             <label key={color} className="flex items-center gap-2">
//               <input
//                 type="checkbox"
//                 checked={p1Pawns.includes(color)}
//                 onChange={() => toggleP1Pawn(color)}
//               />
//               {color}
//             </label>
//           ))}
//         </div>
//       </div>

//       {/* P2 Pawn Colors */}
//       <div>
//         <label className="block font-medium mb-1">P2 Pawn Colors</label>
//         <div className="grid grid-cols-2 gap-2">
//           {availableColors.map((color) => (
//             <label key={color} className="flex items-center gap-2">
//               <input
//                 type="checkbox"
//                 checked={p2Pawns.includes(color)}
//                 onChange={() => toggleP2Pawn(color)}
//               />
//               {color}
//             </label>
//           ))}
//         </div>
//       </div>

//       {/* Error Message */}
//       {error && <p className="text-red-600">{error}</p>}

//       <button
//         type="submit"
//         disabled={loading}
//         className="w-full bg-blue-600 text-white p-2 rounded-lg"
//       >
//         {loading ? "Starting..." : "Start Game"}
//       </button>
//     </form>
//   );
// }



import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API_BASE_URL } from "../api";

export default function ConfigForm() {
  const navigate = useNavigate();

  const availableColors = ["Red", "Blue", "Green"];

  const defaultNodeCount = 7;

  const DEFAULT_GRAPH = [
    [0, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 1],
    [0, 0, 0, 0, 0, 0, 0],
  ];

  const DEFAULT_VERTEX_COLORS = [
    "Red",
    "Red",
    "Blue",
    "Red",
    "Blue",
    "Green",
    "Green",
  ];

  const inputBox =
    "w-full px-3 py-2 bg-white border border-slate-300 rounded-xl shadow-sm " +
    "focus:ring-2 focus:ring-indigo-400 focus:outline-none transition";

  // STATE ---------------------------
  const [ownership, setOwnership] = useState("OVPP");
  const [rule, setRule] = useState("always-grabbing");
  const [kValue, setKValue] = useState(2);

  const [nodeCount, setNodeCount] = useState(defaultNodeCount);
  const [matrix, setMatrix] = useState(DEFAULT_GRAPH);
  const [vertexColors, setVertexColors] = useState(DEFAULT_VERTEX_COLORS);

  const [startVertex, setStartVertex] = useState("0");
  const [targetVertex, setTargetVertex] = useState("6");

  const [p1Pawns, setP1Pawns] = useState(["Red", "Blue", "Green"]);
  const [p2Pawns, setP2Pawns] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const m = Array.from({ length: nodeCount }, () => Array(nodeCount).fill(0));

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

      {/* VERTEX COLORS */}
      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
        <h2 className="text-2xl font-semibold text-slate-800 mb-4">
          Vertex Colors
        </h2>

        <div className="grid gap-3">
          {Array.from({ length: nodeCount }, (_, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="font-medium w-6">{i}</span>

              <select
                value={vertexColors[i]}
                onChange={(e) => {
                  const arr = [...vertexColors];
                  arr[i] = e.target.value;
                  setVertexColors(arr);
                }}
                className="w-40 px-3 py-2 border rounded-xl bg-white shadow-sm"
              >
                <option value="">Select Color</option>
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

        <label className="block font-medium text-slate-700">Start Vertex</label>
        <select
          value={startVertex}
          onChange={(e) => setStartVertex(e.target.value)}
          className={inputBox}
        >
          {Array.from({ length: nodeCount }, (_, i) => (
            <option key={i} value={String(i)}>
              {i}
            </option>
          ))}
        </select>

        <label className="block font-medium text-slate-700 mt-4">
          Target Vertex
        </label>
        <select
          value={targetVertex}
          onChange={(e) => setTargetVertex(e.target.value)}
          className={inputBox}
        >
          {Array.from({ length: nodeCount }, (_, i) => (
            <option key={i} value={String(i)}>
              {i}
            </option>
          ))}
        </select>
      </div>

      {/* PAWNS */}
      <div className="bg-white shadow-xl rounded-2xl p-6 border border-slate-200">
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
      </div>

      {error && <p className="text-red-500 text-center font-medium">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md font-semibold transition"
      >
        {loading ? "Starting..." : "Start Game"}
      </button>
    </form>
  );
}
