export default function BookLoading() {
  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 py-10">
      <div className="flex flex-col sm:flex-row gap-8 animate-pulse">
        {/* Cover skeleton */}
        <div className="flex-shrink-0 w-40 sm:w-48 mx-auto sm:mx-0">
          <div className="aspect-[2/3] w-full rounded-lg bg-zinc-200 dark:bg-zinc-800" />
        </div>
        {/* Info skeleton */}
        <div className="flex-1 space-y-4 pt-2">
          <div className="space-y-2">
            <div className="h-8 w-3/4 rounded bg-zinc-200 dark:bg-zinc-800" />
            <div className="h-5 w-1/3 rounded bg-zinc-200 dark:bg-zinc-800" />
          </div>
          <div className="flex gap-2">
            <div className="h-5 w-16 rounded bg-zinc-200 dark:bg-zinc-800" />
            <div className="h-5 w-16 rounded bg-zinc-200 dark:bg-zinc-800" />
          </div>
          <div className="flex gap-3 pt-1">
            <div className="h-9 w-32 rounded-md bg-zinc-200 dark:bg-zinc-800" />
            <div className="h-9 w-24 rounded-md bg-zinc-200 dark:bg-zinc-800" />
          </div>
        </div>
      </div>
    </div>
  );
}
