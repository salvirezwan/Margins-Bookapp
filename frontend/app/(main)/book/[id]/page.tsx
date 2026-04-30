import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { createClient } from "@/lib/supabase/server";
import { serverFetch } from "@/lib/api/server";
import type { Book } from "@/lib/api/books";
import type { ReadingProgress } from "@/lib/api/progress";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { BookOpen, Clock, FileText } from "lucide-react";

interface Props {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: Props) {
  const { id } = await params;
  const book = await serverFetch<Book>(`/books/${id}`).catch(() => null);
  return { title: book ? `${book.title} — margins` : "Book — margins" };
}

export default async function BookPage({ params }: Props) {
  const { id } = await params;
  const book = await serverFetch<Book>(`/books/${id}`).catch(() => null);
  if (!book) notFound();

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  let progress = null;
  if (user) {
    progress = await serverFetch<ReadingProgress>(`/me/progress/${id}`).catch(() => null);
  }

  const wordCountLabel = book.word_count
    ? book.word_count > 1000
      ? `${Math.round(book.word_count / 1000)}k words`
      : `${book.word_count} words`
    : null;

  const readingHours = book.word_count
    ? Math.round(book.word_count / 250 / 60 * 10) / 10
    : null;

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-10">
      <div className="flex flex-col sm:flex-row gap-8">
        {/* Cover */}
        <div className="flex-shrink-0 w-40 sm:w-48 mx-auto sm:mx-0">
          <div className="relative aspect-[2/3] w-full rounded-lg overflow-hidden bg-zinc-100 dark:bg-zinc-800 shadow-md">
            {book.cover_url ? (
              <Image
                src={book.cover_url}
                alt={book.title}
                fill
                sizes="192px"
                className="object-cover"
                priority
              />
            ) : (
              <div className="flex h-full items-end p-3 bg-gradient-to-br from-zinc-200 to-zinc-300 dark:from-zinc-700 dark:to-zinc-800">
                <span className="line-clamp-4 text-xs font-semibold text-zinc-600 dark:text-zinc-300">
                  {book.title}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 space-y-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              {book.title}
            </h1>
            {book.author && (
              <p className="mt-1 text-lg text-zinc-500 dark:text-zinc-400">{book.author}</p>
            )}
          </div>

          {/* Metadata pills */}
          <div className="flex flex-wrap gap-2 text-sm">
            {wordCountLabel && (
              <span className="flex items-center gap-1 text-zinc-500 dark:text-zinc-400">
                <FileText className="h-3.5 w-3.5" />
                {wordCountLabel}
              </span>
            )}
            {readingHours && (
              <span className="flex items-center gap-1 text-zinc-500 dark:text-zinc-400">
                <Clock className="h-3.5 w-3.5" />
                ~{readingHours}h read
              </span>
            )}
            {book.language && (
              <span className="text-zinc-500 dark:text-zinc-400 uppercase text-xs font-medium">
                {book.language}
              </span>
            )}
            <Badge variant="secondary" className="text-xs">
              {book.license.replace(/_/g, " ")}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {book.file_format.toUpperCase()}
            </Badge>
          </div>

          {/* Progress */}
          {progress && progress.percent_complete > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
                <span>{Math.round(progress.percent_complete)}% complete</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div
                  className="h-full rounded-full bg-zinc-900 dark:bg-zinc-100 transition-all"
                  style={{ width: `${Math.min(progress.percent_complete, 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* CTA */}
          <div className="flex gap-3 pt-1">
            {user ? (
              <Link href={`/read/${book.id}`} className={cn(buttonVariants())}>
                <BookOpen className="mr-2 h-4 w-4" />
                {progress && progress.percent_complete > 0 ? "Resume reading" : "Read now"}
              </Link>
            ) : (
              <Link href="/sign-in" className={cn(buttonVariants())}>
                Sign in to read
              </Link>
            )}
            <Link href="/library" className={cn(buttonVariants({ variant: "outline" }))}>
              ← Library
            </Link>
          </div>

          {/* Subjects */}
          {book.subjects && book.subjects.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {book.subjects.slice(0, 8).map((s) => (
                <Badge key={s} variant="secondary" className="text-xs font-normal">
                  {s}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      {book.description && (
        <div className="mt-10 prose prose-zinc dark:prose-invert max-w-none">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-2">About</h2>
          <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">{book.description}</p>
        </div>
      )}
    </div>
  );
}
