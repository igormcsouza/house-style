#!/usr/bin/env python3
"""Copy house-style templates into a project. Never overwrites an existing file; prints created/skipped.
  scaffold.py STACK [--dest .] [--css-dir app] [--app-dir app] [--name N] [--owner O] [--repo R] [--author A] [--accent green]
STACK: nextjs | expo | mkdocs | fastapi | fastmcp | docs   (docs = README/AGENTS/CLAUDE/CONTRIBUTING/CHANGELOG/LICENSE/PR template)"""
import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import tokens  # noqa: E402

T = Path(__file__).resolve().parent.parent / "templates"
TW_CONFIGS = ("tailwind.config.ts", "tailwind.config.js", "tailwind.config.mjs", "tailwind.config.cjs")
NEXT_CONFIG = '''import type { Config } from "tailwindcss";

const config: Config = {
  presets: [require("./{css}/house-style.preset.js")],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
};

export default config;
'''
EXPO_CONFIG = '''module.exports = {
  presets: [require("nativewind/preset"), require("./{css}/house-style.preset.js")],
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
};
'''


class Out:
    def __init__(self, dest):
        self.dest, self.created, self.skipped, self.notes = Path(dest), [], [], []

    def put(self, rel, text=None, src=None):
        f = self.dest / rel
        if f.exists():
            self.skipped.append(str(rel))
            return
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text) if text is not None else shutil.copyfile(src, f)
        self.created.append(str(rel))


def git_user():
    r = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
    return r.stdout.strip() or "The Authors"


def fill(text, a):
    for k, v in (("<Name>", a.name), ("<Project>", a.name), ("<owner>", a.owner), ("<repo>", a.repo)):
        text = text.replace(k, v)
    return text


def docs(o, a):
    d = o.dest
    for rel, src in (("README.md", "README.md"), ("AGENTS.md", "AGENTS.md"), ("CONTRIBUTING.md", "CONTRIBUTING.md"),
                     ("CHANGELOG.md", "CHANGELOG.md"), (".github/pull_request_template.md", "release/pull_request_template.md")):
        text = fill((T / src).read_text(), a)
        if src == "README.md":
            if not (d / "mkdocs.yml").exists():  # no docs site: drop its badge and section
                text = "\n".join(ln for ln in text.splitlines() if "badge/docs" not in ln)
                text = text.replace("## Documentation\n\nFull docs: <link>. Architecture and decisions: `docs/project/`.\n\n", "")
            if not (d / "brand/icon.svg").exists():
                text = text.replace('<img src="brand/icon.svg" alt="" width="56" align="left">\n\n', "")
        o.put(rel, text)
    claude = d / "CLAUDE.md"
    if not claude.exists():
        o.put("CLAUDE.md", "@AGENTS.md\n")
    elif claude.read_text().strip() != "@AGENTS.md":
        o.notes.append("CLAUDE.md exists with its own content: move it into AGENTS.md, then make CLAUDE.md just `@AGENTS.md`")
    lic = (Path(__file__).resolve().parent.parent / "LICENSE").read_text()
    o.put("LICENSE", lic.replace("2026 Igor Souza", f"{datetime.date.today().year} {a.author}"))


def tw_major(dest):
    try:
        pkg = json.loads((dest / "package.json").read_text())
        v = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}.get("tailwindcss", "")
        return int(v.lstrip("^~>=v ").split(".")[0])
    except (OSError, ValueError):
        return 3


def tailwind_config(o, a, body):
    if tw_major(o.dest) >= 4:
        o.notes.append("Tailwind 4: no tailwind.config needed; generate tokens with `build.py --tailwind 4` (house-style.css imports tailwindcss itself, remove the default globals.css import)")
    elif any((o.dest / c).exists() for c in TW_CONFIGS):
        o.notes.append(f'tailwind config exists: add `presets: [require("./{a.css_dir}/house-style.preset.js")]` to it')
    else:
        name, text = body
        o.put(name, text.replace("{css}", a.css_dir))


