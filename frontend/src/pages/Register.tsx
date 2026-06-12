import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register as apiRegister } from "../api/endpoints";
import { useAuth } from "../auth/AuthProvider";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

export function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiRegister(email, password, fullName);
      sessionStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      navigate("/");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Registration failed.";
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
          <p className="mt-2 text-sm text-gray-600 text-center">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-8 space-y-6">
          <Input
            id="full_name"
            label="Full Name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <Input
            id="email"
            label="Email address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}

          <Button type="submit" className="w-full" loading={loading}>
            Create account
          </Button>

          <p className="text-center text-sm text-gray-600">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-600 hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
