"use client";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes"; // <ThemeProvider attribute="class" defaultTheme="system" enableSystem> in the root layout
import { Button } from "@/components/ui/button"; // shadcn

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <Button variant="ghost" size="icon" aria-label={dark ? "Switch to light theme" : "Switch to dark theme"} onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? <Sun aria-hidden className="size-5" /> : <Moon aria-hidden className="size-5" />}
    </Button>
  );
}
