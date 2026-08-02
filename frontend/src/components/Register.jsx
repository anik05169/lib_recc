import { useState } from "react";
import { API_BASE_URL } from "../api";
import { formatApiError } from "../utils/apiError";
import "./Login.css";

function Register({ onRegister, switchToLogin }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        if (data.detail && Array.isArray(data.detail)) {
          const messages = data.detail.map((d) => d.msg || d.message || JSON.stringify(d));
          throw new Error(messages.join(". "));
        }
        throw new Error(formatApiError(data.detail, "Registration failed"));
      }

      await response.json();
      const loginResponse = await fetch(`${API_BASE_URL.replace(/\/$/, "")}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!loginResponse.ok) {
        throw new Error("Registration successful but login failed");
      }

      const loginData = await loginResponse.json();
      localStorage.setItem("token", loginData.access_token);
      onRegister(loginData.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <aside className="auth-hero">
        <div className="auth-hero-ornament" />
        <div className="auth-hero-content">
          <p className="auth-brand">Library AI</p>
          <p className="auth-hero-line">
            Create an account to collect books, leave ratings, and get tailored suggestions.
          </p>
        </div>
      </aside>

      <div className="auth-panel">
        <div className="auth-card">
          <h2>Create account</h2>
          <p className="auth-card-lead">A few details and your shelf is ready.</p>
          {error && <div className="error-message" role="alert">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="register-name">Name</label>
              <input
                id="register-name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="register-email">Email</label>
              <input
                id="register-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="register-password">Password</label>
              <input
                id="register-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                minLength={8}
              />
              <small className="form-hint">
                Min 8 characters, 1 uppercase, 1 digit
              </small>
            </div>
            <button type="submit" disabled={loading}>
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
          <p className="switch-auth">
            Already have an account?
            <button type="button" onClick={switchToLogin} className="link-button">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;
