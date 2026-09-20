import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Cloud } from "lucide-react";
import { api, apiErrorMessage } from "../api";

export default function Login() {
  const [email, setEmail] = useState("demo@cloudscope.example.com");
  const [password, setPassword] = useState("CloudScopeDemo1!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const r = await api.post("/api/auth/login", { email, password });
      localStorage.setItem("token", r.data.access_token);
      navigate("/");
    } catch (err) {
      setError(apiErrorMessage(err, "Login failed. Register an account or seed the demo user first."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login">
      <form className="panel auth" onSubmit={submit}>
        <Cloud size={42} />
        <h1>CloudScope Lite</h1>
        <p>Pre-deployment AWS cost simulator</p>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required minLength={8} />
        </label>
        {error && <div className="error">{error}</div>}
        <button disabled={loading}>{loading ? "Signing in..." : "Sign in"}</button>
        <small>
          No account? <Link to="/register">Register</Link>
        </small>
      </form>
    </main>
  );
}
