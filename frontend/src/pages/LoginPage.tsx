import { AxiosError } from "axios";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem("access_token", response.data.access_token);

      navigate("/chat");
    } catch (err) {
      if (err instanceof AxiosError) {
        const message =
          err.response?.data?.detail ||
          "Login failed. Please check your credentials.";

        setError(message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center text-white bg-slate-950">
      <form
        onSubmit={handleLogin}
        className="w-full max-w-md bg-slate-900 p-8 rounded-2xl shadow-xl space-y-4"
      >
        <div>
          <h1 className="text-2xl font-bold">Login</h1>
          <p className="text-sm text-slate-400 mt-1">
            Welcome back, captain.
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-300 p-3 rounded">
            {error}
          </div>
        )}

        <input
          className="w-full p-3 rounded bg-slate-800 border border-slate-700 outline-none focus:border-blue-500"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          className="w-full p-3 rounded bg-slate-800 border border-slate-700 outline-none focus:border-blue-500"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:cursor-not-allowed p-3 rounded font-semibold"
        >
          {loading ? "Logging in..." : "Login"}
        </button>

        <p className="text-sm text-slate-400">
          New here?{" "}
          <Link className="text-blue-400 hover:underline" to="/register">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}