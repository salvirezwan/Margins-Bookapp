"use client";

import Image from "next/image";
import Link from "next/link";
import type { BookListItem } from "@/lib/api/books";

interface BookCardProps {
  book: BookListItem;
  progress?: number;
}

export function BookCard({ book, progress }: BookCardProps) {
  return (
    <Link href={`/book/${book.id}`} className="group block">
      <div className="relative aspect-[2/3] w-full overflow-hidden rounded-md bg-zinc-100 dark:bg-zinc-800 shadow-sm transition-transform duration-200 group-hover:scale-[1.03] group-hover:shadow-md">
        {book.cover_url ? (
          <Image
            src={book.cover_url}
            alt={book.title}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full items-end p-3 bg-gradient-to-br from-zinc-200 to-zinc-300 dark:from-zinc-700 dark:to-zinc-800">
            <span className="line-clamp-3 text-xs font-semibold text-zinc-600 dark:text-zinc-300 leading-snug">
              {book.title}
            </span>
          </div>
        )}
        {progress !== undefined && progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-300 dark:bg-zinc-700">
            <div
              className="h-full bg-zinc-900 dark:bg-zinc-100 transition-all"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        )}
      </div>
      <div className="mt-2 space-y-0.5">
        <p className="line-clamp-2 text-sm font-medium text-zinc-900 dark:text-zinc-50 leading-snug">
          {book.title}
        </p>
        {book.author && (
          <p className="line-clamp-1 text-xs text-zinc-500 dark:text-zinc-400">
            {book.author}
          </p>
        )}
      </div>
    </Link>
  );
}
