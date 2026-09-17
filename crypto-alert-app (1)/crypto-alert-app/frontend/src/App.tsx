import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CoinDetail from "./pages/CoinDetail";
import Portfolio from "./pages/Portfolio";
import Backtest from "./pages/Backtest";
import Settings from "./pages/Settings";

function Rail() {
  return (
    <nav className="rail">
      <div className="rail-brand"><span className="dot" /> Signal Deck</div>
      <NavLink to="/" end className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}>Dashboard</NavLink>
      <NavLink to="/portfolio" className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}>Portfolio</NavLink>
      <NavLink to="/backtest" className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}>Backtest</NavLink>
      <NavLink to="/settings" className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}>Settings</NavLink>
      <div className="rail-disclaimer">
        Analysis &amp; alert tool only. No automatic trading, no Binance login, no withdrawal access.
        You buy and sell manually on Binance.
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Rail />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/coin/:symbol" element={<CoinDetail />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
