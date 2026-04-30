import { apiClient } from "./client";

export interface ReadingProgress {
  book_id: string;
  current_location: string;
  percent_complete: number;
  last_read_at: string;
}

export interface ProgressUpsert {
  current_location: string;
  percent_complete: number;
}

export function getProgress(bookId: string): Promise<ReadingProgress | null> {
  return apiClient.get<ReadingProgress | null>(`/me/progress/${bookId}`);
}

export function getAllProgress(): Promise<ReadingProgress[]> {
  return apiClient.get<ReadingProgress[]>("/me/progress");
}

export function upsertProgress(
  bookId: string,
  data: ProgressUpsert
): Promise<ReadingProgress> {
  return apiClient.put<ReadingProgress>(`/me/progress/${bookId}`, data);
}
