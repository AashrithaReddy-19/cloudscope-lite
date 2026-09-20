import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Cloud, Plus } from "lucide-react";
import { api, apiErrorMessage, Project } from "../api";
import { Shell, LoadingState, ErrorState, EmptyState } from "../components";

const REGIONS = ["us-east-1", "ap-south-1"];

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [region, setRegion] = useState(REGIONS[0]);
  const [budget, setBudget] = useState("50");
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  function load() {
    setError("");
    setProjects(null);
    api
      .get<Project[]>("/api/projects")
      .then((r) => setProjects(r.data))
      .catch((err) => setError(apiErrorMessage(err, "Could not load projects.")));
  }

  useEffect(load, []);

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    setCreateError("");
    setCreating(true);
    try {
      const r = await api.post<Project>("/api/projects", {
        project_name: name,
        aws_region: region,
        monthly_budget: Number(budget),
      });
      setShowForm(false);
      setName("");
      navigate(`/projects/${r.data.id}`);
    } catch (err) {
      setCreateError(apiErrorMessage(err, "Could not create the project."));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Shell>
      <header>
        <div>
          <span className="eyebrow">OVERVIEW</span>
          <h1>Cloud cost clarity, before deployment.</h1>
        </div>
        <button className="button" onClick={() => setShowForm((v) => !v)}>
          <Plus size={16} /> New project
        </button>
      </header>

      {showForm && (
        <form className="panel form" onSubmit={createProject} style={{ margin: "20px 0" }}>
          <label>
            Project name
            <input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} />
          </label>
          <label>
            AWS region
            <select value={region} onChange={(e) => setRegion(e.target.value)}>
              {REGIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label>
            Monthly simulation budget (USD)
            <input value={budget} onChange={(e) => setBudget(e.target.value)} type="number" min="1" step="0.01" required />
          </label>
          <small>
            This is the budget used to PASS/WARNING/FAIL Terraform cost analyses for this project. It is separate from any
            real AWS Budget configured for the deployed infrastructure.
          </small>
          {createError && <div className="error">{createError}</div>}
          <button disabled={creating}>{creating ? "Creating..." : "Create project"}</button>
        </form>
      )}

      {error && <ErrorState message={error} onRetry={load} />}
      {!error && projects === null && <LoadingState label="Loading projects..." />}
      {!error && projects !== null && projects.length === 0 && (
        <EmptyState icon={<Cloud size={54} />} title="No projects yet">
          <p>Create a project to paste or upload Terraform and see a safe, pre-deployment cost estimate.</p>
        </EmptyState>
      )}
      {!error && projects !== null && projects.length > 0 && (
        <section className="cards">
          {projects.map((p) => (
            <article key={p.id} onClick={() => navigate(`/projects/${p.id}`)} style={{ cursor: "pointer" }}>
              <span>{p.aws_region}</span>
              <strong>{p.project_name}</strong>
              <small>Simulation budget: ${p.monthly_budget}/mo</small>
            </article>
          ))}
        </section>
      )}
    </Shell>
  );
}
