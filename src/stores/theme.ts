import { writable } from "svelte/store";

export interface ThemePalette {
  background: string;
  surface: string;
  primary: string;
  secondary: string;
  accent: string;
  success: string;
  warning: string;
  danger: string;
}

const STORAGE_KEY = "cybrtech-theme";

export const defaultTheme: ThemePalette = {
  background: "#080c10",
  surface: "#0d1219",
  primary: "#4a9eff",
  secondary: "#203548",
  accent: "#6ae3ff",
  success: "#39d353",
  warning: "#e3b341",
  danger: "#f47067"
};

const { subscribe, set, update } = writable<ThemePalette>(defaultTheme);

function safeHex(value: string, fallback: string) {
  return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
}

function withAlpha(hex: string, alphaHex: string) {
  return `${hex}${alphaHex}`;
}

function applyTheme(theme: ThemePalette) {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  root.style.setProperty("--bg", theme.background);
  root.style.setProperty("--surface", theme.surface);
  root.style.setProperty("--surface-strong", theme.surface);
  root.style.setProperty("--primary", theme.primary);
  root.style.setProperty("--secondary", theme.secondary);
  root.style.setProperty("--accent", theme.accent);
  root.style.setProperty("--accent-lo", withAlpha(theme.primary, "14"));
  root.style.setProperty("--border", withAlpha(theme.secondary, "55"));
  root.style.setProperty("--border-hi", theme.secondary);
  root.style.setProperty("--green", theme.success);
  root.style.setProperty("--yellow", theme.warning);
  root.style.setProperty("--red", theme.danger);
}

export const theme = {
  subscribe,
  init() {
    if (typeof window === "undefined") {
      applyTheme(defaultTheme);
      return;
    }

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        applyTheme(defaultTheme);
        return;
      }

      const parsed = JSON.parse(raw) as Partial<ThemePalette>;
      const nextTheme: ThemePalette = {
        background: safeHex(parsed.background ?? "", defaultTheme.background),
        surface: safeHex(parsed.surface ?? "", defaultTheme.surface),
        primary: safeHex(parsed.primary ?? "", defaultTheme.primary),
        secondary: safeHex(parsed.secondary ?? "", defaultTheme.secondary),
        accent: safeHex(parsed.accent ?? "", defaultTheme.accent),
        success: safeHex(parsed.success ?? "", defaultTheme.success),
        warning: safeHex(parsed.warning ?? "", defaultTheme.warning),
        danger: safeHex(parsed.danger ?? "", defaultTheme.danger)
      };

      set(nextTheme);
      applyTheme(nextTheme);
    } catch {
      applyTheme(defaultTheme);
    }
  },
  updateColor(key: keyof ThemePalette, value: string) {
    update((current) => {
      const nextTheme = { ...current, [key]: safeHex(value, current[key]) };
      applyTheme(nextTheme);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextTheme));
      }
      return nextTheme;
    });
  },
  reset() {
    set(defaultTheme);
    applyTheme(defaultTheme);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultTheme));
    }
  }
};
