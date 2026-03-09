import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Chat from "./pages/Chat.jsx";
import SipCalculator from "./pages/SipCalculator.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="font-bold tracking-wide">SmartFunds</Link>
          <nav className="space-x-4 text-sm">
            <Link className="hover:underline" to="/login">Login</Link>
            <Link className="hover:underline" to="/chat">Chat</Link>
			<Link className="hover:underline" to="/calculator">SIP Calc</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/chat" element={<Chat />} />
		  <Route path="/calculator" element={<SipCalculator />} />
          <Route path="*" element={<div className="p-6">Not Found</div>} />
        </Routes>
      </main>
    </div>
  );
}
