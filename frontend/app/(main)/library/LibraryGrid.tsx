"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BookCard } from "@/components/library/BookCard";
import { BookCardSkeleton } from "@/components/library/BookCardSkeleton";
import { SearchBar } from "@/components/library/SearchBar";
import { listBooks, type BookListItem, type BookListResponse } from "@/lib/api/books";

interface LibraryGridProps {
  initial: BookListResponse | null;
}

const PAGE_SIZE = 24;

export function LibraryGrid({ initial }: LibraryGridProps) {
  const [books, setBooks] = useState<BookListItem[]>(initial?.items ?? []);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(initial?.has_next ?? false);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const queryRef = useRef(query);
  const pageRef = useRef(page);
  const initialLoadDone = useRef(!!initial);

  const loadPage = useCallback(async (q: string, p: number, replace: boolean) => {
    if (replace) setSearching(true);
    else setLoading(true);
    try {
      const data = await listBooks({ page: p, page_size: PAGE_SIZE, q: q || undefined });
      setBooks(prev => replace ? data.items : [...prev, ...data.items]);
      setHasNext(data.has_next);
      setPage(p);
      pageRef.current = p;
    } catch {
      // leave existing results intact
    } finally {
      setSearching(false);
      setLoading(false);
    }
  }, []);

  function handleQueryChange(q: string) {
    queryRef.current = q;
    setQuery(q);
    void loadPage(q, 1, true);
  }

  // Infinite scroll observer — skip the very first intersection when server data already fills the page
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0].isIntersecting) return;
        if (initialLoadDone.current) {
          initialLoadDone.current = false;
          return;
        }
        if (hasNext && !loading && !searching) {
          void loadPage(queryRef.current, pageRef.current + 1, false);
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNext, loading, searching, loadPage]);

  return (
    <div className="space-y-6">
      <div className="max-w-md">
        <SearchBar value={query} onChange={handleQueryChange} />
      </div>

      {searching ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
          {Array.from({ length: PAGE_SIZE }).map((_, i) => <BookCardSkeleton key={i} />)}
        </div>
      ) : books.length === 0 ? (
        <div className="py-24 text-center">
          <p className="text-zinc-500 dark:text-zinc-400">
            No books found{query ? ` for "${query}"` : ""}.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6">
            {books.map(book => <BookCard key={book.id} book={book} />)}
            {loading && Array.from({ length: 6 }).map((_, i) => <BookCardSkeleton key={`sk-${i}`} />)}
          </div>
          <div ref={sentinelRef} className="h-1" />
        </>
      )}
    </div>
  );
}
