import React from "react";

export default function ActionPanel() {
  const actions = ["Move A → C", "Move A → E", "Grab Red Pawn"]; // placeholder

  return (
    <div className="bg-white rounded-xl shadow p-4 flex flex-col space-y-2">
      <h2 className="text-lg font-semibold mb-2">Available Actions</h2>
      {actions.map((action, idx) => (
        <button
          key={idx}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
        >
          {action}
        </button>
      ))}
    </div>
  );
}
