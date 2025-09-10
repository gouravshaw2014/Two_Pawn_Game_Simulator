import React from "react";

export default function PawnStatus() {
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <h2 className="text-lg font-semibold mb-2">Pawn Status</h2>
      <p className="text-sm text-gray-700">🎮 P1 has: Red, Blue</p>
      <p className="text-sm text-gray-700">🤖 P2 has: Green</p>
    </div>
  );
}
