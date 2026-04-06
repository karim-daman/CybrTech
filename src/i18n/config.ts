import { addMessages, init } from "svelte-i18n";
import en from "./en.json";
import ja from "./ja.json";

addMessages("en", en);
addMessages("ja", ja);

export function setupI18n(locale: string = "en") {
  init({
    fallbackLocale: "en",
    initialLocale: locale,
  });
}

// ✅ Call it immediately at module load time so $t() is ready before first render
const stored = typeof localStorage !== "undefined" ? (localStorage.getItem("cybrtech_lang") ?? "en") : "en";

setupI18n(stored);
