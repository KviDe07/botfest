import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  Users,
  Calendar,
  TrendingUp,
  Activity,
  BarChart3,
  PieChart as PieChartIcon,
  ContactRound,
} from "lucide-react";

type Summary = {
  total_registrations: number;
  unique_users: number;
  unique_names: number;
  by_event: { event_title: string; count: number }[];
  by_day: { day: string; count: number }[];
};

const COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6366f1"];

export default function Dashboard() {
  const [data, setData] = useState<Summary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/analytics/summary");
      if (!res.ok) {
        setErr("Не удалось загрузить статистику");
        return;
      }
      setData(await res.json());
    })();
  }, []);

  if (err)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="card bg-red-50 border-red-200 text-red-600">
          <Activity className="w-8 h-8 mb-2" />
          <p className="font-medium">{err}</p>
        </div>
      </div>
    );

  if (!data)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-gray-600 font-medium">Загрузка данных...</p>
        </div>
      </div>
    );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Статистика
          </h1>
          <p className="text-gray-600 mt-2">Обзор регистраций и мероприятий</p>
        </div>
        <Activity className="w-12 h-12 text-blue-600" />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-gray-600 text-sm font-medium">Всего регистраций</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {data.total_registrations}
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-gray-600 text-sm font-medium">Уникальных пользователей</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {data.unique_users}
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-pink-100 rounded-xl">
              <ContactRound className="w-6 h-6 text-pink-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Уникальных по ФИО</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {data.unique_names}
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-amber-100 rounded-xl">
              <BarChart3 className="w-6 h-6 text-amber-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Средняя явка</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {data.by_event.length > 0
              ? Math.round(data.total_registrations / data.by_event.length)
              : 0}
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart - By Event */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">По мероприятиям</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.by_event}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="event_title"
                tick={{ fontSize: 12 }}
                stroke="#6b7280"
              />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
                }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart - By Event */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-100 rounded-lg">
              <PieChartIcon className="w-5 h-5 text-purple-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Распределение</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.by_event}
                dataKey="count"
                nameKey="event_title"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => `${entry.event_title}: ${entry.count}`}
                labelLine={false}
              >
                {data.by_event.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Line Chart - By Day */}
        <div className="card lg:col-span-2">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Динамика по дням</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.by_day}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#10b981"
                strokeWidth={3}
                dot={{ fill: "#10b981", r: 5 }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Calendar className="w-5 h-5 text-indigo-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Детальная статистика</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                  Мероприятие
                </th>
                <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                  Регистраций
                </th>
                <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                  Доля, %
                </th>
              </tr>
            </thead>
            <tbody>
              {data.by_event.map((row, idx) => (
                <tr
                  key={row.event_title}
                  className="border-b border-gray-100 hover:bg-blue-50 transition-colors"
                >
                  <td className="py-3 px-4 font-medium text-gray-900">
                    {row.event_title}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-700">
                    {row.count}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">
                      {((row.count / data.total_registrations) * 100).toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
