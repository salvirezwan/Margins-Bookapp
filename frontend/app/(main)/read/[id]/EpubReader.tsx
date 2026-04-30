"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ReactReader, ReactReaderStyle } from "react-reader";
import { useRouter } from "next/navigation";
import type { Rendition } from "epubjs";
import type { Book } from "@/lib/api/books";
import { upsertProgress } from "@/lib/api/progress";
import { ReaderSettings } from "./ReaderSettings";
import { Settings, X, Bookmark } from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface EpubReaderProps {
  book: Book;
  initialLocation: string | null;
  initialPercent: number;
}

type Theme = "light" | "sepia" | "dark";
type FontFamily = "serif" | "sans";

const THEMES: Record<Theme, Record<string, Record<string, string>>> = {
  light: {
    body: { background: "#ffffff", color: "#1a1a1a" },
  },
  sepia: {
    body: { background: "#f5efe0", color: "#3b2f1e" },
  },
  dark: {
    body: { background: "#1a1a1a", color: "#e0e0e0" },
  },
};

const BG: Record<Theme, string> = {
  light: "#ffffff",
  sepia: "#f5efe0",
  dark: "#1a1a1a",
};

export function EpubReader({ book, initialLocation, initialPercent }: EpubReaderProps) {
  const router = useRouter();
  const [location, setLocation] = useState<string | number>(initialLocation ?? 0);
  const [percent, setPercent] = useState(initialPercent);
  const [theme, setTheme] = useState<Theme>("light");
  const [fontSize, setFontSize] = useState(16);
  const [fontFamily, setFontFamily] = useState<FontFamily>("serif");
  const [showSettings, setShowSettings] = useState(false);
  const renditionRef = useRef<Rendition | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const locationRef = useRef(location);
  const percentRef = useRef(percent);

  // Apply theme + font to rendition whenever settings change
  useEffect(() => {
    const r = renditionRef.current;
    if (!r) return;
    Object.entries(THEMES).forEach(([name, styles]) => r.themes.register(name, styles));
    r.themes.select(theme);
    r.themes.fontSize(`${fontSize}px`);
    r.themes.font(fontFamily === "serif" ? "Georgia, 'Times New Roman', serif" : "system-ui, sans-serif");
  }, [theme, fontSize, fontFamily]);

  const saveProgress = useCallback((loc: string | number, pct: number) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      void upsertProgress(book.id, {
        current_location: String(loc),
        percent_complete: Math.round(pct * 100 * 10) / 10,
      });
    }, 2000);
  }, [book.id]);

  function handleLocationChange(loc: string | number) {
    locationRef.current = loc;
    setLocation(loc);
    saveProgress(loc, percentRef.current);
  }

  function handleGetRendition(rendition: Rendition) {
    renditionRef.current = rendition;
    Object.entries(THEMES).forEach(([name, styles]) => rendition.themes.register(name, styles));
    rendition.themes.select(theme);
    rendition.themes.fontSize(`${fontSize}px`);
    rendition.themes.font(fontFamily === "serif" ? "Georgia, 'Times New Roman', serif" : "system-ui, sans-serif");

    rendition.on("rendered", (_section: unknown, view: { window: Window }) => {
      // Keyboard nav
      view.window?.addEventListener("keydown", (e: KeyboardEvent) => {
        if (e.key === "ArrowRight") rendition.next();
        if (e.key === "ArrowLeft") rendition.prev();
        if (e.key === "Escape") router.push(`/book/${book.id}`);
      });
    });

    rendition.on("relocated", (loc: { start: { percentage: number } }) => {
      const pct = loc.start.percentage ?? 0;
      percentRef.current = pct;
      setPercent(pct);
      saveProgress(locationRef.current, pct);
    });
  }

  async function handleBookmark() {
    await apiClient.post("/me/bookmarks", {
      book_id: book.id,
      location: String(locationRef.current),
      note: null,
    });
  }

  // Keyboard shortcuts at page level
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") router.push(`/book/${book.id}`);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [book.id, router]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col" style={{ background: BG[theme] }}>
      {/* Top bar */}
      <div
        className="flex items-center justify-between px-4 h-10 flex-shrink-0 border-b"
        style={{
          background: BG[theme],
          borderColor: theme === "dark" ? "#333" : "#e5e7eb",
        }}
      >
        <button
          onClick={() => router.push(`/book/${book.id}`)}
          className="flex items-center gap-1.5 text-sm opacity-60 hover:opacity-100 transition-opacity"
          style={{ color: theme === "dark" ? "#e0e0e0" : "#1a1a1a" }}
        >
          <X className="h-4 w-4" />
          <span className="hidden sm:inline truncate max-w-xs">{book.title}</span>
        </button>

        <div className="flex items-center gap-1">
          {/* Progress indicator */}
          <span className="text-xs opacity-40 mr-2" style={{ color: theme === "dark" ? "#e0e0e0" : "#1a1a1a" }}>
            {percent > 0 ? `${Math.round(percent * 100)}%` : ""}
          </span>

          <button
            onClick={handleBookmark}
            className="p-1.5 rounded opacity-60 hover:opacity-100 transition-opacity"
            style={{ color: theme === "dark" ? "#e0e0e0" : "#1a1a1a" }}
            title="Bookmark this location"
          >
            <Bookmark className="h-4 w-4" />
          </button>

          <button
            onClick={() => setShowSettings(s => !s)}
            className="p-1.5 rounded opacity-60 hover:opacity-100 transition-opacity"
            style={{ color: theme === "dark" ? "#e0e0e0" : "#1a1a1a" }}
            title="Reader settings"
          >
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Settings panel */}
      {showSettings && (
        <ReaderSettings
          theme={theme}
          fontSize={fontSize}
          fontFamily={fontFamily}
          onThemeChange={setTheme}
          onFontSizeChange={setFontSize}
          onFontFamilyChange={setFontFamily}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Reader */}
      <div className="flex-1 min-h-0">
        <ReactReader
          url={book.file_url}
          location={location}
          locationChanged={handleLocationChange}
          getRendition={handleGetRendition}
          readerStyles={{
            ...ReactReaderStyle,
            container: { ...ReactReaderStyle.container, background: BG[theme] },
            readerArea: { ...ReactReaderStyle.readerArea, background: BG[theme] },
            reader: { ...ReactReaderStyle.reader, background: BG[theme] },
            arrow: { ...ReactReaderStyle.arrow, color: theme === "dark" ? "#e0e0e0" : "#1a1a1a" },
            arrowHover: { ...ReactReaderStyle.arrowHover, color: theme === "dark" ? "#fff" : "#000" },
            titleArea: { display: "none" },
          }}
          epubOptions={{ flow: "paginated" }}
        />
      </div>
    </div>
  );
}
