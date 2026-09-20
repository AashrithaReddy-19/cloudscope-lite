import React from "react";
import { NavLink } from "react-router-dom";
import { Cloud, LayoutDashboard, LogOut } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      <aside>
        <h2>
          <Cloud /> CloudScope
        </h2>
        <NavLink to="/">
          <LayoutDashboard />
          Projects
        </NavLink>
        <button
          className="logout"
          onClick={() => {
            localStorage.clear();
            location.href = "/login";
          }}
        >
          <LogOut />
          Sign out
        </button>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <section className="panel empty">
      <p>{label}</p>
    </section>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <section className="panel empty error-panel">
      <p className="error">{message}</p>
      {onRetry && (
        <button className="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </section>
  );
}

export function EmptyState({ icon, title, children }: { icon?: React.ReactNode; title: string; children?: React.ReactNode }) {
  return (
    <section className="panel empty">
      {icon}
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function money(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : "-";
}
