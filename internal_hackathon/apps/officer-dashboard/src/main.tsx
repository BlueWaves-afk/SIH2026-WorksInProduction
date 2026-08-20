import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import { OfficerAuthGate } from "./auth/OfficerAuthGate";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <OfficerAuthGate><App /></OfficerAuthGate>
  </StrictMode>,
);
