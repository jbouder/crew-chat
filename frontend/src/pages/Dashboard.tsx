import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { DashboardData } from "../types";
import "./Dashboard.css";

interface DashboardProps {
  memberId: number;
}

function Dashboard({ memberId }: DashboardProps) {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getMemberDashboard(memberId);
      setDashboard(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [memberId]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleCancelEnrollment = async (enrollmentId: number) => {
    if (
      !confirm(
        "Are you sure you want to cancel this benefit? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      await api.cancelEnrollment(memberId, enrollmentId);
      loadDashboard();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to cancel enrollment");
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={loadDashboard} className="btn btn-primary">
          Try Again
        </button>
      </div>
    );
  }

  if (!dashboard) {
    return null;
  }

  const { member, enrollments, total_monthly_premium, total_coverage } =
    dashboard;

  return (
    <div className="dashboard">
      {/* Welcome Section */}
      <section className="welcome-section">
        <div className="welcome-content">
          <h1>Welcome, {member.first_name}!</h1>
          <p className="member-number">Member # {member.member_number}</p>
        </div>
        <div className="quick-actions">
          <Link to="/benefits" className="btn btn-primary">
            Browse Benefits
          </Link>
        </div>
      </section>

      {/* Summary Cards */}
      <section className="summary-section">
        <div className="summary-card">
          <span className="summary-label">Total Coverage</span>
          <span className="summary-value">
            {formatCurrency(total_coverage)}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Monthly Premium</span>
          <span className="summary-value">
            {formatCurrency(total_monthly_premium)}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Active Benefits</span>
          <span className="summary-value">{enrollments.length}</span>
        </div>
        <div className="summary-card status-card">
          <span className="summary-label">Membership Status</span>
          <span
            className={`status-badge status-${member.membership_status.toLowerCase()}`}
          >
            {member.membership_status}
          </span>
        </div>
      </section>

      {/* Member Information */}
      <section className="info-section">
        <h2>Member Information</h2>
        <div className="info-grid">
          <div className="info-card">
            <h3>Personal Details</h3>
            <div className="info-row">
              <span className="info-label">Name:</span>
              <span className="info-value">
                {member.first_name} {member.last_name}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">Email:</span>
              <span className="info-value">{member.email}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Phone:</span>
              <span className="info-value">
                {member.phone || "Not provided"}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">Address:</span>
              <span className="info-value">
                {member.address
                  ? `${member.address}, ${member.city}, ${member.state} ${member.zip_code}`
                  : "Not provided"}
              </span>
            </div>
          </div>
          <div className="info-card">
            <h3>Military Service</h3>
            <div className="info-row">
              <span className="info-label">Branch:</span>
              <span className="info-value">{member.military_branch}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Rank:</span>
              <span className="info-value">
                {member.rank || "Not provided"}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">Status:</span>
              <span className="info-value">
                {member.is_active_duty ? "Active Duty" : "Veteran/Reserve"}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">Service Start:</span>
              <span className="info-value">
                {member.service_start_date
                  ? formatDate(member.service_start_date)
                  : "Not provided"}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Active Enrollments */}
      <section className="enrollments-section">
        <div className="section-header">
          <h2>Your Active Benefits</h2>
          <Link to="/benefits" className="btn btn-secondary">
            + Add Benefit
          </Link>
        </div>

        {enrollments.length === 0 ? (
          <div className="no-enrollments">
            <p>You don&apos;t have any active benefits yet.</p>
            <Link to="/benefits" className="btn btn-primary">
              Browse Available Benefits
            </Link>
          </div>
        ) : (
          <div className="enrollments-grid">
            {enrollments.map((enrollment) => (
              <div key={enrollment.id} className="enrollment-card">
                <div className="enrollment-header">
                  <h3>{enrollment.benefit?.name || "Benefit"}</h3>
                  <span
                    className={`category-badge category-${enrollment.benefit?.category
                      .toLowerCase()
                      .replace(" ", "-")}`}
                  >
                    {enrollment.benefit?.category}
                  </span>
                </div>
                <div className="enrollment-details">
                  <div className="detail-row">
                    <span className="detail-label">Coverage:</span>
                    <span className="detail-value">
                      {formatCurrency(enrollment.coverage_amount)}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Monthly Premium:</span>
                    <span className="detail-value">
                      {formatCurrency(enrollment.monthly_premium)}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Effective Date:</span>
                    <span className="detail-value">
                      {formatDate(enrollment.effective_date)}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Beneficiary:</span>
                    <span className="detail-value">
                      {enrollment.beneficiary_name
                        ? `${enrollment.beneficiary_name} (${enrollment.beneficiary_relationship})`
                        : "Not designated"}
                    </span>
                  </div>
                </div>
                <div className="enrollment-actions">
                  <button
                    className="btn btn-danger btn-small"
                    onClick={() => handleCancelEnrollment(enrollment.id)}
                  >
                    Cancel Benefit
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Dashboard;
