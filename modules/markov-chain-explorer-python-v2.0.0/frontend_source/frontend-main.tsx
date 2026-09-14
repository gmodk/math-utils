import React from "react";
import ReactDOM from "react-dom/client";

import "@/styles/globals.css";
import { MarkovLab } from "@/components/markov-lab";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MarkovLab />
  </React.StrictMode>,
);
