import { writable } from "svelte/store";
import { locale } from "svelte-i18n";

const STORAGE_KEY = "cybrtech_lang";

function createLanguageStore() {
  const stored = typeof localStorage !== "undefined" ? (localStorage.getItem(STORAGE_KEY) ?? "en") : "en";

  const { subscribe, set } = writable<string>(stored);

  return {
    subscribe,
    setLanguage(lang: string) {
      localStorage.setItem(STORAGE_KEY, lang);
      locale.set(lang);
      set(lang);
    },
    init() {
      locale.set(stored);
      set(stored);
    },
  };
}

export const language = createLanguageStore();
