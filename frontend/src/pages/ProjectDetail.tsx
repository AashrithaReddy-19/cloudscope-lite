import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ScanLine, TrendingUp, UploadCloud } from "lucide-react";
import { api, apiErrorMessage, Project } from "../api";
import { Shell, LoadingState, ErrorState } from "../components";

interface AnalysisSummary {
  analysis_id: number;
  terraform_filename: string;
  workload_scenario: string;
  estimated_monthly_cost: number;
  budget_status: string;
  pricing_effective_date: string;
  created_at: string;
}

const MAX_TF_BYTES = 1024 * 1024;

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [projectError, setProjectError] = useState("");

  const [tf, setTf] = useState('resource "aws_instance" "web" {\n  instance_type = "t3.micro"\n  root_volume_size_gb = 8\n}');
  const [file, setFile] = useState<File | null>(null);
  const [scenario, setScenario] = useState("high");
  const [uploadError, setUploadError] = useState("");
  const [analyzeError, setAnalyzeError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);

  const [history, setHistory] = useState<AnalysisSummary[] | null>(null);
  const [historyError, setHistoryError] = useState("");

  const [costFile, setCostFile] = useState<File | null>(null);
  const [costUploadMessage, setCostUploadMessage] = useState("");
  const [costUploadError, setCostUploadError] = useState("");

  function loadProject() {
    setProjectError("");
    setProject(null);
    api
      .get<Project>(`/api/projects/${id}`)
      .then((r) => setProject(r.data))
      .catch((err) => setProjectError(apiErrorMessage(err, "Could not load this project.")));
  }

  function loadHistory() {
    setHistoryError("");
    api
      .get<AnalysisSummary[]>(`/api/projects/${id}/analyses`)
      .then((r) => setHistory(r.data))
      .catch((err) => setHistoryError(apiErrorMessage(err, "Could not load analysis history.")));
  }

  useEffect(() => {
    loadProject();
    loadHistory();
  }, [id]);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setUploadError("");
    const f = e.target.files?.[0] ?? null;
    if (f) {
      if (!f.name.toLowerCase().endsWith(".tf")) {
        setUploadError("Only .tf files are accepted.");
        setFile(null);
        return;
      }
      if (f.size > MAX_TF_BYTES) {
        setUploadError("File exceeds the 1 MB limit.");
        setFile(null);
        return;
      }
    }
    setFile(f);
  }

  async function runAnalysis() {
    setAnalyzeError("");
    setAnalyzing(true);
    try {
      const form = new FormData();
      form.append("project_id", String(id));
      form.append("workload_scenario", scenario);
      if (file) form.append("file", file);
      else form.append("terraform_text", tf);
      const r = await api.post("/api/analyze", form);
      navigate(`/analyses/${r.data.analysis_id}`);
    } catch (err) {
      setAnalyzeError(apiErrorMessage(err, "Analysis failed."));
    } finally {
      setAnalyzing(false);
    }
  }

  async function uploadCosts(e: React.FormEvent) {
    e.preventDefault();
    setCostUploadError("");
    setCostUploadMessage("");
    if (!costFile) return;
    try {
      const form = new FormData();
      form.append("file", costFile);
      const r = await api.post(`/api/projects/${id}/history/upload`, form);
      setCostUploadMessage(`Imported ${r.data.imported} historical cost records.`);
    } catch (err) {
      setCostUploadError(apiErrorMessage(err, "Could not import the CSV file."));
    }
  }

  if (projectError) return <Shell><ErrorState message={projectError} onRetry={loadProject} /></Shell>;
  if (!project) return <Shell><LoadingState label="Loading project..." /></Shell>;

  return (
    <Shell>
      <h1>{project.project_name}</h1>
      <p className="eyebrow">
        {project.aws_region.toUpperCase()} · Simulation budget ${project.monthly_budget}/mo
      </p>

      <div className="grid">
        <section className="panel form">
          <h2>New analysis</h2>
          <label>
            Workload scenario
            <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <label>
            Upload a .tf file (optional - clears the pasted text below)
            <input type="file" accept=".tf" onChange={onFileChange} />
          </label>
          {file && <small>Selected: {file.name} ({file.size} bytes)</small>}
          {uploadError && <div className="error">{uploadError}</div>}
          <label>
            Or paste Terraform code
            <textarea value={tf} onChange={(e) => setTf(e.target.value)} disabled={!!file} />
          </label>
          <small>
            Only aws_instance, aws_ebs_volume, aws_s3_bucket and aws_db_instance are priced. Terraform is parsed as text
            only - init/plan/apply are never run against what you submit here.
          </small>
          {analyzeError && <div className="error">{analyzeError}</div>}
          <button onClick={runAnalysis} disabled={analyzing}>
            <ScanLine size={16} /> {analyzing ? "Analyzing..." : "Analyze safely"}
          </button>
        </section>

        <section className="panel form">
          <h2>
            <TrendingUp size={18} /> Historical costs
          </h2>
          <p>Upload a CSV with date,cost columns to enable forecasting and anomaly detection for this project.</p>
          <form onSubmit={uploadCosts}>
            <label>
              CSV file
              <input type="file" accept=".csv" onChange={(e) => setCostFile(e.target.files?.[0] ?? null)} />
            </label>
            {costUploadError && <div className="error">{costUploadError}</div>}
            {costUploadMessage && <div className="pass">{costUploadMessage}</div>}
            <button disabled={!costFile}>
              <UploadCloud size={16} /> Upload
            </button>
          </form>
          <button className="button" onClick={() => navigate(`/projects/${id}/forecast`)} style={{ marginTop: 12 }}>
            View forecast &amp; anomalies
          </button>
        </section>
      </div>

      <section className="panel" style={{ marginTop: 24 }}>
        <h2>Analysis history</h2>
        {historyError && <ErrorState message={historyError} onRetry={loadHistory} />}
        {!historyError && history === null && <LoadingState label="Loading history..." />}
        {!historyError && history !== null && history.length === 0 && <p>No analyses yet - run one above.</p>}
        {!historyError && history !== null && history.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Source</th>
                <th>Scenario</th>
                <th>Estimated cost</th>
                <th>Budget status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((a) => (
                <tr key={a.analysis_id} className="clickable-row" onClick={() => navigate(`/analyses/${a.analysis_id}`)}>
                  <td>{new Date(a.created_at).toLocaleString()}</td>
                  <td>{a.terraform_filename}</td>
                  <td>{a.workload_scenario}</td>
                  <td>${a.estimated_monthly_cost.toFixed(2)}</td>
                  <td className={a.budget_status.toLowerCase()}>{a.budget_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </Shell>
  );
}
