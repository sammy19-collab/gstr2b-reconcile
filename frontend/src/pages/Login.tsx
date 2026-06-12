import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Login failed. Please check your credentials.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 text-center">GST Reconcile AI</h1>
          <p className="mt-2 text-sm text-gray-600 text-center">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-8 space-y-6">
          <Input
            id="email"
            label="Email address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}

          <Button type="submit" className="w-full" loading={loading}>
            Sign in
          </Button>

          <p className="text-center text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="text-blue-600 hover:underline">
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
