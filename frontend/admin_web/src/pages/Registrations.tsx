import { useEffect, useState } from "react";
import { apiFetch } from "../api";
import { Users, Search, Filter, Download, Calendar, User, Mail, Code } from "lucide-react";

type Row = {
  id: number;
  user_id: number;
  username: string | null;
  event_id: number;
  event_title: string;
  name: string;
  contact: string;
  reg_code: string;
  registered_at: string;
};

export default function Registrations() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [search, setSearch] = useState("");
  const [filterEvent, setFilterEvent] = useState("");

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/registrations");
      if (res.ok) setRows(await res.json());
    })();
  }, []);

  if (!rows)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-gray-600 font-medium">Загрузка регистраций...</p>
        </div>
      </div>
    );

  const events = Array.from(new Set(rows.map((r) => r.event_title)));

  const filteredRows = rows.filter((row) => {
    const matchesSearch =
      search === "" ||
      row.name.toLowerCase().includes(search.toLowerCase()) ||
      row.contact.toLowerCase().includes(search.toLowerCase()) ||
      row.reg_code.toLowerCase().includes(search.toLowerCase()) ||
      (row.username && row.username.toLowerCase().includes(search.toLowerCase()));

    const matchesEvent = filterEvent === "" || row.event_title === filterEvent;

    return matchesSearch && matchesEvent;
  });

  const exportToCSV = () => {
    const headers = ["ID", "Мероприятие", "ФИО", "Контакт", "Username", "Код", "Дата"];
    const csvContent = [
      headers.join(","),
      ...filteredRows.map((r) =>
        [
          r.id,
          `"${r.event_title}"`,
          `"${r.name}"`,
          `"${r.contact}"`,
          r.username || "",
          r.reg_code,
          r.registered_at,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `registrations_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Регистрации
          </h1>
          <p className="text-gray-600 mt-2">
            Всего регистраций: <span className="font-semibold">{filteredRows.length}</span>
            {filteredRows.length !== rows.length && (
              <span className="text-gray-400"> из {rows.length}</span>
            )}
          </p>
        </div>
        <button
          onClick={exportToCSV}
          className="btn-primary flex items-center gap-2"
          disabled={filteredRows.length === 0}
        >
          <Download className="w-5 h-5" />
          Экспорт CSV
        </button>
      </div>

      {/* Filters Card */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Search className="inline w-4 h-4 mr-2" />
              Поиск
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Поиск по имени, контакту, коду..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-full md:w-64">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Filter className="inline w-4 h-4 mr-2" />
              Мероприятие
            </label>
            <select
              className="input-field"
              value={filterEvent}
              onChange={(e) => setFilterEvent(e.target.value)}
            >
              <option value="">Все мероприятия</option>
              {events.map((event) => (
                <option key={event} value={event}>
                  {event}
                </option>
              ))}
            </select>
          </div>
        </div>

        {(search !== "" || filterEvent !== "") && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={() => {
                setSearch("");
                setFilterEvent("");
              }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Сбросить фильтры
            </button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Найдено регистраций</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{filteredRows.length}</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Calendar className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Мероприятий</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {new Set(filteredRows.map((r) => r.event_title)).size}
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-pink-100 rounded-xl">
              <User className="w-6 h-6 text-pink-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Уникальных пользователей</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {new Set(filteredRows.map((r) => r.user_id)).size}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {filteredRows.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Регистрации не найдены</p>
            <p className="text-gray-400 text-sm mt-1">
              Попробуйте изменить параметры поиска
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">ID</th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    <Calendar className="inline w-4 h-4 mr-2" />
                    Мероприятие
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    <User className="inline w-4 h-4 mr-2" />
                    ФИО
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    <Mail className="inline w-4 h-4 mr-2" />
                    Контакт
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    Username
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    <Code className="inline w-4 h-4 mr-2" />
                    Код
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    Дата
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row, idx) => (
                  <tr
                    key={row.id}
                    className={`border-b border-gray-100 hover:bg-blue-50 transition-colors ${
                      idx % 2 === 0 ? "bg-white" : "bg-gray-50"
                    }`}
                  >
                    <td className="py-3 px-4 text-gray-600 font-medium">{row.id}</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                        {row.event_title}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-900">{row.name}</td>
                    <td className="py-3 px-4 text-gray-700">{row.contact}</td>
                    <td className="py-3 px-4 text-gray-600">
                      {row.username ? `@${row.username}` : "-"}
                    </td>
                    <td className="py-3 px-4">
                      <code className="px-2 py-1 bg-gray-100 text-gray-800 rounded font-mono text-sm">
                        {row.reg_code}
                      </code>
                    </td>
                    <td className="py-3 px-4 text-gray-600 text-sm">
                      {new Date(row.registered_at).toLocaleString("ru-RU")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
