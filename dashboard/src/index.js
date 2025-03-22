import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";
import { MetamorphicProvider } from "./context/MetamorphicContext";

// Create root element
const root = ReactDOM.createRoot(document.getElementById("root"));

// Render app with providers
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <MetamorphicProvider>
        <App />
      </MetamorphicProvider>
    </BrowserRouter>
  </React.StrictMode>
);
