import { Link, useLocation } from "react-router-dom";
import type { Member } from "../types";
import "./Navigation.css";

interface NavigationProps {
  member: Member | null;
  onLogout: () => void;
}

function Navigation({ member, onLogout }: NavigationProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path ? "active" : "";
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          <span className="brand-icon">🛡️</span>
          <span className="brand-text">Patriot Life</span>
        </Link>

        <div className="nav-links">
          <Link to="/" className={`nav-link ${isActive("/")}`}>
            Home
          </Link>
          <Link to="/benefits" className={`nav-link ${isActive("/benefits")}`}>
            Benefits
          </Link>
          {member && (
            <Link
              to="/dashboard"
              className={`nav-link ${isActive("/dashboard")}`}
            >
              Dashboard
            </Link>
          )}
        </div>

        <div className="nav-auth">
          {member ? (
            <div className="user-menu">
              <span className="user-name">
                {member.first_name} {member.last_name}
              </span>
              <button onClick={onLogout} className="btn btn-logout">
                Logout
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-login">
              Member Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
