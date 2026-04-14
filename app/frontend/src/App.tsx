import { NavLink, Route, Routes } from "react-router-dom";

import { AttributeManagementPage } from "./pages/AttributeManagementPage";
import { GroupViewPage } from "./pages/GroupViewPage";
import { UserCreationPage } from "./pages/UserCreationPage";

export function App() {
  return (
    <div className="layout">
      <header className="header">
        <div className="header-copy">
          <h1>Social Grouping App</h1>
          <p className="header-muted">
            Discover meaningful clusters based on shared signals.
          </p>
        </div>

        <nav className="nav" aria-label="Primary">
          <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            Create User
          </NavLink>
          <NavLink
            to="/attributes"
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            Attributes
          </NavLink>
          <NavLink to="/groups" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            Groups
          </NavLink>
        </nav>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<UserCreationPage />} />
          <Route path="/attributes" element={<AttributeManagementPage />} />
          <Route path="/groups" element={<GroupViewPage />} />
        </Routes>
      </main>
    </div>
  );
}
