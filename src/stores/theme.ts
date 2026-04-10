import { get, writable } from "svelte/store";

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

export interface ThemePreset {
  id: string;
  name: string;
  palette: ThemePalette;
}

const STORAGE_KEY = "cybrtech-theme";
const PRESETS_STORAGE_KEY = "cybrtech-theme-presets";

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

const themeStore = writable<ThemePalette>(defaultTheme);
const presetsStore = writable<ThemePreset[]>([]);

function safeHex(value: string, fallback: string) {
  return /^#[0-9a-f]{6}$/i.test(value) ? value : fallback;
}

function withAlpha(hex: string, alphaHex: string) {
  return `${hex}${alphaHex}`;
}

function sanitizeTheme(input?: Partial<ThemePalette>): ThemePalette {
  return {
    background: safeHex(input?.background ?? "", defaultTheme.background),
    surface: safeHex(input?.surface ?? "", defaultTheme.surface),
    primary: safeHex(input?.primary ?? "", defaultTheme.primary),
    secondary: safeHex(input?.secondary ?? "", defaultTheme.secondary),
    accent: safeHex(input?.accent ?? "", defaultTheme.accent),
    success: safeHex(input?.success ?? "", defaultTheme.success),
    warning: safeHex(input?.warning ?? "", defaultTheme.warning),
    danger: safeHex(input?.danger ?? "", defaultTheme.danger)
  };
}

function sanitizePresets(input: unknown): ThemePreset[] {
  if (!Array.isArray(input)) return [];

  return input
    .map((entry, index) => {
      if (!entry || typeof entry !== "object") return null;

      const candidate = entry as Partial<ThemePreset> & { palette?: Partial<ThemePalette> };
      const name = typeof candidate.name === "string" ? candidate.name.trim() : "";
      if (!name) return null;

      return {
        id: typeof candidate.id === "string" && candidate.id.trim() ? candidate.id : `preset-${index}`,
        name,
        palette: sanitizeTheme(candidate.palette)
      };
    })
    .filter((preset): preset is ThemePreset => Boolean(preset));
}

function persistTheme(nextTheme: ThemePalette) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextTheme));
}

function persistPresets(nextPresets: ThemePreset[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(nextPresets));
}

function applyTheme(nextTheme: ThemePalette) {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  root.style.setProperty("--bg", nextTheme.background);
  root.style.setProperty("--surface", nextTheme.surface);
  root.style.setProperty("--surface-strong", nextTheme.surface);
  root.style.setProperty("--primary", nextTheme.primary);
  root.style.setProperty("--secondary", nextTheme.secondary);
  root.style.setProperty("--accent", nextTheme.accent);
  root.style.setProperty("--accent-lo", withAlpha(nextTheme.primary, "14"));
  root.style.setProperty("--border", withAlpha(nextTheme.secondary, "55"));
  root.style.setProperty("--border-hi", nextTheme.secondary);
  root.style.setProperty("--green", nextTheme.success);
  root.style.setProperty("--yellow", nextTheme.warning);
  root.style.setProperty("--red", nextTheme.danger);
}

export const savedThemePresets = {
  subscribe: presetsStore.subscribe
};

export const theme = {
  subscribe: themeStore.subscribe,
  init() {
    if (typeof window === "undefined") {
      themeStore.set(defaultTheme);
      presetsStore.set([]);
      applyTheme(defaultTheme);
      return;
    }

    try {
      const rawTheme = window.localStorage.getItem(STORAGE_KEY);
      const parsedTheme = rawTheme ? (JSON.parse(rawTheme) as Partial<ThemePalette>) : defaultTheme;
      const nextTheme = sanitizeTheme(parsedTheme);
      themeStore.set(nextTheme);
      applyTheme(nextTheme);
    } catch {
      themeStore.set(defaultTheme);
      applyTheme(defaultTheme);
    }

    try {
      const rawPresets = window.localStorage.getItem(PRESETS_STORAGE_KEY);
      const parsedPresets = rawPresets ? JSON.parse(rawPresets) : [];
      presetsStore.set(sanitizePresets(parsedPresets));
    } catch {
      presetsStore.set([]);
    }
  },
  updateColor(key: keyof ThemePalette, value: string) {
    themeStore.update((current) => {
      const nextTheme = { ...current, [key]: safeHex(value, current[key]) };
      applyTheme(nextTheme);
      persistTheme(nextTheme);
      return nextTheme;
    });
  },
  reset() {
    themeStore.set(defaultTheme);
    applyTheme(defaultTheme);
    persistTheme(defaultTheme);
  },
  savePreset(name: string) {
    const normalizedName = name.trim();
    if (!normalizedName) return null;

    const currentTheme = get(themeStore);
    const currentPresets = get(presetsStore);
    const presetId = normalizedName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || `preset-${Date.now()}`;

    const nextPreset: ThemePreset = {
      id: presetId,
      name: normalizedName,
      palette: { ...currentTheme }
    };

    const nextPresets = [...currentPresets.filter((preset) => preset.id !== presetId && preset.name.toLowerCase() !== normalizedName.toLowerCase()), nextPreset].sort((a, b) =>
      a.name.localeCompare(b.name)
    );

    presetsStore.set(nextPresets);
    persistPresets(nextPresets);
    return presetId;
  },
  applyPreset(id: string) {
    const preset = get(presetsStore).find((entry) => entry.id === id);
    if (!preset) return false;

    const nextTheme = sanitizeTheme(preset.palette);
    themeStore.set(nextTheme);
    applyTheme(nextTheme);
    persistTheme(nextTheme);
    return true;
  },
  deletePreset(id: string) {
    const nextPresets = get(presetsStore).filter((preset) => preset.id !== id);
    presetsStore.set(nextPresets);
    persistPresets(nextPresets);
  }
};
