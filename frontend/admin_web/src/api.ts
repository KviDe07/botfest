export function getToken(): string | null {
  return sessionStorage.getItem("token");
}

export function setToken(t: string) {
  sessionStorage.setItem("token", t);
}

export function clearToken() {
  sessionStorage.removeItem("token");
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (init.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
  const res = await fetch(path, { ...init, headers });
  if (res.status === 401) {
    clearToken();
    if (!path.includes("/auth/login")) window.location.href = "/login";
  }
  return res;
}
