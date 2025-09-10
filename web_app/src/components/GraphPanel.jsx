import React from "react";
import placeholder from "../assets/react.svg";

export default function GraphPanel() {
  return (
    <div className="w-full h-[400px] flex items-center justify-center">
      <img
        src={placeholder}
        alt="Graph placeholder"
        className="max-h-full object-contain"
      />
    </div>
  );
}
