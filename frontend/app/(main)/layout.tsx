import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export default async function MainLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50 dark:bg-zinc-950">
      <header className="sticky top-0 z-40 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto max-w-7xl flex h-14 items-center justify-between px-4 sm:px-6">
          <Link
            href="/library"
            className="text-lg font-bold tracking-tight text-zinc-900 dark:text-zinc-50"
          >
            margins
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            {user ? (
              <>
                <Link
                  href="/library"
                  className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50 transition-colors"
                >
                  Library
                </Link>
                <Link
                  href="/my-books"
                  className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50 transition-colors"
                >
                  My Books
                </Link>
              </>
            ) : (
              <Link
                href="/sign-in"
                className="font-medium text-zinc-900 dark:text-zinc-50"
              >
                Sign in
              </Link>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
