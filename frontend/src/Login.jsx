import { useState } from "react";

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`;

function getApiError(data, fallback) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg || item.message || JSON.stringify(item)).join(" ");
  }
  if (data?.detail && typeof data.detail === "object") return data.detail.message || JSON.stringify(data.detail);
  if (typeof data?.error === "string") return data.error;
  return fallback;
}

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [forgotEmail, setForgotEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const persistAuth = (token, user) => {
    localStorage.setItem("smartNotesAuthToken", token);
    localStorage.setItem("smartNotesUser", JSON.stringify(user));
    onLogin();
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!email || !password) {
      setError("Please enter email and password.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, "Login failed"));
      persistAuth(data.token, data.user);
    } catch (loginError) {
      setError(loginError.message || "Unable to log in.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    if (!name || !email || !password) {
      setError("Please complete all sign-up fields.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, "Registration failed"));
      persistAuth(data.token, data.user);
    } catch (registerError) {
      setError(registerError.message || "Unable to create account.");
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (event) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    if (!forgotEmail) {
      setError("Please enter your email to receive a reset code.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, "Unable to send reset code"));
      if (data?.email_delivery_failed && data?.otp) {
        setSuccessMessage(`${data.message || "Reset code sent."} OTP: ${data.otp}`);
        setMode("reset");
      } else {
        setSuccessMessage(data.message || "Reset code sent.");
      }
    } catch (resetError) {
      setError(resetError.message || "Reset failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (event) => {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    if (!forgotEmail || !otp || !newPassword) {
      setError("Please enter your email, OTP, and new password.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail, otp, new_password: newPassword }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, "Password reset failed"));
      setSuccessMessage(data.message || "Password updated.");
      setMode("login");
      setPassword("");
      setOtp("");
      setNewPassword("");
    } catch (resetError) {
      setError(resetError.message || "Could not reset the password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="background-shape shape-orange" />
      <div className="background-shape shape-yellow" />
      <div className="background-shape shape-green" />
      <div className="background-shape shape-blue" />
      <div className="background-wave" aria-hidden="true">
        {Array.from({ length: 11 }, (_, index) => <span key={index} />)}
      </div>
      <div className="login-card">
        <div className="login-logo">🎙</div>
        <h1>Smart Notes</h1>
        <p className="login-subtitle">
          Speak naturally. Turn your voice into notes.
        </p>

        {mode === "login" && (
          <form onSubmit={handleLogin}>
            <label htmlFor="login-email">Email</label>
            <input id="login-email" type="email" placeholder="Enter your email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <label htmlFor="login-password">Password</label>
            <input id="login-password" type="password" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} />
            {error && <p className="login-error">{error}</p>}
            {successMessage && <p className="login-success">{successMessage}</p>}
            <button type="submit" className="login-button" disabled={loading}>{loading ? "Please wait..." : "Login →"}</button>
            <div className="auth-links">
              <button type="button" className="text-button" onClick={() => { setMode("register"); setError(""); setSuccessMessage(""); }}>Create account</button>
              <button type="button" className="text-button" onClick={() => { setMode("forgot"); setError(""); setSuccessMessage(""); }}>Forgot password?</button>
            </div>
          </form>
        )}

        {mode === "register" && (
          <form onSubmit={handleRegister}>
            <label htmlFor="register-name">Full name</label>
            <input id="register-name" type="text" placeholder="Enter your full name" value={name} onChange={(event) => setName(event.target.value)} />
            <label htmlFor="register-email">Email</label>
            <input id="register-email" type="email" placeholder="Enter your email" value={email} onChange={(event) => setEmail(event.target.value)} />
            <label htmlFor="register-password">Password</label>
            <input id="register-password" type="password" placeholder="Create a password" value={password} onChange={(event) => setPassword(event.target.value)} />
            {error && <p className="login-error">{error}</p>}
            <button type="submit" className="login-button" disabled={loading}>{loading ? "Creating account..." : "Create account →"}</button>
            <div className="auth-links"><button type="button" className="text-button" onClick={() => setMode("login")}>Back to login</button></div>
          </form>
        )}

        {mode === "forgot" && (
          <form onSubmit={handleForgotPassword}>
            <label htmlFor="forgot-email">Email</label>
            <input id="forgot-email" type="email" placeholder="Enter your email" value={forgotEmail} onChange={(event) => setForgotEmail(event.target.value)} />
            {error && <p className="login-error">{error}</p>}
            {successMessage && <p className="login-success">{successMessage}</p>}
            <button type="submit" className="login-button" disabled={loading}>{loading ? "Sending code..." : "Send reset code →"}</button>
            <div className="auth-links"><button type="button" className="text-button" onClick={() => setMode("reset")}>I have an OTP</button><button type="button" className="text-button" onClick={() => setMode("login")}>Back to login</button></div>
          </form>
        )}

        {mode === "reset" && (
          <form onSubmit={handleResetPassword}>
            <label htmlFor="reset-email">Email</label>
            <input id="reset-email" type="email" placeholder="Enter your email" value={forgotEmail} onChange={(event) => setForgotEmail(event.target.value)} />
            <label htmlFor="reset-otp">OTP code</label>
            <input id="reset-otp" type="text" placeholder="Enter the 6-digit code" value={otp} onChange={(event) => setOtp(event.target.value)} />
            <label htmlFor="reset-password">New password</label>
            <input id="reset-password" type="password" placeholder="Enter a new password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} />
            {error && <p className="login-error">{error}</p>}
            {successMessage && <p className="login-success">{successMessage}</p>}
            <button type="submit" className="login-button" disabled={loading}>{loading ? "Updating password..." : "Reset password →"}</button>
            <div className="auth-links"><button type="button" className="text-button" onClick={() => setMode("login")}>Back to login</button></div>
          </form>
        )}

        <p className="login-info">Hindi · English · Mixed Language</p>
      </div>
    </div>
  );
}
