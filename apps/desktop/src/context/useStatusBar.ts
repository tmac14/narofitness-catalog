import { useContext } from "react";
import { StatusBarContext } from "@/context/statusBarContextShared";

export function useStatusBar() {
  const ctx = useContext(StatusBarContext);
  if (!ctx) {
    throw new Error("useStatusBar must be used within StatusBarProvider");
  }
  return ctx;
}
