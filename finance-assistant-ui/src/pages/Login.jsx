import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginApi } from "../lib/api";
import { useNavigate } from "react-router-dom";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(4, "Password must be at least 4 characters"),
});

export default function Login() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values) => {
    setServerError("");
    setLoading(true);
    try {
      // call backend
      const data = await loginApi(values);
      // In the MVP we’ll just stash a dummy user id
      const userId = data?.user?.id || "u123";
      localStorage.setItem("userId", userId);
      navigate("/chat");
    } catch (err) {
      setServerError(err?.response?.data?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold mb-6">Sign in</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm mb-1">Email</label>
          <input
            type="email"
            className="w-full rounded-md bg-gray-900 border border-gray-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600"
            placeholder="you@example.com"
            {...register("email")}
          />
          {errors.email && (
            <p className="text-red-400 text-sm mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm mb-1">Password</label>
          <input
            type="password"
            className="w-full rounded-md bg-gray-900 border border-gray-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600"
            placeholder="••••••••"
            {...register("password")}
          />
          {errors.password && (
            <p className="text-red-400 text-sm mt-1">{errors.password.message}</p>
          )}
        </div>

        {serverError && (
          <div className="rounded-md bg-red-950/60 border border-red-800 px-3 py-2 text-sm text-red-300">
            {serverError}
          </div>
        )}

        <button
          disabled={loading}
          className="w-full rounded-md bg-indigo-600 hover:bg-indigo-500 transition-colors px-3 py-2 font-medium disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p className="text-xs text-gray-400 mt-4">
        Demo tip: backend can return a dummy user; we store <code>userId</code> in localStorage.
      </p>
    </div>
  );
}
