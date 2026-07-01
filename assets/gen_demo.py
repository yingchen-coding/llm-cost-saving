#!/usr/bin/env python3
"""Generate assets/demo.svg — a static terminal-cast hero showing the quota-failover story.

Pure stdlib, deterministic (no timestamps/random), so the SVG is reproducible. Regenerate with:
    python3 assets/gen_demo.py
"""
from __future__ import annotations

import html
from pathlib import Path

# (text, color-role) — roles map to a small GitHub-dark palette below
LINES = [
    ("$ broker run -t reasoning \"refactor the auth module\"", "cmd"),
    ("  → claude   ✗ usage limit reached, resets 4pm  — cooling down 5h", "err"),
    ("  → codex    ✓ done                              (auto-failover)", "ok"),
    ("", "blank"),
    ("$ broker run -t codegen \"add the missing tests\"", "cmd"),
    ("  → codex    ✓ done                              (codex is strongest here)", "ok"),
    ("", "blank"),
    ("$ broker status", "cmd"),
    ("  claude   cooling 4h58m   — every command skips it until the window resets", "dim"),
    ("  codex    available", "dim"),
    ("", "blank"),
    ("# … 4pm, claude's quota window resets …", "comment"),
    ("$ broker run -t reasoning \"finish the refactor\"", "cmd"),
    ("  → claude   ✓ done                              (auto-resumed, no manual switch)", "ok"),
]

PALETTE = {
    "cmd": "#e6edf3",
    "ok": "#3fb950",
    "err": "#f85149",
    "dim": "#8b949e",
    "comment": "#8b949e",
    "blank": "#e6edf3",
}

PAD_X, PAD_TOP, LINE_H, FONT = 22, 58, 22, 13.5
W = 760
H = PAD_TOP + LINE_H * len(LINES) + 20


def main() -> None:
    rows = []
    y = PAD_TOP
    for text, role in LINES:
        if text:
            rows.append(
                f'<text x="{PAD_X}" y="{y}" fill="{PALETTE[role]}" '
                f'xml:space="preserve">{html.escape(text)}</text>'
            )
        y += LINE_H

    dots = "".join(
        f'<circle cx="{18 + i * 20}" cy="20" r="6" fill="{c}"/>'
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f"))
    )

    label = "modelbroker terminal demo: quota failover and auto-resume"
    title_font = 'font-family="monospace" font-size="12" text-anchor="middle"'
    mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="{label}">',
        f'  <rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        f'  <rect width="{W}" height="40" rx="10" fill="#161b22"/>',
        f'  <rect y="30" width="{W}" height="10" fill="#161b22"/>',
        f"  {dots}",
        f'  <text x="{W // 2}" y="24" fill="#8b949e" {title_font}>'
        f"broker — quota-aware routing</text>",
        f'  <g font-family="{mono}" font-size="{FONT}">',
        f'    {"".join(rows)}',
        "  </g>",
        "</svg>",
        "",
    ]
    svg = "\n".join(parts)
    out = Path(__file__).resolve().parent / "demo.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg)} bytes, {len(LINES)} lines)")


if __name__ == "__main__":
    main()
