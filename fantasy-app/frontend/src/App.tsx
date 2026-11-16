import { NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Rankings from "./pages/Rankings";
import Draft from "./pages/Draft";
import Roster from "./pages/Roster";

const NAV = [
  { to: "/", label: "Home" },
  { to: "/rankings", label: "Rankings" },
  { to: "/draft", label: "Draft" },
  { to: "/roster", label: "Roster" },
];

export default function App() {
  return (
    <div className="layout">
      <header className="topbar">
        <span className="brand">Fantasy Tools</span>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end>
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/rankings" element={<Rankings />} />
          <Route path="/draft" element={<Draft />} />
          <Route path="/roster" element={<Roster />} />
        </Routes>
      </main>
    </div>
  );
}
