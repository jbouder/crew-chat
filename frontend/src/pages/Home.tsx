import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Patriot Life Insurance</h1>
          <p className="hero-subtitle">Serving Those Who Serve</p>
          <p className="hero-description">
            Dedicated exclusively to the brave men and women of the U.S. Armed
            Forces and their families. We provide comprehensive life insurance
            and benefits designed specifically for military life.
          </p>
          <div className="hero-buttons">
            <Link to="/login" className="btn btn-primary">
              Member Login
            </Link>
            <a href="#benefits" className="btn btn-secondary">
              Explore Benefits
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose Patriot Life?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🎖️</div>
            <h3>Military-Exclusive Coverage</h3>
            <p>
              Benefits designed specifically for service members, veterans, and
              their families. We understand the unique challenges of military
              life.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">💰</div>
            <h3>Competitive Rates</h3>
            <p>
              As a non-profit serving the military community, we offer some of
              the most competitive rates available for life insurance coverage.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🌍</div>
            <h3>Worldwide Coverage</h3>
            <p>
              Your coverage follows you wherever duty calls. No war clauses or
              deployment exclusions—you&apos;re covered at home and abroad.
            </p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📱</div>
            <h3>Easy Management</h3>
            <p>
              Manage your benefits online anytime, anywhere. View coverage,
              update beneficiaries, and enroll in new benefits with ease.
            </p>
          </div>
        </div>
      </section>

      {/* Benefits Overview Section */}
      <section id="benefits" className="benefits-overview">
        <h2>Our Benefits</h2>
        <div className="benefits-grid">
          <div className="benefit-category">
            <h3>Life Insurance</h3>
            <ul>
              <li>SGLI-equivalent coverage up to $400,000</li>
              <li>Family coverage (FSGLI) options</li>
              <li>Veterans coverage (VGLI)</li>
              <li>Service-Disabled Veterans Insurance</li>
            </ul>
          </div>
          <div className="benefit-category">
            <h3>Disability Protection</h3>
            <ul>
              <li>Income replacement coverage</li>
              <li>Service-related disability coverage</li>
              <li>Flexible benefit amounts</li>
              <li>No waiting periods for active duty</li>
            </ul>
          </div>
          <div className="benefit-category">
            <h3>Supplemental Coverage</h3>
            <ul>
              <li>Accident protection plans</li>
              <li>Critical illness coverage</li>
              <li>Additional term life options</li>
              <li>Family protection packages</li>
            </ul>
          </div>
        </div>
        <div className="benefits-cta">
          <p>Ready to protect your family&apos;s future?</p>
          <Link to="/login" className="btn btn-primary">
            Get Started Today
          </Link>
        </div>
      </section>

      {/* Trust Section */}
      <section className="trust">
        <h2>Trusted by Service Members Since 1942</h2>
        <div className="stats-grid">
          <div className="stat">
            <span className="stat-number">500K+</span>
            <span className="stat-label">Active Members</span>
          </div>
          <div className="stat">
            <span className="stat-number">$50B+</span>
            <span className="stat-label">Coverage in Force</span>
          </div>
          <div className="stat">
            <span className="stat-number">98%</span>
            <span className="stat-label">Claims Paid</span>
          </div>
          <div className="stat">
            <span className="stat-number">24/7</span>
            <span className="stat-label">Member Support</span>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="contact">
        <h2>Need Help?</h2>
        <p>Our member services team is available to assist you.</p>
        <div className="contact-info">
          <div className="contact-item">
            <span className="contact-label">Phone:</span>
            <span className="contact-value">1-800-PATRIOT (728-7468)</span>
          </div>
          <div className="contact-item">
            <span className="contact-label">Email:</span>
            <span className="contact-value">support@patriotlife.com</span>
          </div>
          <div className="contact-item">
            <span className="contact-label">Hours:</span>
            <span className="contact-value">24/7 Member Support</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
