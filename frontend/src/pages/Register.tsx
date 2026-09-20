import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Cloud } from "lucide-react";
import { api, apiErrorMessage } from "../api";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const r = await api.post("/api/auth/register", { name, email, password });
      localStorage.setItem("token", r.data.access_token);
      navigate("/");
    } catch (err) {
      setError(apiErrorMessage(err, "Registration failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login">
      <form className="panel auth" onSubmit={submit}>
        <Cloud size={42} />
        <h1>Create an account</h1>
        <p>For classroom and demonstration use only.</p>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} minLength={2} required />
        </label>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required minLength={8} />
        </label>
        {error && <div className="error">{error}</div>}
        <button disabled={loading}>{loading ? "Creating account..." : "Register"}</button>
        <small>
          Already have an account? <Link to="/login">Sign in</Link>
        </small>
      </form>
    </main>
  );
}
