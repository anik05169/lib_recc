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
        // Handle Pydantic validation errors (password strength)
        if (data.detail && Array.isArray(data.detail)) {
          const messages = data.detail.map((d) => d.msg || d.message || JSON.stringify(d));
          throw new Error(messages.join(". "));
        }
        throw new Error(formatApiError(data.detail, "Registration failed"));
      }

      await response.json();
      // After registration, automatically log in
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
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create Account</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              minLength={8}
            />
            <small style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
              Min 8 characters, 1 uppercase, 1 digit
            </small>
          </div>
          <button type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </button>
        </form>
        <p className="switch-auth">
          Already have an account?{" "}
          <button type="button" onClick={switchToLogin} className="link-button">
            Login
          </button>
        </p>
      </div>
    </div>
  );
}

export default Register;
