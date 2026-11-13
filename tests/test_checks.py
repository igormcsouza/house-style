import checks
import pytest


def rules(path, text):
    return {r for _, r, _ in checks.check(path, text)}


@pytest.mark.parametrize(
    ("path", "text", "rule"),
    [
        ("a.tsx", '<div style={{color: "#22c55e"}} />', "color"),
        ("a.css", "a { color: rgb(1, 2, 3); }", "color"),
        ("a.tsx", "<button>Save ✅</button>", "emoji"),
        ("a.tsx", 'import Button from "@mui/material/Button";', "lib"),
        ("a.tsx", 'import { Home } from "react-icons/fa";', "lib"),
        ("a.css", "* { scrollbar-width: none; }", "scrollbar"),
        ("a.tsx", '<img src="/x.png" />', "alt"),
        ("a.css", "button { outline: none; }", "focus"),
        ("layout.tsx", 'import { Inter } from "next/font/google";', "font"),
        ("s.py", "from mcp.server.fastmcp import FastMCP", "fastmcp"),
        ("s.py", '@mcp.custom_route("/.well-known/oauth-authorization-server")', "oauth"),
        ("s.py", 'app.add_middleware(CORSMiddleware, allow_origins=["*"])', "cors"),
        ("s.py", "app = FastAPI(debug=True)", "debug"),
        ("s.py", "httpx.get(url, verify=False)", "tls"),
        ("s.py", "subprocess.run(cmd, shell=True)", "shell"),
        ("s.py", "eval(user_input)", "eval"),
        ("s.py", "jwt.decode(t, options={'verify_signature': False})", "jwt"),
        ("s.py", "obj = pickle.loads(blob)", "deserialize"),
        ("s.py", "cfg = yaml.load(text)", "deserialize"),
        ("s.py", 'cur.execute(f"select * from t where id={i}")', "sql"),
        ("s.py", 'API_TOKEN = "sk_live_abcdef123456"', "secret"),
        ("tests/test_x.py", "import unittest", "unittest"),
        ("tests/test_x.py", "class T(unittest.TestCase): pass", "unittest"),  # house-style: allow fixture
        ("tests/test_x.py", "from unittest import skip", "unittest"),
    ],
)
def test_violations_are_flagged(path, text, rule):
    assert rule in rules(path, text)


@pytest.mark.parametrize(
    ("path", "text"),
    [
        ("a.tsx", '<img src="x" alt="" /><p className="bg-primary text-foreground">hi</p>'),
        ("a.tsx", 'import { Home } from "lucide-react"; import { Geist } from "next/font/google";'),
        ("a.css", "button:focus-visible { outline: 2px solid hsl(var(--ring)); }"),
        ("s.py", "from fastmcp import FastMCP"),
        ("a.tsx", "// issue #123 uses #fff in a comment"),
        ("a.tsx", "const link = '#section';"),
        ("tokens/colors.css", ":root{--a:#fff}"),
        ("tailwind.config.ts", 'c: "#fff"'),
        ("a.tsx", 'const c = "#fff"; // house-style: allow third-party brand color'),
        ("README.md", "#fff 😀"),
        ("post.mdx", "Great job 🎉 #fff"),
        ("s.py", 'TOKEN_TABLE = "push-tokens"'),
        ("s.py", 'DEV_PASSWORD = "password"'),
        ("s.py", 'API_KEY = os.environ["API_KEY"]'),
        ("s.py", "# eval(x) in a comment"),
        ("tests/test_x.py", "from unittest import mock\nimport unittest.mock"),
        ("tests/test_x.py", 'eval("1")'),
    ],
)
def test_compliant_or_exempt(path, text):
    assert rules(path, text) == set()


def test_font_import_allows_geist_only():
    assert rules("l.tsx", 'import { Geist, Geist_Mono } from "next/font/google";') == set()
    found = checks.check("l.tsx", 'import { Geist, Roboto as R } from "next/font/google";')
    assert found
    assert "Roboto" in found[0][2]


def test_focus_ok_when_ring_present():
    assert rules("a.tsx", 'className="outline-none focus-visible:ring-2"') == set()


def test_python_allow_marker_suppresses_a_line():
    assert rules("s.py", "subprocess.run(cmd, shell=True)  # house-style: allow trusted constant") == set()


def test_alt_check_respects_allow_marker():
    assert rules("a.tsx", '<img src="x" /> {/* house-style: allow decorative */}') == set()


def test_non_ui_extension_is_ignored():
    assert checks.check("notes.txt", "#fff 🚀") == []


def test_format_violations_truncates():
    found = [(i, "color", "m") for i in range(1, 11)]
    text = checks.format_violations("a.tsx", found, limit=3)
    assert "10 violation(s) in a.tsx" in text
    assert "...and 7 more" in text
    assert "house-style: allow" in text
    assert "more" not in checks.format_violations("a.tsx", found[:2])
