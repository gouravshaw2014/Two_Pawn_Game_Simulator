// import { useEffect, useState } from "react";
// import axios from "axios";
// import { API_BASE_URL } from "../api";

// export default function GameUI() {
//   const [state, setState] = useState(null);
//   const [actions, setActions] = useState([]);
//   const [image, setImage] = useState(null);
//   const [loading, setLoading] = useState(false);

//   // Load initial state from localStorage
//   useEffect(() => {
//     const saved = localStorage.getItem("game_state");
//     if (saved) {
//       const data = JSON.parse(saved);
//       setState(data.state);
//       setActions(data.valid_actions);
//       setImage(data.image);
//     }
//   }, []);

//   const sendAction = async (action) => {
//     setLoading(true);
//     try {
//       const res = await axios.post(`${API_BASE_URL}/action`, { action });
//       const newState = res.data.state;

//       setState(newState);
//       setActions(res.data.valid_actions);
//       setImage(res.data.image);

//       // WIN CHECKS HERE ⬇⬇⬇

//       // P1 WIN CONDITION: reached target & holds its pawn
//       if (
//         String(newState.p1_pos) ===
//         String(localStorage.getItem("target_vertex"))
//       ) {
//         setActions([]); // disable all buttons
//         return;
//       }

//       // P2 WIN CONDITION: no valid actions left
//       if (res.data.valid_actions.length === 0) {
//         setActions([]); // disable all buttons
//         return;
//       }
//     } catch (err) {
//       console.error(err);
//       alert("Action failed");
//     }
//     setLoading(false);
//   };

//   if (!state)
//     return <p className="text-center mt-10 text-gray-500">Loading game...</p>;

//   return (
//     <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
//       {/* LEFT SIDE - GRAPH IMAGE */}
//       <div className="bg-white shadow rounded-2xl p-4 flex items-center justify-center">
//         {image ? (
//           <img
//             src={`data:image/png;base64,${image}`}
//             alt="Game State"
//             className="rounded-xl shadow"
//           />
//         ) : (
//           <p className="text-gray-500">Loading image...</p>
//         )}
//       </div>

//       {/* RIGHT SIDE */}
//       <div className="flex flex-col gap-4">
//         {/* CURRENT STATE */}
//         <div className="bg-white shadow rounded-2xl p-4">
//           <h2 className="font-semibold mb-2">Current State</h2>
//           <p>
//             <strong>P1 Position:</strong> {state.p1_pos}
//           </p>
//           <p>
//             <strong>P1 Pawns:</strong> {state.p1_pawns.join(", ") || "None"}
//           </p>
//           <p>
//             <strong>P2 Position:</strong> {state.p2_pos || "None"}
//           </p>
//           <p>
//             <strong>P2 Pawns:</strong> {state.p2_pawns.join(", ") || "None"}
//           </p>
//           <p>
//             <strong>Turn:</strong> Player {state.current_player}
//           </p>
//           <p>
//             <strong>Phase:</strong> {state.phase}
//           </p>
//           {state.message && (
//             <p className="text-blue-600 mt-2">{state.message}</p>
//           )}
//         </div>

//         {/* VALID ACTIONS */}
//         <div className="bg-white shadow rounded-2xl p-4">
//           <h2 className="font-semibold mb-2">Valid Actions</h2>
//           <div className="flex flex-wrap gap-2">
//             {actions.length === 0 && (
//               <p className="text-red-600">No valid actions</p>
//             )}

//             {actions.map((act) => (
//               <button
//                 key={act}
//                 disabled={loading}
//                 onClick={() => sendAction(act)}
//                 className="bg-blue-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700"
//               >
//                 {act}
//               </button>
//             ))}
//           </div>
//         </div>

//         {/* GAME LOG */}
//         <div className="bg-white shadow rounded-2xl p-4">
//           <h2 className="font-semibold mb-2">Game Log</h2>
//           <ul className="text-sm space-y-1">
//             <li>{state.message}</li>
//           </ul>
//         </div>

