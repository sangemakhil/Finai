import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:5001",
  withCredentials: true, // if you later use httpOnly cookies
  timeout: 60000,
});

export async function loginApi({ email, password }) {
  const res = await api.post("/auth/login", { email, password });
  return res.data; // expect { token? , user? }
}

export async function chatApi({ userId, query }) {
  const res = await api.post("/chat", { user_id: userId, query });
  return res.data; // expect { answer_text, facts, meta }
}

export default api;
