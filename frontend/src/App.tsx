import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ProjectDetail from "./pages/ProjectDetail";
import Forecast from "./pages/Forecast";
import AnalysisResult from "./pages/AnalysisResult";

function RequireAuth({ children }: { children: React.ReactElement }) {
  return localStorage.getItem("token") ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/projects/:id"
          element={
            <RequireAuth>
              <ProjectDetail />
            </RequireAuth>
          }
        />
        <Route
          path="/projects/:id/forecast"
          element={
            <RequireAuth>
              <Forecast />
            </RequireAuth>
          }
        />
        <Route
          path="/analyses/:id"
          element={
            <RequireAuth>
              <AnalysisResult />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
