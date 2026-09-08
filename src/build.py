#!/usr/bin/env python3
"""
Builds ../index.html from data.json + logo.png.

Monthly update:
  1. Edit src/data.json (add the new month to "months", update "through",
     "window_label", "footer_note", and the last-year comparison figures).
  2. /usr/bin/python3 src/build.py
  3. git add -A && git commit -m "Scorecard: <month>" && git push
Vercel redeploys automatically on push.
"""
import base64, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

d = json.load(open(os.path.join(HERE, "data.json")))
logo = "data:image/png;base64," + base64.b64encode(
    open(os.path.join(HERE, "logo.png"), "rb").read()).decode()

months = d["months"]
# Only months we fully owned feed the headline totals. May (took over the 19th)
# and the current partial month are shown in the table but never counted.
counted = [m for m in months if m.get("counted")]
tot_spend = sum(m["spend"] for m in counted)
tot_sales = sum(m["sales"] for m in counted)
tot_book = sum(m["bookings"] for m in counted)
tot_roas = tot_sales / tot_spend
ly_spend, ly_sales = d["ly_spend"], d["ly_sales"]
ly_roas = ly_sales / ly_spend          # derived, so the tile can never contradict the figures beside it
ly_book = d["ly_bookings"]
growth_pct = (tot_sales - ly_sales) / ly_sales * 100

# ---------- YoY chart (months flagged chart:true) ----------
bars = [m for m in months if m.get("chart")]
mx = max(max(m["sales"], m["ly_sales"]) for m in bars)
W, H = 760, 260
pad_l, pad_b, pad_t = 54, 42, 16
plot_h = H - pad_b - pad_t
grp_w = (W - pad_l - 16) / len(bars)
bw = grp_w * 0.30
svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;display:block">']
for gi in range(4):
    y = pad_t + plot_h * gi / 3
    svg.append(f'<line x1="{pad_l}" y1="{y:.0f}" x2="{W-8}" y2="{y:.0f}" stroke="#243030" stroke-width="1"/>')
    svg.append(f'<text x="{pad_l-8}" y="{y+4:.0f}" text-anchor="end" font-family="Arial" '
               f'font-size="10" fill="#93A2A2">${mx*(1-gi/3)/1000:.0f}k</text>')
hit = []   # transparent hover targets, appended last so they sit on top
for i, m in enumerate(bars):
    cur, ly = m["sales"], m["ly_sales"]
    x0 = pad_l + grp_w * i + grp_w * 0.16
    h1, h2 = plot_h * ly / mx, plot_h * cur / mx
    svg.append(f'<rect x="{x0:.0f}" y="{pad_t+plot_h-h1:.0f}" width="{bw:.0f}" height="{h1:.0f}" '
               f'fill="#3A4A4A" rx="3" class="b b{i} ly"/>')
    svg.append(f'<rect x="{x0+bw+6:.0f}" y="{pad_t+plot_h-h2:.0f}" width="{bw:.0f}" height="{h2:.0f}" '
               f'fill="#00CED1" rx="3" class="b b{i} ty"/>')
    pct = (cur - ly) / ly * 100
    col = "#3FD08A" if pct >= 0 else "#C9A86A"
    # anchor the label above the TALLER bar so it never overlaps the other one
    label_y = pad_t + plot_h - max(h1, h2) - 7
    svg.append(f'<text x="{x0+bw+3:.0f}" y="{label_y:.0f}" text-anchor="middle" font-family="Arial" '
               f'font-size="11" font-weight="700" fill="{col}">{pct:+.0f}%</text>')
    svg.append(f'<text x="{x0+bw+3:.0f}" y="{H-16:.0f}" text-anchor="middle" font-family="Arial" '
               f'font-size="11" fill="#EAF2F2">{m["short"]}</text>')

    m_ly_roas = m["ly_sales"] / m["ly_spend"]
    tip = {
        "label": m["label"], "short": m["short"],
        "cur": {"sales": m["sales"], "spend": m["spend"], "bk": m["bookings"], "roas": f'{m["roas"]:.1f}'},
        "ly":  {"sales": m["ly_sales"], "spend": m["ly_spend"], "bk": m["ly_bookings"], "roas": f'{m_ly_roas:.1f}'},
        "pct": f'{pct:+.0f}%', "up": pct >= 0,
    }
    hit.append(f'<rect x="{pad_l+grp_w*i:.0f}" y="{pad_t:.0f}" width="{grp_w:.0f}" height="{plot_h:.0f}" '
               f'fill="transparent" class="hit" data-i="{i}" '
               f"data-tip='{json.dumps(tip)}'></rect>")
