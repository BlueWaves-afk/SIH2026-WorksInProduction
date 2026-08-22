import { createContext, useContext, useMemo, type ReactNode } from "react";
import en from "./en.json";
import hi from "./hi.json";
import mr from "./mr.json";

export type Locale = "en" | "hi" | "mr";

type Dict = Record<string, string>;
const DICTS: Record<Locale, Dict> = { en, hi, mr };

export const LOCALE_NAMES: Record<Locale, string> = { en: "English", hi: "हिंदी", mr: "मराठी" };

const LocaleContext = createContext<Locale>("en");

export function LocaleProvider({ locale, children }: { locale: Locale; children: ReactNode }) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

/**
 * Translation lookup. Falls back to English, then to the key itself, so a missing
 * translation degrades to readable text rather than a blank screen.
 * `vars` does simple {name} interpolation.
 */
export function useT() {
  const locale = useContext(LocaleContext);
  return useMemo(() => {
    return (key: string, vars?: Record<string, string | number>) => {
      const raw = DICTS[locale][key] ?? DICTS.en[key] ?? key;
      if (!vars) return raw;
      return Object.entries(vars).reduce((acc, [k, v]) => acc.split(`{${k}}`).join(String(v)), raw);
    };
  }, [locale]);
}

export function useLocale(): Locale {
  return useContext(LocaleContext);
}

/** Dev helper: which keys are missing from a non-English dictionary. */
export function missingKeys(locale: Locale): string[] {
  return Object.keys(DICTS.en).filter((k) => !(k in DICTS[locale]));
}

/** Non-hook lookup, for components that render the provider itself. */
export function translate(locale: Locale) {
  return (key: string, vars?: Record<string, string | number>) => {
    const raw = DICTS[locale][key] ?? DICTS.en[key] ?? key;
    if (!vars) return raw;
    return Object.entries(vars).reduce((acc, [k, v]) => acc.split(`{${k}}`).join(String(v)), raw);
  };
}
