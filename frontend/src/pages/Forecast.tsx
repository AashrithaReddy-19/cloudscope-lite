import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { TrendingUp } from "lucide-react";
import { api, apiErrorMessage } from "../api";
import { Shell, LoadingState, ErrorState, EmptyState } from "../components";

interface ForecastResult {
  linear_regression: number[];
  moving_average: number[];
  metrics: { mae: number; rmse: number; mape: number | null } | null;
  limitations: string[];
}

interface Anomaly {
  date: string;
  actual_cost: number;
  expected_range: [number, number];
  difference: number;
  detection_method: string;
  explanation: string;
}

export default function Forecast() {
  const { id } = useParams();
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [forecastError, setForecastError] = useState("");
  const [forecastNotReady, setForecastNotReady] = useState("");
  const [anomalies, setAnomalies] = useState<Anomaly[] | null>(null);
  const [anomalyError, setAnomalyError] = useState("");

  function loadForecast() {
    setForecastError("");
    setForecastNotReady("");
    setForecast(null);
    api
      .get<ForecastResult>(`/api/projects/${id}/forecast`)
      .then((r) => setForecast(r.data))
      .catch((err) => {
        if (err.response?.status === 422) setForecastNotReady(apiErrorMessage(err));
        else setForecastError(apiErrorMessage(err, "Could not load the forecast."));
      });
  }

  function loadAnomalies() {
    setAnomalyError("");
    api
      .get<Anomaly[]>(`/api/projects/${id}/anomalies`)
      .then((r) => setAnomalies(r.data))
      .catch((err) => setAnomalyError(apiErrorMessage(err, "Could not load anomaly detection results.")));
  }

  useEffect(() => {
    loadForecast();
    loadAnomalies();
  }, [id]);

  return (
    <Shell>
      <h1>
        <TrendingUp /> Forecast &amp; anomalies
      </h1>
      <p>
        These are statistical estimates derived from the historical costs you upload for this project - they are not
        AWS billing predictions and carry no accuracy guarantee.
      </p>

      <section className="panel" style={{ marginTop: 20 }}>
        <h2>Forecast (next 3 periods)</h2>
        {forecastError && <ErrorState message={forecastError} onRetry={loadForecast} />}
        {forecastNotReady && (
          <EmptyState icon={<TrendingUp size={48} />} title="Not enough data yet">
            <p>{forecastNotReady} Upload a historical-cost CSV from the project page first.</p>
          </EmptyState>
        )}
        {!forecastError && !forecastNotReady && forecast === null && <LoadingState label="Loading forecast..." />}
        {forecast && (
          <>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>+1</th>
                  <th>+2</th>
                  <th>+3</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Linear regression</td>
                  {forecast.linear_regression.map((v, i) => (
                    <td key={i}>${v.toFixed(2)}</td>
                  ))}
                </tr>
                <tr>
                  <td>Moving average</td>
                  {forecast.moving_average.map((v, i) => (
                    <td key={i}>${v.toFixed(2)}</td>
                  ))}
                </tr>
              </tbody>
            </table>
            {forecast.metrics ? (
              <p>
                Backtested accuracy (12+ records): MAE ${forecast.metrics.mae}, RMSE ${forecast.metrics.rmse}
                {forecast.metrics.mape !== null && `, MAPE ${forecast.metrics.mape}%`}
              </p>
            ) : (
              <p>Upload 12+ records to see backtested accuracy metrics (MAE/RMSE/MAPE).</p>
            )}
            <ul>
              {forecast.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <h2>Anomaly warnings (IQR method)</h2>
        {anomalyError && <ErrorState message={anomalyError} onRetry={loadAnomalies} />}
        {!anomalyError && anomalies === null && <LoadingState label="Checking for anomalies..." />}
        {!anomalyError && anomalies !== null && anomalies.length === 0 && <p>No statistical anomalies detected in the uploaded history.</p>}
        {!anomalyError && anomalies !== null && anomalies.length > 0 && (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Actual cost</th>
                <th>Expected range</th>
                <th>Difference</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a) => (
                <tr key={a.date}>
                  <td>{a.date}</td>
                  <td>${a.actual_cost.toFixed(2)}</td>
                  <td>
                    ${a.expected_range[0].toFixed(2)} - ${a.expected_range[1].toFixed(2)}
                  </td>
                  <td>${a.difference.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <small>A flagged date is a statistical deviation from recent history, not proof of a billing error.</small>
      </section>
    </Shell>
  );
}
