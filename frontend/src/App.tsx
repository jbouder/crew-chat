import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navigation from "./components/Navigation";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Benefits from "./pages/Benefits";
import { api } from "./api";
import type { Member, Enrollment } from "./types";
import "./App.css";

function App() {
  const [member, setMember] = useState<Member | null>(null);
  const [enrolledBenefitIds, setEnrolledBenefitIds] = useState<number[]>([]);

  const loadEnrollments = useCallback(async () => {
    if (!member) return;
    try {
      const enrollments = await api.getMemberEnrollments(member.id);
      setEnrolledBenefitIds(enrollments.map((e: Enrollment) => e.benefit_id));
    } catch (err) {
      console.error("Failed to load enrollments:", err);
    }
  }, [member]);

  useEffect(() => {
    loadEnrollments();
  }, [loadEnrollments]);

  const handleLogin = (loggedInMember: Member) => {
    setMember(loggedInMember);
  };

  const handleLogout = () => {
    setMember(null);
    setEnrolledBenefitIds([]);
  };

  const handleEnroll = (benefitId: number) => {
    setEnrolledBenefitIds((prev) => [...prev, benefitId]);
  };

  return (
    <BrowserRouter>
      <div className="app">
        <Navigation member={member} onLogout={handleLogout} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route
              path="/login"
              element={
                member ? (
                  <Navigate to="/dashboard" />
                ) : (
                  <Login onLogin={handleLogin} />
                )
              }
            />
            <Route
              path="/dashboard"
              element={
                member ? (
                  <Dashboard memberId={member.id} />
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route
              path="/benefits"
              element={
                <Benefits
                  memberId={member?.id || null}
                  enrolledBenefitIds={enrolledBenefitIds}
                  onEnroll={handleEnroll}
                />
              }
            />
          </Routes>
        </main>
        <footer className="footer">
          <p>© 2024 Patriot Life Insurance. Serving Those Who Serve.</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
