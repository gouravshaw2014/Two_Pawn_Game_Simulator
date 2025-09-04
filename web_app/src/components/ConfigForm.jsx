import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function ConfigForm() {
  const [ownership, setOwnership] = useState("MVPP");
  const [rule, setRule] = useState("always-grabbing");
  const [kValue, setKValue] = useState(2);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // Later: send to backend
    navigate("/simulator");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block font-medium mb-1">Ownership Model</label>
        <select
          value={ownership}
          onChange={(e) => setOwnership(e.target.value)}
          className="w-full border rounded-lg p-2"
        >
          <option value="OVPP">One Vertex per Pawn (OVPP)</option>
          <option value="MVPP">Multiple Vertices per Pawn (MVPP)</option>
          <option value="OMVPP">Overlapping Vertices (OMVPP)</option>
        </select>
      </div>

      <div>
        <label className="block font-medium mb-1">Grabbing Rule</label>
        <select
          value={rule}
          onChange={(e) => setRule(e.target.value)}
          className="w-full border rounded-lg p-2"
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
          <label className="block font-medium mb-1">K Value</label>
          <input
            type="number"
            min="1"
            value={kValue}
            onChange={(e) => setKValue(e.target.value)}
            className="w-full border rounded-lg p-2"
          />
        </div>
      )}

      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
      >
        Start Game
      </button>
    </form>
  );
}
