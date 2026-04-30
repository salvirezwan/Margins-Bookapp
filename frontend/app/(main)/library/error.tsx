"use client";

import { useEffect } from "react";

export default function LibraryError({
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
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3 text-center px-6">
      <p className="text-zinc-500 dark:text-zinc-400">Failed to load the library.</p>
      <button
        onClick={reset}
        className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 transition-colors"
      >
        Try again
      </button>
    </div>
  );
}
