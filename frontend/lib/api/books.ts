import { apiClient } from "./client";

export interface Book {
  id: string;
  title: string;
  author: string | null;
  language: string | null;
  description: string | null;
  cover_url: string | null;
  file_url: string;
  file_format: "epub" | "pdf" | "txt" | "cbz";
  file_size_bytes: number | null;
  page_count: number | null;
  word_count: number | null;
  source: string;
  license: string;
  visibility: "public" | "private";
  download_count: number;
  subjects: string[];
  created_at: string;
  updated_at: string;
}

export interface BookListResponse {
  items: BookListItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface BookListItem {
  id: string;
  title: string;
  author: string | null;
  language: string | null;
  cover_url: string | null;
  file_format: "epub" | "pdf" | "txt" | "cbz";
  word_count: number | null;
  license: string;
  created_at: string;
}

export interface BookListParams {
  page?: number;
  page_size?: number;
  q?: string;
  language?: string;
}

export function listBooks(params: BookListParams = {}): Promise<BookListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.page_size) query.set("page_size", String(params.page_size));
  if (params.q) query.set("q", params.q);
  if (params.language) query.set("language", params.language);
  const qs = query.toString();
  return apiClient.get<BookListResponse>(`/books${qs ? `?${qs}` : ""}`);
}

export function getBook(id: string): Promise<Book> {
  return apiClient.get<Book>(`/books/${id}`);
}
