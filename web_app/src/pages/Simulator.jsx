import GameUI from "../components/GameUI";

export default function Simulator() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-blue-600 text-white py-3 text-center font-semibold text-lg">
        Two Pawn Game Simulator
      </header>
      <main className="flex-1 p-4 flex items-start gap-6">
        <GameUI />
      </main>
    </div>
  );
}