//         {/* WIN/LOSE MESSAGES */}
//         {actions.length === 0 && state.phase === "move" && (
//           <div className="bg-red-100 text-red-700 p-4 font-bold rounded-xl text-center">
//             P2 Wins! (No valid actions)
//           </div>
//         )}

//         {String(state.p1_pos) ===
//           String(localStorage.getItem("target_vertex")) && (
//           <div className="bg-green-100 text-green-700 p-4 font-bold rounded-xl text-center">
//             🎉 P1 Wins! (Reached Target)
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../api";
import { useNavigate } from "react-router-dom";

export default function GameUI() {

  const navigate = useNavigate();
  const [state, setState] = useState(null);
  const [actions, setActions] = useState([]);
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  // NEW: continuous log
  const [log, setLog] = useState([]);

  // Load initial game state
  useEffect(() => {
    const saved = localStorage.getItem("game_state");
    if (saved) {
      const data = JSON.parse(saved);
      setState(data.state);
      setActions(data.valid_actions);
      setImage(data.image);

      // initialize log with first message
      if (data.state?.message) {
        setLog((prev) => [data.state.message, ...prev]);
      }
    }
  }, []);

  const sendAction = async (action) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/action`, { action });
      const newState = res.data.state;

      setState(newState);
      setActions(res.data.valid_actions);
      setImage(res.data.image);

      // push new message to log (newest first)
      if (newState.message) {
        setLog((prev) => [newState.message, ...prev]);
      }

      // Check win conditions
      if (
        String(newState.p1_pos) ===
        String(localStorage.getItem("target_vertex"))
      ) {
        setActions([]);
        return;
      }

      if (res.data.valid_actions.length === 0) {
        setActions([]);
        return;
      }
    } catch (err) {
      console.error(err);
      alert("Action failed");
    }
    setLoading(false);
  };

  if (!state)
    return (
      <p className="text-center mt-10 text-gray-500 animate-pulse">
        Loading game...
      </p>
    );

  // WIN STATES — Move these ABOVE page layout
  const p1Win =
    String(state.p1_pos) === String(localStorage.getItem("target_vertex"));

  const p2Win = actions.length === 0 && state.phase === "move";

  return (
    <div className="relative w-full">
      {/* WINNING BANNERS - FLOAT AT TOP CENTER */}
      {(p1Win || p2Win) && (
        <div className="fixed inset-0 flex items-center justify-center z-[9999] bg-black/25">
          <div
            className={`relative px-12 py-8 rounded-2xl shadow-2xl text-center text-2xl font-extrabold animate-pop
            ${
              p1Win ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
            }`}
          >
            {/* Close Button */}
            <button
              onClick={() => navigate("/")}
              className="absolute top-3 right-3 text-xl font-bold hover:opacity-60"
            >
              ✖
            </button>

            {/* Win Text */}
            <div className="mb-6">
              {p1Win
                ? "🎉 P1 Wins — Target Reached!"
                : "❌ P2 Wins — No Actions Left!"}
            </div>

            {/* New Game Button */}
            <button
              onClick={() => navigate("/")}
              className={`px-6 py-2 rounded-lg text-lg font-semibold shadow 
              ${p1Win ? "bg-green-600 text-white" : "bg-red-600 text-white"}
              hover:opacity-90`}
            >
              🔄 New Game
            </button>
          </div>
        </div>
      )}

      {/* MAIN LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full mt-4">
        {/* LEFT — GRAPH IMAGE */}
        <div className="bg-white shadow-lg rounded-xl p-3 flex items-center justify-center border border-slate-200">
          {image ? (
            <img
              src={`data:image/png;base64,${image}`}
              alt="Game State"
              className="rounded-xl shadow max-h-[600px] object-contain"
            />
          ) : (
            <p className="text-gray-400">Loading image...</p>
          )}
        </div>

        {/* RIGHT SIDE */}
        <div className="flex flex-col gap-4">
          {/* CURRENT STATE */}
          <div className="bg-white shadow-lg rounded-xl p-5 border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-800 mb-3">
              Current State
            </h2>

            <div className="grid grid-cols-2 gap-3">
              {/* PLAYER 1 */}
              <div className="bg-indigo-50 p-3 rounded-xl border border-indigo-200">
                <h3 className="font-bold text-indigo-700 mb-2 text-sm">
                  Player 1
                </h3>
                <p>
                  <span className="font-medium text-sm">Position:</span>{" "}
                  <span className="inline-block px-2 py-1 bg-indigo-600 text-white text-sm rounded-lg shadow">
                    {state.p1_pos}
                  </span>
                </p>
                <p className="mt-1">
                  <span className="font-medium text-sm">Pawns:</span>{" "}
                  {state.p1_pawns.length > 0 ? (
                    state.p1_pawns.map((p) => (
                      <span
                        key={p}
                        className="inline-block px-2 py-1 bg-indigo-200 text-indigo-800 rounded-lg text-xs mx-1"
                      >
                        {p}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 text-sm">None</span>
                  )}
                </p>
              </div>

              {/* PLAYER 2 */}
              <div className="bg-rose-50 p-3 rounded-xl border border-rose-200">
                <h3 className="font-bold text-rose-700 mb-2 text-sm">
                  Player 2
                </h3>
                <p>
                  <span className="font-medium text-sm">Position:</span>{" "}
                  <span className="inline-block px-2 py-1 bg-rose-600 text-white text-sm rounded-lg shadow">
                    {state.p2_pos ?? "None"}
                  </span>
                </p>
                <p className="mt-1">
                  <span className="font-medium text-sm">Pawns:</span>{" "}
                  {state.p2_pawns.length > 0 ? (
                    state.p2_pawns.map((p) => (
                      <span
                        key={p}
                        className="inline-block px-2 py-1 bg-rose-200 text-rose-800 rounded-lg text-xs mx-1"
                      >
                        {p}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 text-sm">None</span>
                  )}
                </p>
              </div>
            </div>

            {/* TURN + PHASE */}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="bg-slate-100 p-3 rounded-xl border border-slate-300 text-center">
                <p className="text-slate-500 text-xs">Turn</p>
                <span className="text-base font-bold">
                  Player {state.current_player}
                </span>
              </div>

              <div className="bg-slate-100 p-3 rounded-xl border border-slate-300 text-center">
                <p className="text-slate-500 text-xs">Phase</p>
                <span className="text-base font-bold">{state.phase}</span>
              </div>
            </div>
          </div>

          {/* ACTIONS */}
          <div className="bg-white shadow-lg rounded-xl p-5 border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-800 mb-3">
              Actions
            </h2>

            <div className="flex flex-wrap gap-2">
              {actions.length === 0 && (
                <p className="text-red-600 text-sm">No valid actions</p>
              )}

              {actions.map((act) => (
                <button
                  key={act}
                  disabled={loading}
                  onClick={() => sendAction(act)}
                  className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg shadow hover:bg-indigo-700 text-sm active:scale-95 transition"
                >
                  {act}
                </button>
              ))}
            </div>
          </div>

          {/* GAME LOG — NOW SCROLLABLE + CONTINUOUS */}
          <div className="bg-white shadow-lg rounded-xl p-5 border border-slate-200 h-56 flex flex-col">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">
              Game Log
            </h2>

            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {log.length === 0 && (
                <p className="text-slate-400 text-sm">No events yet.</p>
              )}

              {log.map((msg, idx) => (
                <div
                  key={idx}
                  className="p-2 bg-slate-100 rounded-lg border border-slate-300 text-sm text-slate-700"
                >
                  {msg}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
