# kryptic.sh

GitHub Pages repo for [kryptic.sh](https://kryptic.sh) — the unified site for
every kryptic-sh project. Each app lives at `kryptic.sh/<app>/` (no per-app
subdomains).

## Layout

- `templates/layout.html` — shared page shell (head meta, siblings bar, nav,
  footer).
- `content/<page>.html` — one file per page: JSON front-matter in a
  `<!--meta ... meta-->` comment, per-page CSS in `<!--head-->`, page body in
  `<!--body-->`. `content/index.html` is the homepage.
- `assets/css/base.css` — shared design system (accent slots overridden per
  page).
- `assets/js/site.js` — deferred GA loader + live version badges. Any element
  with `data-version="<repo>"` gets the latest release tag from the GitHub API
  at page load (sessionStorage-cached, 1 h).
- `public/` — static files copied verbatim to the site root (CNAME, robots,
  sitemap, favicons; `public/<app>/` holds per-app icons + og images).
- `build.py` — stdlib-only assembler: `python3 build.py` → `dist/`.

## Develop

```sh
python3 build.py
python3 -m http.server -d dist 8000
```

Deploys via `.github/workflows/pages.yml` on push to main. Versions are fetched
client-side, so releases show up without a rebuild.
