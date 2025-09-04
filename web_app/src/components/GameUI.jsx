import React from "react";
export default function GameUI() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* Graph / Visualization placeholder */}
      <div className="bg-white shadow rounded-2xl p-4 flex items-center justify-center">
        <p className="text-gray-500">[Graph Visualization Here]</p>
      </div>

      {/* Right side: game info */}
      <div className="flex flex-col gap-4">
        <div className="bg-white shadow rounded-2xl p-4">
          <h2 className="font-semibold mb-2">Current State</h2>
          <p>P1 Position: Start</p>
          <p>P1 Pawns: Red, Blue</p>
          <p>P2 Position: None</p>
          <p>P2 Pawns: Green</p>
        </div>

        <div className="bg-white shadow rounded-2xl p-4">
          <h2 className="font-semibold mb-2">Valid Actions</h2>
          <div className="flex flex-wrap gap-2">
            <button className="bg-blue-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700">
              Move A
            </button>
            <button className="bg-blue-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700">
              Grab Red
            </button>
          </div>
        </div>

        <div className="bg-white shadow rounded-2xl p-4">
          <h2 className="font-semibold mb-2">Game Log</h2>
          <ul className="text-sm space-y-1">
            <li>Player 1 moves to A</li>
            <li>Player 2 grabs Red</li>
          </ul>
        </div>

        <div className="bg-white shadow rounded-2xl p-4 text-center font-bold text-green-600">
          P1 Wins!
        </div>
      </div>
    </div>
  );
}
