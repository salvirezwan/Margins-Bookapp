import { redirect } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { createClient } from "@/lib/supabase/server";
import { serverFetch } from "@/lib/api/server";
import type { ReadingProgress } from "@/lib/api/progress";
import type { Book } from "@/lib/api/books";

export const metadata = { title: "My Books — margins" };

interface ProgressWithBook extends ReadingProgress {
  book: Book;
}

export default async function MyBooksPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/sign-in");

  const progressList = await serverFetch<ReadingProgress[]>("/me/progress").catch(() => []);

  // Fetch book details for each progress entry
  const withBooks = (
    await Promise.all(
      progressList.map(async (p) => {
        const book = await serverFetch<Book>(`/books/${p.book_id}`).catch(() => null);
        if (!book) return null;
        return { ...p, book } as ProgressWithBook;
      })
    )
  ).filter((x): x is ProgressWithBook => x !== null);

  const inProgress = withBooks.filter((p) => p.percent_complete > 0 && p.percent_complete < 99);
  const finished = withBooks.filter((p) => p.percent_complete >= 99);

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-10 space-y-10">
      <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">My Books</h1>

      {withBooks.length === 0 ? (
        <div className="py-24 text-center space-y-4">
          <p className="text-zinc-500 dark:text-zinc-400">You haven&apos;t started reading anything yet.</p>
          <Link
            href="/library"
            className="inline-block rounded-full bg-zinc-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 transition-colors"
          >
            Browse the library
          </Link>
        </div>
      ) : (
        <>
          {inProgress.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">Continue reading</h2>
              <div className="space-y-3">
                {inProgress.map((p) => (
                  <ProgressRow key={p.book_id} p={p} />
                ))}
              </div>
            </section>
          )}

          {finished.length > 0 && (
            <section className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">Finished</h2>
              <div className="space-y-3">
                {finished.map((p) => (
                  <ProgressRow key={p.book_id} p={p} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function ProgressRow({ p }: { p: ProgressWithBook }) {
  const pct = Math.min(Math.round(p.percent_complete), 100);
  return (
    <Link
      href={`/read/${p.book_id}`}
      className="flex items-center gap-4 rounded-lg border border-zinc-200 dark:border-zinc-800 p-3 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors"
    >
      <div className="relative h-16 w-11 flex-shrink-0 rounded overflow-hidden bg-zinc-100 dark:bg-zinc-800">
        {p.book.cover_url ? (
          <Image src={p.book.cover_url} alt={p.book.title} fill sizes="44px" className="object-cover" />
        ) : (
          <div className="h-full w-full bg-gradient-to-br from-zinc-200 to-zinc-300 dark:from-zinc-700 dark:to-zinc-800" />
        )}
      </div>
      <div className="flex-1 min-w-0 space-y-1.5">
        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50 truncate">{p.book.title}</p>
        {p.book.author && (
          <p className="text-xs text-zinc-500 dark:text-zinc-400 truncate">{p.book.author}</p>
        )}
        <div className="flex items-center gap-2">
          <div className="h-1 flex-1 rounded-full bg-zinc-200 dark:bg-zinc-700">
            <div
              className="h-full rounded-full bg-zinc-900 dark:bg-zinc-100"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-zinc-400 tabular-nums w-8 text-right">{pct}%</span>
        </div>
      </div>
    </Link>
  );
}
