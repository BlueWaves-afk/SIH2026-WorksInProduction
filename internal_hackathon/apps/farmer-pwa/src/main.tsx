import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import { FarmerAuthGate } from "./auth/FarmerAuthGate";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <FarmerAuthGate><App /></FarmerAuthGate>
  </StrictMode>,
);
