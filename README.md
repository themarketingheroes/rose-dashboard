# ROSE Therapeutic Farm, Monthly Scorecard

Client-facing Meta performance dashboard for ROSE Therapeutic Farm / Goat Yoga Katy
(Meta account 51962666). Built by Dotoli Digital.

Live: deployed on Vercel, redeploys automatically on every push to `main`.

## Monthly update, three steps

1. **Edit the data.** Everything the page shows lives in `src/data.json`. Add the new
   month to `months`, update `through`, `window_label`, the `ly_*` comparison figures,
   and `footer_note`.

2. **Rebuild.**
   ```
   /usr/bin/python3 src/build.py
   ```
   This regenerates `index.html` from the data plus the logo. It fails loudly if an
   em dash sneaks into the output.

3. **Ship.**
   ```
   git add -A && git commit -m "Scorecard: September 2026" && git push
   ```
   Vercel picks it up and redeploys within about a minute.

## How the months work

Each entry in `months` has three flags that control where it appears:

| Flag | Effect |
|---|---|
| `counted` | Included in the KPI totals at the top. Only use for complete months we fully owned. |
| `chart` | Drawn as a bar in the year-over-year chart. |
| `partial` / `tag` | Shows a small grey pill next to the month name, e.g. "partial". |

We took the account over on **May 19, 2026**, so May is not `counted`: it contains 18
days that were not ours. The current in-flight month is not `counted` either, since it
would be compared against a full month last year. Both still appear in the scorecard
table for completeness, with the reason stated in the notes column.

## Where the numbers come from

Meta Ads Manager, **Campaigns** export (not the Ads export), broken down by month.
When aggregating, skip the account-total rows, the ones whose reporting period spans
the entire account history rather than a single month. Those rows duplicate the totals
and will roughly double every figure if left in.

## Layout

```
index.html        generated, this is what Vercel serves. Do not hand-edit.
src/data.json     every number and every line of copy on the page
src/build.py      the generator
src/logo.png      Dotoli Digital turquoise logo, inlined as base64 at build time
```

`index.html` is fully self-contained: no external CSS, JS, fonts, or images, so it
renders identically anywhere and cannot break from a third-party outage.
