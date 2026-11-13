"""Run: python3 -m unittest discover -s tests -v   (stdlib only; icon test skips without network/ImageMagick)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "lib"))
import checks  # noqa: E402
import hygiene  # noqa: E402
import tokens  # noqa: E402


def rules(path, text):
    return {r for _, r, _ in checks.check(path, text)}


class Checks(unittest.TestCase):
    def test_flags(self):
        self.assertIn("color", rules("a.tsx", '<div className="x" style={{color: "#22c55e"}} />'))
        self.assertIn("color", rules("a.css", "a { color: rgb(1, 2, 3); }"))
        self.assertIn("emoji", rules("a.tsx", "<button>Save ✅</button>"))
        self.assertIn("lib", rules("a.tsx", 'import Button from "@mui/material/Button";'))
        self.assertIn("lib", rules("a.tsx", 'import { Home } from "react-icons/fa";'))
        self.assertIn("scrollbar", rules("a.css", "* { scrollbar-width: none; }"))
        self.assertIn("alt", rules("a.tsx", '<img src="/x.png" />'))
        self.assertIn("focus", rules("a.css", "button { outline: none; }"))
        self.assertIn("font", rules("layout.tsx", 'import { Inter } from "next/font/google";'))
        self.assertIn("fastmcp", rules("s.py", "from mcp.server.fastmcp import FastMCP"))
        self.assertIn("oauth", rules("s.py", '@mcp.custom_route("/.well-known/oauth-authorization-server")'))

    def test_clean(self):
        self.assertEqual(rules("a.tsx", '<img src="x" alt="" /><p className="bg-primary text-foreground">hi</p>'), set())
        self.assertEqual(rules("a.tsx", 'import { Home } from "lucide-react"; import { Geist } from "next/font/google";'), set())
        self.assertEqual(rules("a.css", "button:focus-visible { outline: 2px solid hsl(var(--ring)); }"), set())
        self.assertEqual(rules("s.py", "from fastmcp import FastMCP"), set())
        self.assertEqual(rules("a.tsx", "// issue #123 uses #fff in a comment"), set())
        self.assertEqual(rules("a.tsx", "const link = '#section';"), set())

    def test_exemptions(self):
        self.assertEqual(rules("tokens/colors.css", ":root{--a:#fff}"), set())
        self.assertEqual(rules("tailwind.config.ts", 'c: "#fff"'), set())
        self.assertEqual(rules("a.tsx", 'const c = "#fff"; // house-style: allow third-party brand color'), set())
        self.assertEqual(rules("README.md", "#fff 😀"), set())
        self.assertEqual(rules("post.mdx", "Great job 🎉 #fff"), set())

    def test_templates_are_compliant(self):
        for f in (ROOT / "templates").rglob("*"):
            if f.is_file() and f.suffix in (".tsx", ".py"):
                self.assertEqual(checks.check(f, f.read_text()), [], f)


class Tokens(unittest.TestCase):
    def test_all_accents_pass(self):
        self.assertEqual([m for a in tokens.ACCENTS for m in tokens.validate(a)], [])

    def test_validator_can_fail(self):
        orig = tokens.ACCENTS["green"]
        tokens.ACCENTS["green"] = ("#86efac", "#14532d")  # pale on white, dark on dark: both must fail
        try:
            self.assertTrue(tokens.validate("green"))
        finally:
            tokens.ACCENTS["green"] = orig

    def test_contrast_math(self):
        self.assertAlmostEqual(tokens.contrast((0, 0, 0), (1, 1, 1)), 21, places=1)

    def test_css_outputs(self):
        for tw in (3, 4):
            c = tokens.css("blue", tw)
            self.assertIn("--primary:", c)
            self.assertIn("prefers-reduced-motion", c)
            self.assertEqual("@theme inline" in c, tw == 4)
        self.assertIn("hsl(var(--primary))", tokens.preset())


class Hooks(unittest.TestCase):
    def run_hook(self, name, payload):
        return subprocess.run([sys.executable, str(ROOT / "hooks" / name)], input=json.dumps(payload), capture_output=True, text=True)

    def test_guard_opt_in_and_block(self):
        with tempfile.TemporaryDirectory() as d:
            f = str(Path(d) / "src" / "a.tsx")
            bad = {"tool_name": "Write", "tool_input": {"file_path": f, "content": '<div style={{color:"#fff"}}>🚀</div>'}, "cwd": d}
            self.assertEqual(self.run_hook("guard.py", bad).returncode, 0)  # not opted in
            (Path(d) / ".house-style.json").write_text("{}")
            r = self.run_hook("guard.py", bad)
            self.assertEqual(r.returncode, 2)
            self.assertIn("[color]", r.stderr)
            self.assertIn("[emoji]", r.stderr)
            ok = {**bad, "tool_input": {"file_path": f, "content": "<div className='text-foreground' />"}}
            self.assertEqual(self.run_hook("guard.py", ok).returncode, 0)
            multi = {"tool_name": "MultiEdit", "tool_input": {"file_path": f, "edits": [{"new_string": "x"}, {"new_string": "color: #abc123"}]}, "cwd": d}
            f2 = str(Path(d) / "b.css")
            multi["tool_input"]["file_path"] = f2
            self.assertEqual(self.run_hook("guard.py", multi).returncode, 2)

    def test_guard_survives_garbage(self):
        r = subprocess.run([sys.executable, str(ROOT / "hooks" / "guard.py")], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)

    def test_session_and_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.run_hook("session_start.py", {"cwd": d}).stdout, "")  # unrelated dir: silent
            (Path(d) / "package.json").write_text('{"dependencies":{"next":"15"}}')
            self.assertIn("/house-style:init", self.run_hook("session_start.py", {"cwd": d}).stdout)
            (Path(d) / ".house-style.json").write_text('{"name":"Demo","accent":"teal","icon":"rocket"}')
            out = json.loads(self.run_hook("session_start.py", {"cwd": d}).stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("accent=teal", out)
            self.assertIn(str(ROOT), out)
            p = json.loads(self.run_hook("prompt_submit.py", {"cwd": d, "prompt": "add a loading spinner to the login page"}).stdout)
            self.assertIn("loading.md", p["hookSpecificOutput"]["additionalContext"])
            for prompt, rule in (("cut a new release and bump the version", "releasing.md"), ("rewrite the README", "docs.md")):
                out = json.loads(self.run_hook("prompt_submit.py", {"cwd": d, "prompt": prompt}).stdout)
                self.assertIn(rule, out["hookSpecificOutput"]["additionalContext"])
            self.assertEqual(self.run_hook("prompt_submit.py", {"cwd": d, "prompt": "rename a variable"}).stdout, "")


def git(cwd, *a):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


class Release(unittest.TestCase):
    def repo(self, d, version="0.2.0"):
        git(d, "init", "-q", "-b", "main")
        (Path(d) / "pyproject.toml").write_text(f'[project]\nname = "x"\nversion = "{version}"\n')
        pkg = Path(d) / "x"
        pkg.mkdir()
        (pkg / "__init__.py").write_text(f'__version__ = "{version}"\n')
        git(d, "add", "-A")
        git(d, "commit", "-qm", "feat: initial import")
        git(d, "tag", f"v{version}")

    def commit(self, d, msg):
        (Path(d) / "f.txt").write_text(msg)
        git(d, "add", "-A")
        git(d, "commit", "-qm", msg)

    def run_rel(self, d, *args):
        ident = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}  # CI runners have no git identity
        env = {**os.environ, **ident}
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "release.py"), "--cwd", d, *args], capture_output=True, text=True, env=env)

    def test_dry_run_and_apply_0x(self):
        with tempfile.TemporaryDirectory() as d:
            self.repo(d)
            self.commit(d, "feat(api): add search (#7)")
            self.commit(d, "fix: null title (#8)")
            self.commit(d, "docs: typo")
            r = self.run_rel(d)
            self.assertIn("v0.2.1", r.stdout)  # 0.x: feat + fix -> patch
            self.assertIn("- add search (#7)", r.stdout)
            self.assertNotIn("typo", r.stdout)
            self.assertIn("0.2.0", (Path(d) / "pyproject.toml").read_text())  # dry run changed nothing
            self.commit(d, "feat!: drop v1 endpoints (#9)")
            r = self.run_rel(d, "--apply")
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertIn("v0.3.0", r.stdout)  # 0.x: breaking -> minor
            self.assertIn('version = "0.3.0"', (Path(d) / "pyproject.toml").read_text())
            self.assertIn('__version__ = "0.3.0"', (Path(d) / "x" / "__init__.py").read_text())
            cl = (Path(d) / "CHANGELOG.md").read_text()
            self.assertIn("## [0.3.0]", cl)
            self.assertIn("### Breaking changes", cl)
            self.assertEqual(git(d, "rev-parse", "--abbrev-ref", "HEAD"), "release/v0.3.0")
            self.assertEqual(git(d, "log", "-1", "--format=%s"), "release: v0.3.0")
            self.assertEqual(git(d, "tag", "--list"), "v0.2.0")  # never tags

    def test_1x_rules_and_nothing_to_release(self):
        with tempfile.TemporaryDirectory() as d:
            self.repo(d, "1.4.2")
            self.assertNotEqual(self.run_rel(d).returncode, 0)  # no commits since tag
            self.commit(d, "chore: bump ci")
            self.assertNotEqual(self.run_rel(d).returncode, 0)  # only chore
            self.commit(d, "feat: new thing")
            self.assertIn("v1.5.0", self.run_rel(d).stdout)
            self.commit(d, "fix: x\n\nBREAKING CHANGE: flag renamed")
            r = self.run_rel(d)
            self.assertIn("v2.0.0", r.stdout)
            self.assertIn("Migration: flag renamed", r.stdout)

    def test_refuses_dirty_and_disagreeing_versions(self):
        with tempfile.TemporaryDirectory() as d:
            self.repo(d)
            self.commit(d, "fix: a")
            (Path(d) / "dirty.txt").write_text("x")
            self.assertNotEqual(self.run_rel(d, "--apply").returncode, 0)
            (Path(d) / "x" / "__init__.py").write_text('__version__ = "9.9.9"\n')
            self.assertIn("disagree", self.run_rel(d).stderr)


class Hygiene(unittest.TestCase):
    def test_findings_and_clean(self):
        with tempfile.TemporaryDirectory() as d:
            msgs = " ".join(hygiene.check_repo(d))
            for k in ("README.md missing", "AGENTS.md missing", "LICENSE missing"):
                self.assertIn(k, msgs)
            for rel in ("templates/README.md", "templates/AGENTS.md"):
                (Path(d) / Path(rel).name).write_text((ROOT / rel).read_text())
            (Path(d) / "LICENSE").write_text("MIT")
            (Path(d) / "CLAUDE.md").write_text("@AGENTS.md\n")
            self.assertEqual(hygiene.check_repo(d), [])
            (Path(d) / "CLAUDE.md").write_text("lots of stuff")
            git(d, "init", "-q")
            git(d, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "x")
            git(d, "tag", "0.1.0")
            m = " ".join(hygiene.check_repo(d))
            self.assertIn("CLAUDE.md should contain only", m)
            self.assertIn("not in vX.Y.Z form", m)
            self.assertIn("CHANGELOG.md missing", m)



class Scaffold(unittest.TestCase):
    def run_sc(self, d, *args):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), *args, "--dest", d], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_nextjs_creates_config_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_sc(d, "nextjs")
            for f in ("components/skeleton.tsx", "components/states.tsx", "app/loading.tsx", "app/layout.tsx", "tailwind.config.ts"):
                self.assertTrue((Path(d) / f).is_file(), f)
            self.assertIn("house-style.preset.js", (Path(d) / "tailwind.config.ts").read_text())
            self.assertIn('./house-style.css', (Path(d) / "app/layout.tsx").read_text())
            (Path(d) / "components/skeleton.tsx").write_text("mine")
            out = self.run_sc(d, "nextjs")
            self.assertEqual((Path(d) / "components/skeleton.tsx").read_text(), "mine")  # never overwrites
            self.assertIn("components/skeleton.tsx", out.split("skipped")[1])

    def test_existing_tailwind_config_is_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tailwind.config.js").write_text("module.exports = {}")
            out = self.run_sc(d, "nextjs")
            self.assertFalse((Path(d) / "tailwind.config.ts").exists())
            self.assertEqual((Path(d) / "tailwind.config.js").read_text(), "module.exports = {}")
            self.assertIn("add `presets:", out)

    def test_existing_layout_gets_a_note(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "app").mkdir()
            (Path(d) / "app/layout.tsx").write_text('import "./globals.css";')
            out = self.run_sc(d, "nextjs")
            self.assertIn("layout.tsx exists: replace", out)
            self.assertEqual((Path(d) / "app/layout.tsx").read_text(), 'import "./globals.css";')

    def test_tailwind4_gets_no_config(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text('{"devDependencies":{"tailwindcss":"^4.1.0"}}')
            out = self.run_sc(d, "nextjs")
            self.assertFalse((Path(d) / "tailwind.config.ts").exists())
            self.assertIn("Tailwind 4", out)
        self.assertTrue(tokens.css("green", 4).lstrip().splitlines()[1].startswith('@import "tailwindcss"'))

    def test_expo_and_mkdocs_and_api(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".house-style.json").write_text(json.dumps({"name": "Demo", "accent": "violet"}))
            (Path(d) / "brand").mkdir()
            (Path(d) / "brand/icon.svg").write_text("<svg/>")
            self.run_sc(d, "expo")
            self.assertIn("nativewind/preset", (Path(d) / "tailwind.config.js").read_text())
            self.run_sc(d, "mkdocs")
            y = (Path(d) / "mkdocs.yml").read_text()
            self.assertIn("deep purple", y)
            self.assertIn("Demo", y)
            self.assertTrue((Path(d) / "docs/assets/icon.svg").is_file())
            self.assertTrue((Path(d) / ".github/workflows/docs.yml").is_file())
            self.run_sc(d, "fastmcp")
            self.assertTrue((Path(d) / "server.py").is_file())

    def test_docs_fill_placeholders_and_pass_hygiene(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_sc(d, "docs", "--name", "Demo", "--owner", "me", "--repo", "demo", "--author", "Me")
            readme = (Path(d) / "README.md").read_text()
            self.assertIn("github.com/me/demo", readme)
            self.assertNotIn("<Name>", readme)
            self.assertNotIn("badge/docs", readme)  # no mkdocs -> no docs badge/section
            self.assertNotIn("## Documentation", readme)
            self.assertNotIn("brand/icon.svg", readme)  # no icon yet
            self.assertIn("Me", (Path(d) / "LICENSE").read_text())
            self.assertEqual((Path(d) / "CLAUDE.md").read_text().strip(), "@AGENTS.md")
            self.assertEqual(hygiene.check_repo(d), [])
            (Path(d) / "CLAUDE.md").write_text("old stuff")
            self.assertIn("move it into AGENTS.md", self.run_sc(d, "docs"))
            self.assertEqual((Path(d) / "CLAUDE.md").read_text(), "old stuff")


class Brand(unittest.TestCase):
    @unittest.skipUnless(shutil.which("convert") or shutil.which("magick"), "ImageMagick missing")
    def test_icon_set(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "brand.py"), "--name", "T", "--icon", "rocket", "--accent", "violet"], cwd=d, capture_output=True, text=True)
            if "could not fetch" in (r.stderr + r.stdout):
                self.skipTest("no network for lucide")
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("icon.svg", "icon-1024.png", "apple-icon.png", "favicon.ico", "adaptive-foreground.png"):
                self.assertGreater((Path(d) / "brand" / f).stat().st_size, 100, f)
            self.assertEqual(json.loads((Path(d) / ".house-style.json").read_text())["accent"], "violet")


if __name__ == "__main__":
    unittest.main()
