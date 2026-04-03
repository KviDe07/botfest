import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "../api";
import {
  Calendar,
  Plus,
  Edit,
  Archive,
  ExternalLink,
  Save,
  X,
  AlertCircle,
} from "lucide-react";

type EventRow = {
  id: number;
  title: string;
  sort_order: number;
  archived: boolean;
  registration_mode: "none" | "internal" | "external";
  external_url: string | null;
  description_html: string;
  reminder_enabled: boolean;
  reminder_snippet_html: string | null;
  dates: string[];
};

const emptyForm: Omit<EventRow, "id"> = {
  title: "",
  sort_order: 0,
  archived: false,
  registration_mode: "internal",
  external_url: "",
  description_html: "",
  reminder_enabled: false,
  reminder_snippet_html: "",
  dates: [],
};

export default function Events() {
  const [rows, setRows] = useState<EventRow[] | null>(null);
  const [editing, setEditing] = useState<EventRow | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<Omit<EventRow, "id"> & { id?: number }>(emptyForm);
  const [datesStr, setDatesStr] = useState("");
  const [showModal, setShowModal] = useState(false);

  async function reload() {
    const res = await apiFetch("/api/events?include_archived=true");
    if (res.ok) setRows(await res.json());
  }

  useEffect(() => {
    reload();
  }, []);

  function openEdit(e: EventRow) {
    setEditing(e);
    setCreating(false);
    setForm({ ...e, external_url: e.external_url || "", reminder_snippet_html: e.reminder_snippet_html || "" });
    setDatesStr(e.dates.join(", "));
    setShowModal(true);
  }

  function openCreate() {
    setEditing(null);
    setCreating(true);
    setForm({ ...emptyForm });
    setDatesStr("");
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setCreating(false);
    setEditing(null);
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    const dates = datesStr
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => {
        const d = new Date(s);
        if (Number.isNaN(d.getTime())) return null;
        return d.toISOString().slice(0, 10);
      })
      .filter((x): x is string => x !== null);

    const payload = {
      title: form.title,
      sort_order: form.sort_order,
      archived: form.archived,
      registration_mode: form.registration_mode,
      external_url: form.external_url || null,
      description_html: form.description_html,
      reminder_enabled: form.reminder_enabled,
      reminder_snippet_html: form.reminder_snippet_html || null,
      dates,
    };

    let success = false;
    if (creating) {
      const res = await apiFetch("/api/events", { method: "POST", body: JSON.stringify(payload) });
      success = res.ok;
      if (!success) alert("Ошибка сохранения");
    } else if (editing) {
      const res = await apiFetch(`/api/events/${editing.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      success = res.ok;
      if (!success) alert("Ошибка сохранения");
    }
    
    if (success) {
      closeModal();
      await reload();
    }
  }

  if (!rows)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-gray-600 font-medium">Загрузка мероприятий...</p>
        </div>
      </div>
    );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Мероприятия
          </h1>
          <p className="text-gray-600 mt-2">Управление событиями и регистрациями</p>
        </div>
        <button onClick={openCreate} className="btn-primary flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Новое мероприятие
        </button>
      </div>

      {/* Events Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rows.map((row) => (
          <div
            key={row.id}
            className={`card relative ${
              row.archived ? "opacity-60 bg-gray-50" : ""
            }`}
          >
            {row.archived && (
              <div className="absolute top-4 right-4">
                <Archive className="w-5 h-5 text-gray-400" />
              </div>
            )}
            
            <div className="flex items-start gap-3 mb-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <Calendar className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-lg text-gray-900">{row.title}</h3>
                <p className="text-sm text-gray-500">ID: {row.id}</p>
              </div>
            </div>

            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Режим:</span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    row.registration_mode === "internal"
                      ? "bg-green-100 text-green-700"
                      : row.registration_mode === "external"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {row.registration_mode === "internal"
                    ? "В боте"
                    : row.registration_mode === "external"
                    ? "Внешняя"
                    : "Информация"}
                </span>
              </div>

              {row.external_url && (
                <div className="flex items-center gap-2 text-sm">
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                  <a
                    href={row.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline truncate"
                  >
                    {row.external_url}
                  </a>
                </div>
              )}

              {row.dates.length > 0 && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Даты:</span> {row.dates.join(", ")}
                </div>
              )}

              {row.reminder_enabled && (
                <div className="flex items-center gap-2 text-sm text-purple-600">
                  <AlertCircle className="w-4 h-4" />
                  <span>Напоминания включены</span>
                </div>
              )}
            </div>

            <button
              onClick={() => openEdit(row)}
              className="w-full btn-secondary flex items-center justify-center gap-2"
            >
              <Edit className="w-4 h-4" />
              Редактировать
            </button>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={save}>
              {/* Modal Header */}
              <div className="sticky top-0 bg-white border-b border-gray-200 px-8 py-6 rounded-t-2xl">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {creating ? "Создание мероприятия" : `Редактирование #${editing?.id}`}
                  </h2>
                  <button
                    type="button"
                    onClick={closeModal}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6 text-gray-500" />
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div className="px-8 py-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название <span className="text-red-500">*</span>
                  </label>
                  <input
                    className="input-field"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Порядок сортировки
                    </label>
                    <input
                      type="number"
                      className="input-field"
                      value={form.sort_order}
                      onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Статус
                    </label>
                    <label className="flex items-center gap-3 p-3 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        className="w-5 h-5"
                        checked={form.archived}
                        onChange={(e) => setForm({ ...form, archived: e.target.checked })}
                      />
                      <span className="text-sm text-gray-700">Архивировано</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Режим регистрации
                  </label>
                  <select
                    className="input-field"
                    value={form.registration_mode}
                    onChange={(e) =>
                      setForm({ ...form, registration_mode: e.target.value as EventRow["registration_mode"] })
                    }
                  >
                    <option value="none">Только информация</option>
                    <option value="internal">Регистрация в боте</option>
                    <option value="external">Внешняя ссылка</option>
                  </select>
                </div>

                {form.registration_mode === "external" && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Внешняя ссылка
                    </label>
                    <input
                      type="url"
                      className="input-field"
                      value={form.external_url || ""}
                      onChange={(e) => setForm({ ...form, external_url: e.target.value })}
                      placeholder="https://example.com/register"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Описание (HTML)
                  </label>
                  <textarea
                    rows={6}
                    className="input-field font-mono text-sm"
                    value={form.description_html}
                    onChange={(e) => setForm({ ...form, description_html: e.target.value })}
                    placeholder="<b>Описание</b> мероприятия..."
                  />
                </div>

                <div>
                  <label className="flex items-center gap-3 p-4 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="checkbox"
                      className="w-5 h-5"
                      checked={form.reminder_enabled}
                      onChange={(e) => setForm({ ...form, reminder_enabled: e.target.checked })}
                    />
                    <div>
                      <span className="text-sm font-medium text-gray-700">
                        Включить напоминания
                      </span>
                      <p className="text-xs text-gray-500">
                        Отправлять уведомления за день до события
                      </p>
                    </div>
                  </label>
                </div>

                {form.reminder_enabled && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Текст напоминания (HTML)
                    </label>
                    <textarea
                      rows={4}
                      className="input-field font-mono text-sm"
                      value={form.reminder_snippet_html || ""}
                      onChange={(e) => setForm({ ...form, reminder_snippet_html: e.target.value })}
                      placeholder="<b>Напоминаем!</b> Завтра..."
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Даты события (для напоминаний)
                  </label>
                  <input
                    className="input-field"
                    value={datesStr}
                    onChange={(e) => setDatesStr(e.target.value)}
                    placeholder="2026-04-10, 2026-04-11"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Укажите даты в формате YYYY-MM-DD через запятую
                  </p>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-8 py-4 rounded-b-2xl flex gap-3 justify-end">
                <button type="button" onClick={closeModal} className="btn-secondary">
                  Отмена
                </button>
                <button type="submit" className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