svg.append("".join(hit))
svg.append('</svg>')
chart = "".join(svg)

# ---------- scorecard table ----------
trs = ""
for m in months:
    if m.get("partial"):
        change = '<td class="num na">n/a, partial month</td>'
    else:
        pct = (m["sales"] - m["ly_sales"]) / m["ly_sales"] * 100
        change = f'<td class="num {"up" if pct >= 0 else "down"}">{pct:+.0f}%</td>'
    tag = f' <span class="tag">{m["tag"]}</span>' if m.get("tag") else ''
    trs += (f'<tr><td><b>{m["label"]}</b>{tag}</td><td class="num">${m["spend"]:,}</td>'
            f'<td class="num">{m["bookings"]}</td><td class="num">${m["sales"]:,}</td>'
            f'<td class="num">{m["roas"]}</td><td class="num">${m["ly_sales"]:,}</td>'
            + change + f'<td class="note">{m["note"]}</td></tr>')

season_cells = "".join(
    f'<div class="s"><div class="m">{n}</div><div class="v">${v:,}</div></div>'
    for n, v in d["season"]["cells"])

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{d['client'].split('&')[0].strip()} | Monthly Scorecard</title>
<style>
 :root{{--bg:#000;--panel:#101616;--panel2:#161E1E;--card:#131B1B;--ink:#EAF2F2;--muted:#93A2A2;--line:#243030;--accent:#00CED1;--accent2:#7FE3E4;--tint:#0E2626;--green:#3FD08A;--flat:#C9A86A;--sans:"Helvetica Neue",Arial,sans-serif}}
 *{{box-sizing:border-box}} html,body{{margin:0;padding:0}} body{{background:#000}}
 .wrap{{font-family:var(--sans);color:var(--ink);background:var(--bg);line-height:1.5;max-width:1060px;margin:0 auto}}
 .mast{{padding:28px 26px 24px;border-bottom:1px solid var(--line)}}
 .mast img{{height:34px;display:block;margin-bottom:18px}}
 .eyebrow{{color:var(--accent);font-size:11.5px;letter-spacing:2.5px;text-transform:uppercase;font-weight:700;margin-bottom:8px}}
 h1{{font-size:27px;margin:0 0 6px;font-weight:800;color:#fff;letter-spacing:-.3px}}
 .sub{{color:#AEBcBc;font-size:14.5px;margin:0}}
 .meta{{display:flex;flex-wrap:wrap;gap:8px 24px;margin-top:16px;font-size:12.5px;color:#7E8C8C}} .meta b{{color:#fff}}
 main{{padding:24px 26px 8px}}
 h2{{font-size:18px;font-weight:800;color:#fff;margin:30px 0 4px;padding-top:18px;border-top:1px solid var(--line)}} h2 .n{{color:var(--accent);margin-right:9px}}
 .lead{{color:var(--muted);font-size:13.5px;margin:0 0 14px}}
 .kpis{{display:flex;flex-wrap:wrap;gap:12px;margin:6px 0 2px}}
 .kpi{{flex:1 1 160px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
 .kpi .v{{font-size:23px;font-weight:800;color:var(--accent)}}
 .kpi .l{{font-size:11px;letter-spacing:.4px;color:#98A6A6;margin-top:3px;text-transform:uppercase}}
 .kpi .d{{font-size:11.5px;margin-top:6px;font-weight:700;color:var(--accent2)}}
 .card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 18px 10px;margin:14px 0;position:relative}}
 .b{{transition:opacity .12s ease}} .hit{{cursor:pointer}}
 .card.dim .b{{opacity:.32}} .card.dim .b.on{{opacity:1}}
 #tip{{position:absolute;z-index:5;pointer-events:none;opacity:0;transition:opacity .12s ease;background:#0B1717;border:1px solid #21585A;border-radius:9px;padding:11px 13px;min-width:186px;box-shadow:0 8px 24px rgba(0,0,0,.6)}}
 #tip.on{{opacity:1}}
 #tip .t{{font-size:12px;font-weight:800;color:var(--accent);margin-bottom:8px;white-space:nowrap}}
 #tip .r{{display:flex;justify-content:space-between;gap:16px;font-size:12px;padding:3px 0;white-space:nowrap}}
 #tip .r span:first-child{{color:var(--muted)}} #tip .r span:last-child{{color:#fff;font-weight:700;font-variant-numeric:tabular-nums}}
 #tip .hr{{height:1px;background:#21585A;margin:7px 0}}
 #tip .yr{{font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:#7E8C8C;margin:2px 0 3px}}
 #tip .d{{font-size:12px;font-weight:800;text-align:right;margin-top:7px}}
 #tip .d.up{{color:var(--green)}} #tip .d.dn{{color:var(--flat)}}
 .legend{{display:flex;gap:18px;font-size:12px;color:var(--muted);margin-top:6px}}
 .sw{{width:12px;height:12px;border-radius:3px;display:inline-block;vertical-align:-1px;margin-right:6px}}
 .tablewrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:14px 0;background:var(--panel)}}
 table{{border-collapse:collapse;width:100%;font-size:13px;min-width:820px}}
 th,td{{text-align:left;padding:10px 13px;white-space:normal;border-bottom:1px solid var(--line);vertical-align:top}}
 thead th{{background:var(--accent);color:#00201F;font-size:11px;letter-spacing:.4px;text-transform:uppercase;font-weight:800}}
 tbody tr:last-child td{{border-bottom:none}} tbody tr:nth-child(even){{background:var(--panel2)}}
 td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
 td.note{{color:var(--muted);font-size:12px;max-width:280px}}
 .na{{color:#7E8C8C;font-weight:600;font-size:11.5px;white-space:nowrap}}
 .up{{color:var(--green);font-weight:800}} .down{{color:var(--flat);font-weight:800}}
 .tag{{font-size:9.5px;background:#243030;color:#93A2A2;padding:2px 6px;border-radius:99px;letter-spacing:.5px;white-space:nowrap}}
 .callout{{background:var(--tint);border:1px solid #17494B;border-left:4px solid var(--accent);border-radius:10px;padding:16px 18px;margin:16px 0}}
 .callout h3{{margin:0 0 5px;font-size:14.5px;color:var(--accent)}} .callout p{{margin:0;color:#D3E4E4;font-size:13.5px}} .callout b{{color:#fff}}
 .note-panel{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:15px 17px;margin:14px 0}}
 .note-panel h3{{margin:0 0 6px;font-size:13px;font-weight:800;color:#fff;letter-spacing:.2px}}
 .note-panel p{{margin:0;color:#B9C7C7;font-size:13px;line-height:1.62}} .note-panel b{{color:#fff;font-weight:700}}
 .season{{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}}
 .s{{flex:1 1 150px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 15px}}
 .s .m{{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#98A6A6}} .s .v{{font-size:20px;font-weight:800;color:var(--accent);margin-top:2px}}
 footer{{padding:18px 26px 40px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;align-items:center;margin-top:20px}}
 footer img{{height:15px;vertical-align:middle}}
 @media(max-width:640px){{h1{{font-size:22px}}.mast,main,footer{{padding-left:16px;padding-right:16px}}}}
</style></head><body><div class="wrap">
<header class="mast">
 <img src="{logo}" alt="Dotoli Digital">
 <div class="eyebrow">Monthly Scorecard</div>
 <h1>{d['client']}</h1>
 <p class="sub">Meta performance since Dotoli Digital took over the account, measured against the same months last year.</p>
 <div class="meta"><span>Prepared for <b>{d['prepared_for']}</b></span><span>Account <b>{d['account']}</b></span><span>Took over <b>{d['takeover']}</b></span><span>Through <b>{d['through']}</b></span></div>
</header>
<main>

 <h2><span class="n">01</span>Since we took over</h2>
 <p class="lead">{d['window_label']}, compared with the same dates last year.</p>
 <div class="kpis">
  <div class="kpi"><div class="v">${tot_sales:,}</div><div class="l">Attributed sales (Meta)</div><div class="d">vs ${ly_sales:,} last year</div></div>
  <div class="kpi"><div class="v">${tot_spend:,}</div><div class="l">Ad spend</div><div class="d">vs ${ly_spend:,} last year</div></div>
  <div class="kpi"><div class="v">{tot_book:,}</div><div class="l">Bookings</div><div class="d">vs {ly_book:,} last year</div></div>
  <div class="kpi"><div class="v">{tot_roas:.1f}x</div><div class="l">Blended ROAS</div><div class="d">vs {ly_roas:.1f}x last year</div></div>
 </div>
 <div class="callout"><h3>{d['headline_title']}</h3><p>{d['headline']}</p></div>
 <div class="note-panel"><h3>{d['roas_title']}</h3><p>{d['roas_note']}</p></div>

 <h2><span class="n">02</span>This year vs last year, month by month</h2>
 <p class="lead">{d['chart_lead']}</p>
 <div class="card" id="chartcard">{chart}
  <div id="tip"></div>
  <div class="legend"><span><span class="sw" style="background:#3A4A4A"></span>Last year</span><span><span class="sw" style="background:#00CED1"></span>This year</span><span style="margin-left:auto;font-size:11px">Hover a column for detail</span></div>
 </div>

 <h2><span class="n">03</span>The scorecard</h2>
 <div class="tablewrap"><table>
  <thead><tr><th>Month</th><th class="num">Ad Spend</th><th class="num">Bookings</th><th class="num">Attributed Sales</th><th class="num">ROAS</th><th class="num">Same Month LY</th><th class="num">Change</th><th>What We Did</th></tr></thead>
  <tbody>{trs}</tbody>
 </table></div>
 <p class="lead">{d['partial_note']}</p>

 <h2><span class="n">04</span>The season ahead</h2>
 <p class="lead">{d['season']['lead']}</p>
 <div class="season">{season_cells}</div>
 <div class="callout"><h3>{d['season']['callout_title']}</h3><p>{d['season']['callout']}</p></div>

</main>
<footer><span><img src="{logo}" alt="Dotoli Digital">&nbsp;&nbsp;|&nbsp;&nbsp;dotolidigital.com</span><span>{d['footer_note']}</span></footer>
</div>
<script>
(function(){{
 var card=document.getElementById('chartcard'), tip=document.getElementById('tip');
 if(!card||!tip) return;
 var money=function(n){{return '$'+n.toLocaleString('en-US');}};
 function show(el,ev){{
  var t; try{{ t=JSON.parse(el.getAttribute('data-tip')); }}catch(e){{ return; }}
  tip.innerHTML='<div class="t">'+t.label+'</div>'
   +'<div class="yr">This year</div>'
   +'<div class="r"><span>Sales</span><span>'+money(t.cur.sales)+'</span></div>'
   +'<div class="r"><span>Spend</span><span>'+money(t.cur.spend)+'</span></div>'
   +'<div class="r"><span>Bookings</span><span>'+t.cur.bk+'</span></div>'
   +'<div class="r"><span>ROAS</span><span>'+t.cur.roas+'x</span></div>'
   +'<div class="hr"></div><div class="yr">Same dates last year</div>'
   +'<div class="r"><span>Sales</span><span>'+money(t.ly.sales)+'</span></div>'
   +'<div class="r"><span>Spend</span><span>'+money(t.ly.spend)+'</span></div>'
   +'<div class="r"><span>Bookings</span><span>'+t.ly.bk+'</span></div>'
   +'<div class="r"><span>ROAS</span><span>'+t.ly.roas+'x</span></div>'
   +'<div class="d '+(t.up?'up':'dn')+'">'+t.pct+' sales</div>';
  tip.classList.add('on'); card.classList.add('dim');
  var i=el.getAttribute('data-i');
  card.querySelectorAll('.b').forEach(function(b){{ b.classList.toggle('on', b.classList.contains('b'+i)); }});
  move(ev);
 }}
 function move(ev){{
  var r=card.getBoundingClientRect(), x=ev.clientX-r.left+14, y=ev.clientY-r.top+14;
  if(x+tip.offsetWidth > r.width-8) x=ev.clientX-r.left-tip.offsetWidth-14;
  if(y+tip.offsetHeight > r.height-8) y=r.height-tip.offsetHeight-8;
  if(x<8) x=8; if(y<8) y=8;
  tip.style.left=x+'px'; tip.style.top=y+'px';
 }}
 function hide(){{
  tip.classList.remove('on'); card.classList.remove('dim');
  card.querySelectorAll('.b').forEach(function(b){{ b.classList.remove('on'); }});
 }}
 card.querySelectorAll('.hit').forEach(function(el){{
  el.addEventListener('pointerenter', function(ev){{ show(el,ev); }});
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerleave', hide);
 }});
 card.addEventListener('pointerleave', hide);
}})();
</script>
</body></html>"""

assert "—" not in html, "em dash found in output"
out = os.path.join(ROOT, "index.html")
open(out, "w").write(html)
print(f"Built {out} ({os.path.getsize(out):,} bytes) from {len(months)} months")
