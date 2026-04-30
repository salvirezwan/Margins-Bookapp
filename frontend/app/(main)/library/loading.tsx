import { BookCardSkeleton } from "@/components/library/BookCardSkeleton";

export default function LibraryLoading() {
  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 py-8 space-y-6">
      {/* Search bar skeleton */}
      <div className="max-w-md h-10 rounded-lg bg-zinc-200 dark:bg-zinc-800 animate-pulse" />
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
        {Array.from({ length: 24 }).map((_, i) => (
          <BookCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
