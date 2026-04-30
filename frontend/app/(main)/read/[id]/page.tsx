import { notFound, redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { serverFetch } from "@/lib/api/server";
import type { Book } from "@/lib/api/books";
import type { ReadingProgress } from "@/lib/api/progress";
import { EpubReader } from "./EpubReader";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const book = await serverFetch<Book>(`/books/${id}`).catch(() => null);
  return { title: book ? `Reading: ${book.title} — margins` : "Reader — margins" };
}

export default async function ReadPage({ params }: Props) {
  const { id } = await params;

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/sign-in");

  const book = await serverFetch<Book>(`/books/${id}`).catch(() => null);
  if (!book) notFound();

  const progress = await serverFetch<ReadingProgress>(`/me/progress/${id}`).catch(() => null);

  return (
    <EpubReader
      book={book}
      initialLocation={progress?.current_location ?? null}
      initialPercent={progress?.percent_complete ?? 0}
    />
  );
}
