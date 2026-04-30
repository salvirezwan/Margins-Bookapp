"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function BookError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center gap-4">
      <p className="text-zinc-500 dark:text-zinc-400">Failed to load this book.</p>
      <div className="flex gap-3">
        <button
          onClick={reset}
          className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 transition-colors"
        >
          Try again
        </button>
        <Link
          href="/library"
          className="rounded-full border border-zinc-200 px-5 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800 transition-colors"
        >
          ← Library
        </Link>
      </div>
    </div>
  );
}
