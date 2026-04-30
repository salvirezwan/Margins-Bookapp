import { Suspense } from "react";
import { listBooks } from "@/lib/api/books";
import { LibraryGrid } from "./LibraryGrid";
import { BookCardSkeleton } from "@/components/library/BookCardSkeleton";

export const metadata = { title: "Library — margins" };

export default async function LibraryPage() {
  const initial = await listBooks({ page: 1, page_size: 24 }).catch(() => null);

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          Library
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          {initial ? `${initial.total.toLocaleString()} books` : "Browse public domain books"}
        </p>
      </div>

      <Suspense fallback={
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
          {Array.from({ length: 24 }).map((_, i) => <BookCardSkeleton key={i} />)}
        </div>
      }>
        <LibraryGrid initial={initial} />
      </Suspense>
    </div>
  );
}
