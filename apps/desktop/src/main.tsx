import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        theme="dark"
        richColors
        position="bottom-right"
        toastOptions={{
          classNames: {
            toast: "bg-card border-border text-foreground shadow-md",
            success: "border-success/30 bg-card text-foreground",
            error: "border-destructive/30 bg-card text-foreground",
            warning: "border-warning/30 bg-card text-foreground",
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>,
);
