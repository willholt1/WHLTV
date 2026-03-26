import type { ReactNode } from "react";
import { NavBar } from "./NavBar";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div style={{ padding: "1rem" }}>
      <NavBar />
      <main>{children}</main>
    </div>
  );
}