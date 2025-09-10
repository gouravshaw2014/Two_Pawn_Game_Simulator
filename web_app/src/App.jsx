import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Simulator from "./pages/Simulator";
import "./App.css";

export default function App() {
  return (
    <>
      {/* <h1 className="text-2xl font-bold">Hello World</h1> */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/simulator" element={<Simulator />} />
      </Routes>
    </>
  );
}
