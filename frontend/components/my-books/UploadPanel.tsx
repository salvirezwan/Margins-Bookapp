"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { Trash2, BookOpen, Upload } from "lucide-react";
import { uploadBook, deleteMyBook, type UserBook } from "@/lib/api/uploads";
import { Button, buttonVariants } from "@/components/ui/button";

interface Props {
  initialBooks: UserBook[];
}

export function UploadPanel({ initialBooks }: Props) {
  const [books, setBooks] = useState<UserBook[]>(initialBooks);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "epub" && ext !== "pdf") {
      setError("Only EPUB and PDF files are supported.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File must be under 50 MB.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const book = await uploadBook(file);
      setBooks((prev) => [book, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDelete = useCallback(async (bookId: string) => {
    try {
      await deleteMyBook(bookId);
      setBooks((prev) => prev.filter((b) => b.id !== bookId));
    } catch {
      setError("Could not delete book. Please try again.");
    }
  }, []);

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={[
          "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10 cursor-pointer transition-colors",
          dragging
            ? "border-zinc-500 bg-zinc-50 dark:bg-zinc-800/50"
            : "border-zinc-300 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-500",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".epub,.pdf,application/epub+zip,application/pdf"
          className="sr-only"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <>
            <div className="h-8 w-8 rounded-full border-2 border-zinc-400 border-t-zinc-900 dark:border-t-zinc-100 animate-spin" />
            <p className="text-sm text-zinc-500">Uploading…</p>
          </>
        ) : (
          <>
            <Upload className="h-8 w-8 text-zinc-400" />
            <div className="text-center">
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Drop an EPUB or PDF here
              </p>
              <p className="text-xs text-zinc-400 mt-0.5">or click to browse — max 50 MB</p>
            </div>
          </>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
      )}

      {/* Uploaded books list */}
      {books.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
            My Library
          </h2>
          <div className="space-y-2">
            {books.map((book) => (
              <div
                key={book.id}
                className="flex items-center gap-3 rounded-lg border border-zinc-200 dark:border-zinc-800 p-3"
              >
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded bg-zinc-100 dark:bg-zinc-800">
                  <BookOpen className="h-5 w-5 text-zinc-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50 truncate">
                    {book.title}
                  </p>
                  {book.author && (
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 truncate">
                      {book.author}
                    </p>
                  )}
                  <p className="text-xs text-zinc-400 uppercase mt-0.5">
                    {book.file_format}
                    {book.file_size_bytes
                      ? ` · ${(book.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
                      : ""}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Link
                    href={`/read/${book.id}`}
                    className={buttonVariants({ size: "sm", variant: "outline" })}
                  >
                    Read
                  </Link>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-zinc-400 hover:text-red-500"
                    onClick={() => handleDelete(book.id)}
                    aria-label={`Delete ${book.title}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
