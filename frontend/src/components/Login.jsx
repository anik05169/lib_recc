import { useState } from "react";
import { API_BASE_URL } from "../api";
import { formatApiError } from "../utils/apiError";
import "./Login.css";

function Login({ onLogin, switchToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(formatApiError(data.detail, "Login failed"));
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <aside className="auth-hero" aria-hidden="false">
        <div className="auth-hero-ornament" />
        <div className="auth-hero-content">
          <p className="auth-brand">Library AI</p>
          <p className="auth-hero-line">
            Build your shelf, rate what you love, and find the next book worth reading.
          </p>
        </div>
      </aside>

      <div className="auth-panel">
        <div className="auth-card">
          <h2>Welcome back</h2>
          <p className="auth-card-lead">Sign in to open your catalog and collection.</p>
          {error && <div className="error-message" role="alert">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <button type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="switch-auth">
            Don&apos;t have an account?
            <button type="button" onClick={switchToRegister} className="link-button">
              Create one
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
