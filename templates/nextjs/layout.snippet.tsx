// app/layout.tsx essentials (Geist fonts, tokens, theme, project icon comes from app/icon.svg + app/apple-icon.png)
import "./globals.css"; // contains: @import/paste of house-style.css
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${sans.variable} ${mono.variable}`}>
      <body className="font-sans">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-3">Skip to content</a>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <main id="main">{children}</main> {/* layout owns the one <main>; pages must not render another */}
        </ThemeProvider>
      </body>
    </html>
  );
}
