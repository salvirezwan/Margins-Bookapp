import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950 px-6">
      <div className="max-w-lg text-center space-y-6">
        <h1 className="text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          margins
        </h1>
        <p className="text-lg text-zinc-500 dark:text-zinc-400">
          A distraction-free reader for the world&apos;s great books.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/library"
            className="rounded-full bg-zinc-900 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Browse library
          </Link>
          <Link
            href="/sign-in"
            className="rounded-full border border-zinc-200 px-6 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
