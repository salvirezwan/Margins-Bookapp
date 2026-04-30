import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getAuthHeader(): Promise<Record<string, string>> {
  const supabase = createClient();
  // getSession() can return a stale token on first client render.
  // refreshSession() exchanges the cookie for a fresh access_token.
  const { data } = await supabase.auth.refreshSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeader = await getAuthHeader();

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

export const apiClient = {
  get<T>(path: string, options?: RequestInit) {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body: unknown, options?: RequestInit) {
    return request<T>(path, {
      ...options,
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  put<T>(path: string, body: unknown, options?: RequestInit) {
    return request<T>(path, {
      ...options,
      method: "PUT",
      body: JSON.stringify(body),
    });
  },
  delete<T>(path: string, options?: RequestInit) {
    return request<T>(path, { ...options, method: "DELETE" });
  },
};

export { ApiError };
