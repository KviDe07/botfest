import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "../api";
import { Save, Sliders, AlertCircle } from "lucide-react";

type AppSettings = {
  reminder_hour_msk: number;
  schedule_caption: string;
  schedule_image_path: string;
  schedule_missing_message: string;
  admin_brand_title: string;
};

export default function Settings() {
  const [form, setForm] = useState<AppSettings | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    (async () => {
      const res = await apiFetch("/api/settings");
      if (!res.ok) {
        setErr("Не удалось загрузить настройки");
        return;
      }
      setForm(await res.json());
    })();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form) return;
    setErr(null);
    setSaved(false);
    setSaving(true);
    try {
      const res = await apiFetch("/api/settings", {
        method: "PATCH",
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        setErr("Ошибка сохранения");
        return;
      }
      const next = await res.json();
      setForm(next);
      setSaved(true);
      window.dispatchEvent(new CustomEvent("app-settings-updated", { detail: next }));
    } finally {
      setSaving(false);
    }
  }

  if (!form)
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent" />
          <p className="text-gray-600 font-medium">Загрузка настроек...</p>
        </div>
      </div>
    );

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl">
          <Sliders className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Настройки
          </h1>
          <p className="text-gray-600 mt-1">Бот, напоминания и оформление панели</p>
        </div>
      </div>

      {err && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm font-medium">{err}</p>
        </div>
      )}

      {saved && (
        <p className="text-sm text-green-600 font-medium">Сохранено</p>
      )}

      <form onSubmit={onSubmit} className="card space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Название в шапке админки
          </label>
          <input
            className="input-field"
            value={form.admin_brand_title}
            onChange={(e) => setForm({ ...form, admin_brand_title: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Час напоминаний (МСК, 0–23)
          </label>
          <input
            type="number"
            min={0}
            max={23}
            className="input-field max-w-xs"
            value={form.reminder_hour_msk}
            onChange={(e) =>
              setForm({ ...form, reminder_hour_msk: Math.min(23, Math.max(0, Number(e.target.value))) })
            }
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Ежедневный запуск рассылки «за день до события» в этот час по Москве
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Подпись к фото расписания в боте
          </label>
          <input
            className="input-field"
            value={form.schedule_caption}
            onChange={(e) => setForm({ ...form, schedule_caption: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Изображение расписания
          </label>
          <input
            className="input-field font-mono text-sm"
            value={form.schedule_image_path}
            onChange={(e) => setForm({ ...form, schedule_image_path: e.target.value })}
            placeholder="media/schedule.jpg или https://..."
          />
          <p className="text-xs text-gray-500 mt-1">
            Локальный путь от рабочей директории бота или прямая ссылка (https)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Сообщение, если файл не найден / ошибка загрузки
          </label>
          <textarea
            rows={2}
            className="input-field"
            value={form.schedule_missing_message}
            onChange={(e) => setForm({ ...form, schedule_missing_message: e.target.value })}
          />
        </div>

        <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2">
          {saving ? (
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
          ) : (
            <Save className="w-5 h-5" />
          )}
          Сохранить
        </button>
      </form>
    </div>
  );
}
