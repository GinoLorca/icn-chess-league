# ICN Chess League

The season standings, player rankings, and points ladder for Impact Coaching
Network's chess league. A single self-contained page — no build step, no
backend, no dependencies beyond two Google Fonts stylesheets.

Live on GitHub Pages at **https://ginolorca.github.io/icn-chess-league/**,
embedded on impactcoachingnetwork.org via an iframe (see below).

## Updating the league

Everything content-related lives in `index.html`, inside the `<script>`
block, and is commented in place:

- **`LEAGUE_DATA`** — each school's cumulative season score, by region
  (Overall / Manhattan / Brooklyn) and competitive section (K–1, Primary,
  Elementary). This is what changes after every Matchday.
- **`ALL_PLAYERS`** — the flat list every player ranking is derived from.
- **`SCHOOL_COLORS`** — each school's two team colors.
- **`SCHOOL_LOGOS`** — maps a school name to its crest file in `logos/`.

To add a school's crest: drop an SVG into `logos/`, then add a line to
`SCHOOL_LOGOS` pointing at it (`"School Name": "logos/school-name.svg"`).
Any aspect ratio works — it's displayed in a fixed square box that centers
and scales the art automatically.

**To publish an update:** commit and push to `main`. GitHub Pages redeploys
automatically, usually live within a minute — nothing else to touch, and
the Squarespace page never needs to be re-edited.

## Local preview

No build step — just serve the folder and open it:

```
python3 -m http.server 8000
# then open http://localhost:8000/
```

(Opening `index.html` directly via `file://` also mostly works, but a local
server avoids some browsers' quirks with `fetch`/font loading.)

## One-time setup: enabling GitHub Pages

If Pages isn't already enabled on this repo:

1. Go to **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Set **Branch** to `main` and the folder to `/ (root)`, then **Save**.
4. GitHub will publish it at `https://ginolorca.github.io/icn-chess-league/`
   within a couple of minutes.

## Embedding on Squarespace

In the Squarespace page editor, add a **Code Block** where the league page
should appear, and paste:

```html
<iframe
  src="https://ginolorca.github.io/icn-chess-league/"
  style="width:100%; min-height:1600px; border:0;"
  loading="lazy">
</iframe>
```

Adjust `min-height` to taste — the page's content height varies by which
view (Team Standings vs. Player Rankings) and how many schools/players are
showing. There's no way for an iframe to auto-fit its parent's height
across domains, so a generous fixed height (with the iframe's own internal
scrolling handling the rest) is the simplest reliable approach.
