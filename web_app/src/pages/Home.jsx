import ConfigForm from "../components/ConfigForm";

export default function Home() {
  return (
    <>
      <header className="bg-blue-600 text-white py-3 text-center font-semibold text-lg">
        Two Pawn Game Simulator
      </header>
      <div className="min-h-screen flex items-center justify-center bg-gray-100 p-6">
        <div className="w-full max-w-lg bg-white shadow-lg rounded-2xl p-6">
          <h1 className="text-2xl font-bold mb-6 text-center">
            Two Pawn Game Setup
          </h1>
          <ConfigForm />
        </div>
      </div>
    </>
  );
}
