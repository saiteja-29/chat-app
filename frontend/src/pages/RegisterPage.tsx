import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function RegisterPage() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();

    await api.post("/auth/register", {
      username,
      email,
      password,
      display_name: displayName || null,
    });

    navigate("/login");
  }

  return (
    <div className="min-h-screen flex items-center justify-center text-white">
      <form
        onSubmit={handleRegister}
        className="w-full max-w-md bg-slate-900 p-8 rounded-2xl shadow-xl space-y-4"
      >
        <h1 className="text-2xl font-bold">Create account</h1>

        <input
          className="w-full p-3 rounded bg-slate-800"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <input
          className="w-full p-3 rounded bg-slate-800"
          placeholder="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />

        <input
          className="w-full p-3 rounded bg-slate-800"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          className="w-full p-3 rounded bg-slate-800"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button className="w-full bg-blue-600 p-3 rounded font-semibold">
          Register
        </button>

        <p className="text-sm text-slate-400">
          Already have an account?{" "}
          <Link className="text-blue-400" to="/login">
            Login
          </Link>
        </p>
      </form>
    </div>
  );
}