"use client";

import { X } from "lucide-react";

type Theme = "light" | "sepia" | "dark";
type FontFamily = "serif" | "sans";

interface ReaderSettingsProps {
  theme: Theme;
  fontSize: number;
  fontFamily: FontFamily;
  onThemeChange: (t: Theme) => void;
  onFontSizeChange: (s: number) => void;
  onFontFamilyChange: (f: FontFamily) => void;
  onClose: () => void;
}

const THEMES: { value: Theme; label: string; bg: string; text: string }[] = [
  { value: "light", label: "Light", bg: "#ffffff", text: "#1a1a1a" },
  { value: "sepia", label: "Sepia", bg: "#f5efe0", text: "#3b2f1e" },
  { value: "dark", label: "Dark", bg: "#1a1a1a", text: "#e0e0e0" },
];

export function ReaderSettings({
  theme,
  fontSize,
  fontFamily,
  onThemeChange,
  onFontSizeChange,
  onFontFamilyChange,
  onClose,
}: ReaderSettingsProps) {
  const isDark = theme === "dark";
  const panelBg = isDark ? "#2a2a2a" : "#f9f9f7";
  const textColor = isDark ? "#e0e0e0" : "#1a1a1a";
  const borderColor = isDark ? "#444" : "#e5e7eb";

  return (
    <div
      className="absolute right-4 top-12 z-50 w-64 rounded-lg shadow-xl border p-4 space-y-4"
      style={{ background: panelBg, color: textColor, borderColor }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">Settings</span>
        <button onClick={onClose} className="opacity-60 hover:opacity-100">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Theme */}
      <div className="space-y-1.5">
        <p className="text-xs opacity-60 uppercase tracking-wide">Theme</p>
        <div className="flex gap-2">
          {THEMES.map(t => (
            <button
              key={t.value}
              onClick={() => onThemeChange(t.value)}
              className="flex-1 rounded py-1.5 text-xs font-medium border transition-all"
              style={{
                background: t.bg,
                color: t.text,
                borderColor: theme === t.value ? "#6366f1" : borderColor,
                boxShadow: theme === t.value ? "0 0 0 2px #6366f1" : "none",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Font size */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <p className="text-xs opacity-60 uppercase tracking-wide">Font size</p>
          <span className="text-xs opacity-60">{fontSize}px</span>
        </div>
        <input
          type="range"
          min={12}
          max={28}
          step={1}
          value={fontSize}
          onChange={e => onFontSizeChange(Number(e.target.value))}
          className="w-full accent-indigo-500"
        />
      </div>

      {/* Font family */}
      <div className="space-y-1.5">
        <p className="text-xs opacity-60 uppercase tracking-wide">Font</p>
        <div className="flex gap-2">
          {(["serif", "sans"] as FontFamily[]).map(f => (
            <button
              key={f}
              onClick={() => onFontFamilyChange(f)}
              className="flex-1 rounded py-1.5 text-xs border transition-all"
              style={{
                fontFamily: f === "serif" ? "Georgia, serif" : "system-ui, sans-serif",
                borderColor: fontFamily === f ? "#6366f1" : borderColor,
                boxShadow: fontFamily === f ? "0 0 0 2px #6366f1" : "none",
                background: "transparent",
                color: textColor,
              }}
            >
              {f === "serif" ? "Serif" : "Sans"}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