def stack(o, a):
    s = a.stack
    if s == "nextjs":
        for f in ("skeleton", "spinner", "action-button", "states", "theme-toggle"):
            o.put(f"components/{f}.tsx", src=T / "nextjs" / f"{f}.tsx")
        o.put(f"{a.app_dir}/loading.tsx", src=T / "nextjs" / "loading.tsx")
        css_import = "./house-style.css" if a.css_dir == a.app_dir else f"../{a.css_dir}/house-style.css"
        layout = (T / "nextjs" / "layout.snippet.tsx").read_text().replace("./globals.css", css_import)
        o.put(f"{a.app_dir}/layout.tsx", layout)
        existing = o.dest / a.app_dir / "layout.tsx"
        if f"{a.app_dir}/layout.tsx" in o.skipped and "house-style.css" not in existing.read_text():
            o.notes.append(f'{a.app_dir}/layout.tsx exists: replace the globals.css import with "{css_import}", wrap children in <ThemeProvider attribute="class" defaultTheme="system" enableSystem><main id="main">...</main></ThemeProvider>, add suppressHydrationWarning on <html> and a skip link (see templates/nextjs/layout.snippet.tsx)')
        tailwind_config(o, a, ("tailwind.config.ts", NEXT_CONFIG))
        o.notes.append("install: npm i lucide-react next-themes clsx tailwind-merge; npx shadcn@latest init && npx shadcn@latest add button (templates import @/components/ui/button and @/lib/utils)")
    elif s == "expo":
        for f in ("Skeleton", "ActionButton", "States"):
            o.put(f"components/{f}.tsx", src=T / "expo" / f"{f}.tsx")
        tailwind_config(o, a, ("tailwind.config.js", EXPO_CONFIG))
        o.notes.append("install: npx expo install nativewind react-native-reanimated lucide-react-native react-native-svg; import house-style.css in app/_layout.tsx")
    elif s == "mkdocs":
        o.put("mkdocs.yml", (T / "mkdocs" / "mkdocs.yml").read_text().replace("{{name}}", a.name).replace("{{accent}}", tokens.MATERIAL[a.accent]))
        if (o.dest / "brand/icon.svg").exists():
            o.put("docs/assets/icon.svg", src=o.dest / "brand/icon.svg")
        o.put("docs/index.md", f"# {a.name}\n\nWhat it is, why it exists, how to start.\n")
        o.put(".github/workflows/docs.yml", src=T / "release" / "docs.yml")
    elif s in ("fastapi", "fastmcp"):
        for f in sorted((T / s).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                o.put(f.relative_to(T / s), src=f)
    elif s == "docs":
        docs(o, a)
    return o


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stack", choices=("nextjs", "expo", "mkdocs", "fastapi", "fastmcp", "docs"))
    p.add_argument("--dest", default=".")
    p.add_argument("--css-dir", default="app", help="where house-style.css/.preset.js live (build.py --out)")
    p.add_argument("--app-dir", default="app", help="Next.js app directory for layout.tsx/loading.tsx")
    p.add_argument("--accent", default=tokens.DEFAULT_ACCENT)
    p.add_argument("--author", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--owner", default="<owner>")
    p.add_argument("--repo", default=None)
    a = p.parse_args()
    dest = Path(a.dest).resolve()
    cfg = dest / ".house-style.json"
    conf = json.loads(cfg.read_text()) if cfg.is_file() else {}
    a.name = a.name or conf.get("name") or dest.name
    a.repo = a.repo or dest.name
    a.author = a.author or git_user()
    a.accent = conf.get("accent", a.accent)
    o = stack(Out(dest), a)
    print("created: " + (", ".join(o.created) or "-"))
    print("skipped (already exist): " + (", ".join(o.skipped) or "-"))
    for n in o.notes:
        print("note: " + n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
