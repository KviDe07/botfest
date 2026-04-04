import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { apiFetch, clearToken, getToken } from "./api";
import Dashboard from "./pages/Dashboard";
import Events from "./pages/Events";
import Login from "./pages/Login";
import Registrations from "./pages/Registrations";
import Settings from "./pages/Settings";
import { BarChart3, Calendar, Users, LogOut, Sliders } from "lucide-react";

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Layout() {
  const [brandTitle, setBrandTitle] = useState("Botfest Admin");

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/settings");
      if (res.ok) {
        const s = (await res.json()) as { admin_brand_title: string };
        if (s.admin_brand_title) setBrandTitle(s.admin_brand_title);
      }
    })();
    const onUpd = (e: Event) => {
      const d = (e as CustomEvent<{ admin_brand_title: string }>).detail;
      if (d?.admin_brand_title) setBrandTitle(d.admin_brand_title);
    };
    window.addEventListener("app-settings-updated", onUpd as EventListener);
    return () => window.removeEventListener("app-settings-updated", onUpd as EventListener);
  }, []);

  const handleLogout = () => {
    clearToken();
    window.location.href = "/login";
  };

  return (
    <div className="h-screen flex overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <aside className="w-72 shrink-0 h-full bg-white border-r border-gray-200 shadow-lg flex flex-col">
        <div className="p-6 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl">
              <Calendar className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                {brandTitle}
              </h1>
              <p className="text-xs text-gray-500">Панель управления</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 min-h-0 overflow-y-auto p-4 space-y-2">
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

          <NavLink
            to="/settings"
            className={({ isActive }) =>
              isActive ? "sidebar-link-active" : "sidebar-link"
            }
          >
            <Sliders className="w-5 h-5" />
            <span className="font-medium">Настройки</span>
          </NavLink>
        </nav>

        <div className="p-4 border-t border-gray-200 shrink-0 bg-white">
          <button
            type="button"
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-all duration-200"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Выйти</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 min-h-0 min-w-0 flex flex-col">
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-8">
            <Outlet />
          </div>
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
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
