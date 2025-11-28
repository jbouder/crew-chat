import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import type { Member } from "../types";
import "./Login.css";

interface LoginProps {
  onLogin: (member: Member) => void;
}

function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("john.doe@military.mil");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const member = await api.login({ email, password });
      onLogin(member);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>Member Login</h1>
          <p>Access your Patriot Life Member Center</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Not a member yet? <Link to="/">Learn about our benefits</Link>
          </p>
        </div>

        <div className="demo-info">
          <h3>Demo Credentials</h3>
          <p>
            <strong>Email:</strong> john.doe@military.mil
          </p>
          <p>
            <strong>Password:</strong> demo
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
