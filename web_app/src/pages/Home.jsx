import ConfigForm from "../components/ConfigForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200">
      {/* Modern Header */}
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 text-center shadow-lg">
        <h1 className="text-2xl font-bold tracking-wide">
          Two Pawn Game Simulator
        </h1>
      </header>

      {/* Center the Form -- but allow it to be full width for larger design */}
      <div className="flex justify-center px-4 py-10">
        <div className="w-full max-w-5xl">
          <ConfigForm />
        </div>
      </div>
    </div>
  );
}
