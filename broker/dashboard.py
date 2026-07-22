"""Render a self-contained HTML dashboard from the broker trace (and optionally usage transcripts).

Zero-dependency: one static HTML file with inline CSS and inline SVG bars — no JS libraries, no
server, no external requests. It reuses the same analyses as the CLI (cost radar, quota pressure,
usage), so the dashboard and the terminal commands never disagree.
"""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from .config import Config
from .cost import cost_radar
from .quota import quota_report
from .trace import summarize
from .usage import UsageReport, analyze

_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: #0d1117; color: #e6edf3;
  font: 14px/1.5 ui-sans-serif, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
.wrap { max-width: 960px; margin: 0 auto; padding: 28px 20px 48px; }
h1 { font-size: 20px; margin: 0 0 2px; }
.sub { color: #8b949e; font-size: 12px; margin: 0 0 22px; }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .8px; color: #8b949e;
  border-bottom: 1px solid #30363d; padding-bottom: 6px; margin: 26px 0 12px; }
.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; }
.card .k { color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: .5px; }
.card .v { font-size: 22px; font-weight: 700; margin-top: 4px; }
.warn .v { color: #f85149; }
.ok .v { color: #3fb950; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #21262d; }
th { color: #8b949e; font-weight: 600; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
.bar { height: 16px; background: #21262d; border-radius: 3px; overflow: hidden; }
.bar > span { display: block; height: 100%; background: #388bfd; }
.tag { font-size: 11px; padding: 1px 6px; border-radius: 10px; }
.tag.waste { background: #3d1418; color: #f85149; }
.tag.trade { background: #33291a; color: #d29922; }
.empty { color: #8b949e; font-style: italic; }
"""


def _bar(value: float, total: float) -> str:
    pct = (value / total * 100) if total > 0 else 0
    return f'<div class="bar"><span style="width:{pct:.1f}%"></span></div>'


def _card(key: str, value: str, cls: str = "") -> str:
    return f'<div class="card {cls}"><div class="k">{html.escape(key)}</div>' \
           f'<div class="v">{html.escape(value)}</div></div>'


def render_html(config: Config, trace_path: str | Path, usage: UsageReport | None = None) -> str:
    summary = summarize(trace_path)
    radar = cost_radar(config, summary)
    quota = quota_report(trace_path)
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    cards = [
        _card("runs", f"{summary.runs:,}"),
        _card("est. spend", f"${radar.total_estimated_cost_usd:,.4f}"),
        _card("failovers", f"{summary.failovers:,}"),
        _card("mechanical waste", f"${radar.mechanical_waste_usd:,.4f}",
              "warn" if radar.mechanical_waste_usd > 0 else "ok"),
    ]

    total_prov = sum(radar.cost_by_provider.values()) or 0.0
    prov_rows = "".join(
        f"<tr><td>{html.escape(p)}</td><td class='n'>${c:,.4f}</td>"
        f"<td style='width:45%'>{_bar(c, total_prov)}</td></tr>"
        for p, c in sorted(radar.cost_by_provider.items(), key=lambda kv: -kv[1])
    ) or "<tr><td colspan='3' class='empty'>no cost recorded yet</td></tr>"

    overpay_rows = "".join(
        f"<tr><td>{html.escape(o.task)}</td><td class='n'>{o.runs}</td>"
        f"<td class='n'>${o.actual_cost_usd:,.4f}</td><td class='n'>${o.overpay_usd:,.4f}</td>"
        f"<td><span class='tag {'waste' if o.mechanical else 'trade'}'>"
        f"{'mechanical waste' if o.mechanical else 'quality tradeoff'}</span></td></tr>"
        for o in radar.overpay_by_task
    ) or "<tr><td colspan='5' class='empty'>no overpay detected</td></tr>"

    quota_rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td class='n'>{row.attempts}</td>"
        f"<td class='n'>{row.quota_hit_rate:.0%}</td><td class='n'>{row.failure_pressure:.0%}</td></tr>"
        for name, row in sorted(quota.providers.items())
    ) or "<tr><td colspan='4' class='empty'>no quota data yet</td></tr>"

    usage_section = ""
    if usage is not None:
        tier_rows = "".join(
            f"<tr><td>{html.escape(t)}</td><td class='n'>${usage.cost_by_tier[t]:,.2f}</td>"
            f"<td class='n'>{usage.tokens_by_tier.get(t, 0) / 1e6:,.1f}M</td></tr>"
            for t in ("fable", "opus", "sonnet", "haiku") if usage.cost_by_tier.get(t)
        )
        usage_section = f"""
    <h2>Usage (transcripts)</h2>
    <div class="cards">
      {_card("total spend", f"${usage.total_cost:,.2f}")}
      {_card("mechanical waste", f"${usage.recoverable:,.2f}", "warn" if usage.recoverable > 0 else "ok")}
      {_card("after rerouting", f"${usage.cost_after:,.2f}", "ok")}
      {_card("turns analyzed", f"{usage.turns:,}")}
    </div>
    <table style="margin-top:12px"><tr><th>tier</th><th class="n">cost</th><th class="n">tokens</th></tr>
    {tier_rows}</table>"""

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>modelbroker dashboard</title><style>{_CSS}</style></head>
<body><div class="wrap">
  <h1>modelbroker dashboard</h1>
  <p class="sub">generated {stamp} · trace: {html.escape(str(trace_path))}</p>
  <div class="cards">{"".join(cards)}</div>

  <h2>Spend by provider</h2>
  <table><tr><th>provider</th><th class="n">cost</th><th>share</th></tr>{prov_rows}</table>

  <h2>Overpay by task</h2>
  <table><tr><th>task</th><th class="n">runs</th><th class="n">spent</th><th class="n">overpaid</th>
    <th>kind</th></tr>{overpay_rows}</table>

  <h2>Quota pressure</h2>
  <table><tr><th>provider</th><th class="n">attempts</th><th class="n">quota-hit</th>
    <th class="n">failure pressure</th></tr>{quota_rows}</table>
  {usage_section}
</div></body></html>
"""


def write_dashboard(config: Config, trace_path: str | Path, output: str | Path,
                    usage_paths: list[str] | None = None) -> Path:
    usage = analyze(usage_paths) if usage_paths else None
    out = Path(output)
    out.write_text(render_html(config, trace_path, usage), encoding="utf-8")
    return out
