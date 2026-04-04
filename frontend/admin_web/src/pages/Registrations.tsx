import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../api";
import { Users, Search, Filter, Download, Calendar, User, Mail, Code, ChevronLeft, ChevronRight } from "lucide-react";

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

type ListResponse = {
  items: Row[];
  total: number;
  distinct_users: number;
  distinct_events: number;
  limit: number;
  offset: number;
};

type EventOption = { id: number; title: string };

const PAGE_SIZES = [25, 50, 100] as const;

export default function Registrations() {
  const [data, setData] = useState<ListResponse | null>(null);
  const [events, setEvents] = useState<EventOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterEventId, setFilterEventId] = useState<number | "">("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState<number>(50);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchInput.trim()), 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    setPage(0);
  }, [debouncedSearch, filterEventId, pageSize]);

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/events?include_archived=false");
      if (res.ok) {
        const rows = (await res.json()) as { id: number; title: string }[];
        setEvents(rows.map((r) => ({ id: r.id, title: r.title })));
      }
    })();
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: String(pageSize),
        offset: String(page * pageSize),
      });
      if (filterEventId !== "") params.set("event_id", String(filterEventId));
      if (debouncedSearch) params.set("q", debouncedSearch);
      const res = await apiFetch(`/api/registrations?${params}`);
      if (res.ok) setData(await res.json());
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterEventId, debouncedSearch]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!data) return;
    if (data.total === 0) {
      if (page !== 0) setPage(0);
      return;
    }
    const maxPage = Math.ceil(data.total / pageSize) - 1;
    if (page > maxPage) setPage(maxPage);
  }, [data, pageSize, page]);

  const exportCsv = async () => {
    const params = new URLSearchParams();
    if (filterEventId !== "") params.set("event_id", String(filterEventId));
    if (debouncedSearch) params.set("q", debouncedSearch);
    const qs = params.toString();
    const res = await apiFetch(`/api/registrations/export${qs ? `?${qs}` : ""}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `registrations_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  if (!data && loading)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-gray-600 font-medium">Загрузка регистраций...</p>
        </div>
      </div>
    );

  if (!data) return null;

  const totalPages = data.total === 0 ? 0 : Math.ceil(data.total / pageSize);
  const currentPage = totalPages === 0 ? 0 : Math.min(page, totalPages - 1);
  const displayPage = totalPages === 0 ? 0 : currentPage + 1;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Регистрации
          </h1>
          <p className="text-gray-600 mt-2">
            По фильтру: <span className="font-semibold">{data.total}</span> записей
            {loading && <span className="text-gray-400 ml-2">(обновление…)</span>}
          </p>
        </div>
        <button
          onClick={exportCsv}
          className="btn-primary flex items-center gap-2 shrink-0"
          disabled={data.total === 0}
        >
          <Download className="w-5 h-5" />
          Экспорт CSV
        </button>
      </div>

      <div className="card">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Search className="inline w-4 h-4 mr-2" />
              Поиск
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Имя, контакт, код, username…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>

          <div className="w-full lg:w-72">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Filter className="inline w-4 h-4 mr-2" />
              Мероприятие
            </label>
            <select
              className="input-field"
              value={filterEventId === "" ? "" : String(filterEventId)}
              onChange={(e) => {
                const v = e.target.value;
                setFilterEventId(v === "" ? "" : Number(v));
              }}
            >
              <option value="">Все мероприятия</option>
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.title}
                </option>
              ))}
            </select>
          </div>

          <div className="w-full lg:w-36">
            <label className="block text-sm font-medium text-gray-700 mb-2">На странице</label>
            <select
              className="input-field"
              value={pageSize}
              onChange={(e) => setPageSize(Number(e.target.value))}
            >
              {PAGE_SIZES.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>

        {(searchInput !== "" || filterEventId !== "") && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => {
                setSearchInput("");
                setFilterEventId("");
              }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Сбросить фильтры
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Регистраций по фильтру</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data.total}</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-purple-100 rounded-xl">
              <Calendar className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Мероприятий (по фильтру)</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data.distinct_events}</p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-2">
            <div className="p-3 bg-pink-100 rounded-xl">
              <User className="w-6 h-6 text-pink-600" />
            </div>
          </div>
          <p className="text-gray-600 text-sm font-medium">Уникальных пользователей</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data.distinct_users}</p>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <p className="text-sm text-gray-600">
            Страница <span className="font-semibold">{displayPage}</span> из{" "}
            <span className="font-semibold">{totalPages}</span>
            {" · "}
            показано {data.items.length} из {data.total}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-3 py-2"
              disabled={currentPage <= 0 || loading}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="w-4 h-4" />
              Назад
            </button>
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-3 py-2"
              disabled={
                totalPages === 0 || currentPage >= totalPages - 1 || loading
              }
              onClick={() => setPage((p) => p + 1)}
            >
              Вперёд
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {data.items.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Регистрации не найдены</p>
            <p className="text-gray-400 text-sm mt-1">Попробуйте изменить параметры поиска</p>
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
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">Username</th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                    <Code className="inline w-4 h-4 mr-2" />
                    Код
                  </th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">Дата</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row, idx) => (
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
