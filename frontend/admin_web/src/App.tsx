import { NavLink, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { getToken } from "./api";
import Dashboard from "./pages/Dashboard";
import Events from "./pages/Events";
import Login from "./pages/Login";
import Registrations from "./pages/Registrations";
import { BarChart3, Calendar, Users, LogOut } from "lucide-react";

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Layout() {
  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-gray-200 shadow-lg flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl">
              <Calendar className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Botfest Admin
              </h1>
              <p className="text-xs text-gray-500">Панель управления</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <NavLink
            end
            to="/"
            className={({ isActive }) =>
              isActive ? "sidebar-link-active" : "sidebar-link"
            }
          >
            <BarChart3 className="w-5 h-5" />
            <span className="font-medium">Статистика</span>
          </NavLink>

          <NavLink
            to="/events"
            className={({ isActive }) =>
              isActive ? "sidebar-link-active" : "sidebar-link"
            }
          >
            <Calendar className="w-5 h-5" />
            <span className="font-medium">Мероприятия</span>
          </NavLink>

          <NavLink
            to="/registrations"
            className={({ isActive }) =>
              isActive ? "sidebar-link-active" : "sidebar-link"
            }
          >
            <Users className="w-5 h-5" />
            <span className="font-medium">Регистрации</span>
          </NavLink>
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-all duration-200"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Выйти</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/events" element={<Events />} />
        <Route path="/registrations" element={<Registrations />} />
      </Route>
    </Routes>
  );
}
