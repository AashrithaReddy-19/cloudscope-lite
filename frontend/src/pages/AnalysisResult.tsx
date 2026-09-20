import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, Download } from "lucide-react";
import { api, apiErrorMessage, AnalysisReport } from "../api";
import { Shell, LoadingState, ErrorState, money } from "../components";

async function download(analysisId: string, format: "json" | "csv") {
  const response = await api.get(`/api/analyses/${analysisId}/download/${format}`, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis-${analysisId}.${format}`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function AnalysisResult() {
  const { id } = useParams();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState("");
  const [scenarioTab, setScenarioTab] = useState<"low" | "medium" | "high">("high");

  function load() {
    setError("");
    setReport(null);
    api
      .get<AnalysisReport>(`/api/analyses/${id}/report`)
      .then((r) => setReport(r.data))
      .catch((err) => setError(apiErrorMessage(err, "Could not load this analysis.")));
  }

  useEffect(load, [id]);

  if (error) return <Shell><ErrorState message={error} onRetry={load} /></Shell>;
  if (!report) return <Shell><LoadingState label="Loading analysis..." /></Shell>;

  const policy = report.budget_policy;

  return (
    <Shell>
      <h1>Analysis result</h1>
      <p className="eyebrow">
        Pricing effective date: {report.pricing_effective_date} ({report.pricing_currency}) &middot; Source: {report.pricing_source}
      </p>

      <section className="grid">
        <section className="panel result">
          <span>MONTHLY ESTIMATE</span>
          <h2>{money(report.total_monthly_cost)}</h2>
          <b className={policy.status.toLowerCase()}>{policy.status}</b>
          <p>{policy.message}</p>
          {policy.status !== "NOT_CONFIGURED" && (
            <small>
              Budget {money(policy.budget)} · Usage {policy.budget_usage_percentage}% · Remaining {money(policy.remaining_budget ?? 0)}
            </small>
          )}
        </section>

        <section className="panel">
          <h2>Downloads</h2>
          <p>Export this report for offline review or a lab submission.</p>
          <button onClick={() => download(id!, "json")}>
            <Download size={16} /> Download JSON
          </button>
          <button onClick={() => download(id!, "csv")} style={{ marginLeft: 10 }}>
            <Download size={16} /> Download CSV
          </button>
        </section>
      </section>

      {report.unsupported_warnings.length > 0 && (
        <section className="panel warning-panel">
          <h2>
            <AlertTriangle size={18} /> Unsupported resources
          </h2>
          <ul>
            {report.unsupported_warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="panel" style={{ marginTop: 20 }}>
        <h2>Per-resource breakdown</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Resource</th>
              <th>Type</th>
              <th>Rate</th>
              <th>Formula</th>
              <th>Estimated cost</th>
            </tr>
          </thead>
          <tbody>
            {report.resources.map((r) => (
              <React.Fragment key={r.resource_name}>
                <tr>
                  <td>{r.resource_name}</td>
                  <td>{r.resource_type}</td>
                  <td>{r.pricing_unit}</td>
                  <td>
                    <code>{r.formula}</code>
                  </td>
                  <td>{money(r.estimated_cost)}</td>
                </tr>
                {r.warnings.length > 0 && (
                  <tr>
                    <td colSpan={5} className="warning">
                      {r.warnings.map((w) => w.message).join(" ")}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        <small>
          Assumptions: {[...new Set(report.resources.flatMap((r) => r.assumptions))].join(", ") || "none"}
        </small>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <h2>Workload comparison</h2>
        <div className="tabs">
          {(["low", "medium", "high"] as const).map((s) => (
            <button
              key={s}
              className={s === scenarioTab ? "tab active" : "tab"}
              onClick={() => setScenarioTab(s)}
            >
              {s}
            </button>
          ))}
        </div>
        <p>
          Total for <b>{scenarioTab}</b> workload: {money(report.scenario_comparison[scenarioTab].total_monthly_cost)}
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Total monthly cost</th>
            </tr>
          </thead>
          <tbody>
            {(["low", "medium", "high"] as const).map((s) => (
              <tr key={s}>
                <td>{s}</td>
                <td>{money(report.scenario_comparison[s].total_monthly_cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {report.recommendations.length > 0 && (
        <section className="panel" style={{ marginTop: 20 }}>
          <h2>Recommendations</h2>
          {report.recommendations.map((r) => (
            <p key={r.resource_name}>
              <b>{r.resource_name}:</b> {r.suggestion} <small>({r.confidence} confidence)</small>
              <br />
              <small>
                {r.explanation}
                {r.estimated_savings ? ` Estimated savings: ${money(r.estimated_savings)}.` : ""}
              </small>
            </p>
          ))}
        </section>
      )}
    </Shell>
  );
}
