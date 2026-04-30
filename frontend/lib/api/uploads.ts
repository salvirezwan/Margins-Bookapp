import { createClient } from "@/lib/supabase/client";
import { ApiError } from "./client";

const API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL ?? "http://localhost:8000";

export interface UserBook {
  id: string;
  title: string;
  author: string | null;
  language: string | null;
  cover_url: string | null;
  file_url: string;
  file_format: "epub" | "pdf";
  file_size_bytes: number | null;
  word_count: number | null;
  created_at: string;
}

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  let { data } = await supabase.auth.getSession();
  if (!data.session) {
    const refreshed = await supabase.auth.refreshSession();
    data = refreshed.data;
  }
  return data.session?.access_token ?? null;
}

export async function listMyBooks(): Promise<UserBook[]> {
  const token = await getToken();
  const res = await fetch(`${API_URL}/me/books`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new ApiError(res.status, await res.text().catch(() => res.statusText));
  return res.json() as Promise<UserBook[]>;
}

export async function uploadBook(file: File): Promise<UserBook> {
  const token = await getToken();
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/me/books`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<UserBook>;
}

export async function deleteMyBook(bookId: string): Promise<void> {
  const token = await getToken();
  const res = await fetch(`${API_URL}/me/books/${bookId}`, {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok && res.status !== 204) {
    throw new ApiError(res.status, await res.text().catch(() => res.statusText));
  }
}
