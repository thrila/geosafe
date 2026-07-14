// src/hooks/useKeyboardShortcuts.ts
import { useEffect } from "react";

type Modifier = "ctrl" | "meta" | "ctrlOrMeta" | "shift" | "alt";

interface Shortcut {
  key: string;
  modifiers?: Modifier[];
  action: () => void;
}

function matchesModifiers(event: KeyboardEvent, modifiers: Modifier[] = []): boolean {
  return modifiers.every((mod) => {
    if (mod === "ctrl") return event.ctrlKey;
    if (mod === "meta") return event.metaKey;
    if (mod === "ctrlOrMeta") return event.ctrlKey || event.metaKey;
    if (mod === "shift") return event.shiftKey;
    if (mod === "alt") return event.altKey;
    return false;
  });
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]): void {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const modifiersMatch = matchesModifiers(event, shortcut.modifiers);

        if (keyMatches && modifiersMatch) {
          event.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts]);
}
