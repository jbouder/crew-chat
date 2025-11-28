import { useState, useEffect, useCallback } from "react";
import { api } from "../api";
import type { Benefit, BenefitCategory } from "../types";
import "./Benefits.css";

interface BenefitsProps {
  memberId: number | null;
  enrolledBenefitIds: number[];
  onEnroll: (benefitId: number) => void;
}

function Benefits({ memberId, enrolledBenefitIds, onEnroll }: BenefitsProps) {
  const [benefits, setBenefits] = useState<Benefit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<
    BenefitCategory | "all"
  >("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [enrollingId, setEnrollingId] = useState<number | null>(null);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedBenefit, setSelectedBenefit] = useState<Benefit | null>(null);
  const [beneficiaryName, setBeneficiaryName] = useState("");
  const [beneficiaryRelationship, setBeneficiaryRelationship] = useState("");

  const loadBenefits = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getBenefits();
      setBenefits(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load benefits");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBenefits();
  }, [loadBenefits]);

  const categories: (BenefitCategory | "all")[] = [
    "all",
    "Life Insurance" as BenefitCategory,
    "Disability" as BenefitCategory,
    "Accident" as BenefitCategory,
    "Critical Illness" as BenefitCategory,
    "Supplemental" as BenefitCategory,
  ];

  const filteredBenefits = benefits.filter((benefit) => {
    const matchesCategory =
      selectedCategory === "all" || benefit.category === selectedCategory;
    const matchesSearch =
      searchQuery === "" ||
      benefit.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      benefit.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleEnrollClick = (benefit: Benefit) => {
    setSelectedBenefit(benefit);
    setBeneficiaryName("");
    setBeneficiaryRelationship("");
    setShowEnrollModal(true);
  };

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberId || !selectedBenefit) return;

    try {
      setEnrollingId(selectedBenefit.id);
      await api.createEnrollment(memberId, {
        benefit_id: selectedBenefit.id,
        beneficiary_name: beneficiaryName || undefined,
        beneficiary_relationship: beneficiaryRelationship || undefined,
      });
      onEnroll(selectedBenefit.id);
      setShowEnrollModal(false);
      alert("Successfully enrolled in " + selectedBenefit.name);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to enroll");
    } finally {
      setEnrollingId(null);
    }
  };

  const closeModal = () => {
    setShowEnrollModal(false);
    setSelectedBenefit(null);
  };

  if (loading) {
    return (
      <div className="benefits-loading">
        <div className="loading-spinner"></div>
        <p>Loading available benefits...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="benefits-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={loadBenefits} className="btn btn-primary">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="benefits-page">
      <header className="benefits-header">
        <h1>Available Benefits</h1>
        <p>
          Explore our comprehensive range of benefits designed for military
          families
        </p>
      </header>

      {/* Filters */}
      <div className="benefits-filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search benefits..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="category-filters">
          {categories.map((category) => (
            <button
              key={category}
              className={`category-btn ${
                selectedCategory === category ? "active" : ""
              }`}
              onClick={() => setSelectedCategory(category)}
            >
              {category === "all" ? "All Benefits" : category}
            </button>
          ))}
        </div>
      </div>

      {/* Benefits Grid */}
      <div className="benefits-grid">
        {filteredBenefits.length === 0 ? (
          <div className="no-benefits">
            <p>No benefits found matching your criteria.</p>
          </div>
        ) : (
          filteredBenefits.map((benefit) => {
            const isEnrolled = enrolledBenefitIds.includes(benefit.id);
            return (
              <div
                key={benefit.id}
                className={`benefit-card ${isEnrolled ? "enrolled" : ""}`}
              >
                <div className="benefit-card-header">
                  <span
                    className={`category-tag category-${benefit.category
                      .toLowerCase()
                      .replace(" ", "-")}`}
                  >
                    {benefit.category}
                  </span>
                  {benefit.requires_active_duty && (
                    <span className="active-duty-badge">Active Duty Only</span>
                  )}
                </div>

                <h3>{benefit.name}</h3>
                <p className="benefit-description">{benefit.description}</p>

                <div className="benefit-details">
                  <div className="detail">
                    <span className="detail-label">Coverage</span>
                    <span className="detail-value coverage">
                      {formatCurrency(benefit.coverage_amount)}
                    </span>
                  </div>
                  <div className="detail">
                    <span className="detail-label">Monthly Premium</span>
                    <span className="detail-value premium">
                      {formatCurrency(benefit.monthly_premium)}/mo
                    </span>
                  </div>
                  {benefit.deductible > 0 && (
                    <div className="detail">
                      <span className="detail-label">Deductible</span>
                      <span className="detail-value">
                        {formatCurrency(benefit.deductible)}
                      </span>
                    </div>
                  )}
                  <div className="detail">
                    <span className="detail-label">Age Range</span>
                    <span className="detail-value">
                      {benefit.min_age} - {benefit.max_age} years
                    </span>
                  </div>
                </div>

                <div className="benefit-card-footer">
                  {isEnrolled ? (
                    <span className="enrolled-badge">✓ Enrolled</span>
                  ) : memberId ? (
                    <button
                      className="btn btn-primary"
                      onClick={() => handleEnrollClick(benefit)}
                      disabled={enrollingId === benefit.id}
                    >
                      {enrollingId === benefit.id
                        ? "Enrolling..."
                        : "Enroll Now"}
                    </button>
                  ) : (
                    <span className="login-prompt">Log in to enroll</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Enrollment Modal */}
      {showEnrollModal && selectedBenefit && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal}>
              ×
            </button>
            <h2>Enroll in {selectedBenefit.name}</h2>
            <p className="modal-subtitle">
              Complete the form below to enroll in this benefit.
            </p>

            <div className="modal-benefit-summary">
              <div className="summary-item">
                <span>Coverage:</span>
                <strong>
                  {formatCurrency(selectedBenefit.coverage_amount)}
                </strong>
              </div>
              <div className="summary-item">
                <span>Monthly Premium:</span>
                <strong>
                  {formatCurrency(selectedBenefit.monthly_premium)}
                </strong>
              </div>
            </div>

            <form onSubmit={handleEnrollSubmit}>
              <div className="form-group">
                <label htmlFor="beneficiaryName">
                  Beneficiary Name (Optional)
                </label>
                <input
                  id="beneficiaryName"
                  type="text"
                  value={beneficiaryName}
                  onChange={(e) => setBeneficiaryName(e.target.value)}
                  placeholder="Enter beneficiary name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="beneficiaryRelationship">
                  Relationship (Optional)
                </label>
                <select
                  id="beneficiaryRelationship"
                  value={beneficiaryRelationship}
                  onChange={(e) => setBeneficiaryRelationship(e.target.value)}
                >
                  <option value="">Select relationship</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Child">Child</option>
                  <option value="Parent">Parent</option>
                  <option value="Sibling">Sibling</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={closeModal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={enrollingId !== null}
                >
                  {enrollingId !== null
                    ? "Processing..."
                    : "Confirm Enrollment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Benefits;
