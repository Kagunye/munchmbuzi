# Mbuzi Munch website (Django)

A rebuild of [mbuzimunch.com](https://www.mbuzimunch.com/) in Django, keeping the brand's signature red (`#FF2626`), black and white, the goat logo, and all of the original copy, photos and the printed menu. Social images and reels come from [@mbuzi_munch](https://www.instagram.com/mbuzi_munch/).

## What's included

| Page | URL | Notes |
|---|---|---|
| The Mbuzi Munch Experience | `/experience/` | Six chapters: the pasture, the secret blend (tap the spice jars), the fire (pick rare/medium/well done, with embers), build your plate (real menu prices printed on a vintage receipt, then "Book this feast" pre-fills the booking), bottle to glass (recycling slider), good times |
| Home | `/` | Photo hero, branch strip, story, signature dishes, drinks, reviews, Instagram reels, delivery partners, events banner, inline booking form, news, Instagram grid |
| Menu | `/menu/` | Full printed menu (211 items) with tabs (Food, Breakfast, Soft drinks, Bar) and live search. PDF download kept |
| Branches | `/branches/` | Golf Park, Galleria, Buffalo Mall, Delamere: hours, phone, email, Google map, directions |
| Book a table | `/book/` | Saves to the database, emails the branch, shows a confirmation page |
| Events | `/events/` | The Sundowner Bar (no venue charge for 20+), MM Catering, event reels |
| Our story | `/our-story/` | Free range, recycled glassware, Buy Local Buy Kenyan |
| Careers | `/careers/` | Openings + application form with CV upload |
| News | `/news/` | The Naivasha opening and QR/M-Pesa articles |

Old Wix links (`/contact-1`, `/copy-of-contact`, `/copy-of-mbuzi-munch-the-finest-nyama`) redirect permanently to the new pages. There's also `sitemap.xml`, `robots.txt`, Open Graph tags and schema.org Restaurant data.

Everything content-related is editable in **Django admin** (`/admin/`): branches, menu categories and items, signature dishes, reviews, news, job openings. Bookings and job applications also land there.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_site       # loads branches, menu, dishes, reviews, news, jobs
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/admin/.

`seed_site` is safe to run again (it only adds what's missing). `seed_site --reset` wipes and reloads the content tables, but never bookings or applications.

Run tests with `python manage.py test core`.

## Deploy on Vercel

The repo is ready for Vercel (`vercel.json` + `build_files.sh`).

1. **Import the repo** in Vercel (New Project → Import `Kagunye/munchmbuzi`). Leave the framework preset as "Other"; `vercel.json` handles the build.
2. **Add a database:** Project → Storage → create a **Postgres** database (Neon) and connect it. This sets `DATABASE_URL`. It's required: Vercel's file system is read-only, so SQLite can't save bookings or job applications.
3. **Set environment variables** (Settings → Environment Variables), see `.env.example`: at least `DJANGO_SECRET_KEY` (a long random string), plus your domain in `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` and SMTP settings for booking emails.
4. **Deploy.** The build installs requirements, runs `migrate` and `seed_site` (adds content only if missing), collects static files and publishes `static/` and `media/` on Vercel's CDN.
5. **Create an admin login** once, from your computer against the production database:
   ```bash
   DATABASE_URL="postgres://…" python manage.py createsuperuser
   ```

**Limits on Vercel:** files uploaded through admin (new photos, CVs, music) are not kept, because the server's disk is temporary. Content that ships with the repo (`static/`, `media/`) works fine. For editable uploads, connect object storage such as Vercel Blob or S3 (`django-storages`). Uploaded CVs are never published (`media/applications/` is git-ignored and removed from the build).

## Other hosts

Set the variables from `.env.example`, then:

```bash
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_site
gunicorn config.wsgi        # or your host's WSGI server
```

Static files are served by WhiteNoise. Uploaded media (`/media/`) needs to be served by your web server or object storage. With `DJANGO_DEBUG=False`, set a real SMTP backend so booking emails reach each branch inbox (`golfpark@`, `galleria@`, `buffalo@`, `delamere@`).

## Project layout

```
config/            settings, urls
core/              models, admin, views, forms, seed command, tests
templates/         base.html, partials/, core/ pages
static/css/site.css   brand styles (tokens at the top)
static/js/site.js     nav, hero slider, reels player, menu search
static/img/        site photos (from mbuzimunch.com), social/ (Instagram), reels/ (video posters)
static/video/      hero grill clip + Instagram reels (re-encoded H.264, faststart)
static/docs/       printed menu PDF
```

## Look & feel

**Clean by default, vintage on request.** The site loads in a clean look: natural-colour food photos and videos, crisp headings, solid red/black/cream sections. A **Vintage mode** switch in the top bar (and "See it in vintage" on the Experience page) turns on the full vintage "white dirt" look: faded film colour, light leaks, grain, dust, scratches, projector flicker on videos, worn-stamp headings and white-dirt wear on the red and black sections. The choice is remembered per visitor (`localStorage`). In CSS, everything vintage-only is switched off under `html:not(.vintage)` at the end of `static/css/site.css`.

The layout is the same in both modes: torn paper edges, and photos shown as taped polaroids, postage stamps, film frames and newspaper clippings. Fonts are the same as the old site: **Courier New** (body) and **Cinzel** (headings).

Textures are small PNG tiles in `static/img/texture/`, generated by `python tools/make_textures.py`. Change the percentages in that script to make the wear heavier or lighter, or the `opacity` values in `static/css/site.css`. They're PNGs rather than SVG filters because browsers paint them far more cheaply, which matters on phones.

**Section artworks:** four artworks supplied by the client, in `static/img/art/`:

| Artwork | Where it's used |
|---|---|
| `the-feast.jpg`: painting of a community feast at a long table | Home ("Welcome to the table"), Events |
| `bass-player.jpg`: painting of a bass player | Events |
| `kitenge-tailor.jpg`: photo of a tailor sewing kitenge | Our Story ("Made by local hands") |
| `mural.jpg`: African pattern mural with plants | Home Experience teaser background, and as a divider strip on Menu, Experience and Careers |

They're shown in a gallery frame (`partials/art_panel.html`, label text via `title` / `note`). **Before launch, confirm Mbuzi Munch has permission to use each piece and add the artist or photographer credit** by passing `note="Artwork by …"` where the partial is included. To replace a piece, overwrite the file with the same name.

**Kitenge art:** four original African-print-inspired tiles in the brand colours (red, black, cream and an ochre accent) live in `static/img/kitenge/`: `diamond.svg`, `sun.svg`, `zigzag.svg` (border band) and `shuka.svg`. They're used as `.kitenge-band` dividers, the `.kitenge-art` home section, `.kitenge-frame` photo frames and the recycling chapter's side strip.

## Instagram content added on request

- **Private-party slider:** 12 venue photos from Instagram post DXgeV1MjEMv (`static/img/party/`) scroll right to left behind "Looking for a private party venue?" on the home page and the Events page header. The list is `PARTY_PHOTOS` in `core/views.py`.
- **Branch videos:** each branch can have a vertical reel (admin: Branches → Video / Video poster). Galleria has its reel; the Naivasha reel is on Delamere Naivasha.
- **Experience page:** the match-day screening reel is in the "Good times" chapter.
- **Events page, "More at Golf Park":** Derby Day (racecourse grill reel) and Golf Buggy Rental (9 holes KES 1,000, 18 holes KES 2,000, book on 0723 868 686).
- **QR badge:** the "Scan me" code is redrawn crisp by `python tools/make_qr.py [link]` (defaults to the menu page). Install `requirements-dev.txt` first.

## Hero pennant

As on the original mbuzimunch.com, a white pennant comes down from the header over the home-page hero. It holds a play button with a progress bar, the social links, "WE ARE OPEN" and the opening hours (edit them in `templates/core/home.html`). Its play button controls the same music as the goat record button.

The original site played "Fortunate Son" by Creedence Clearwater Revival. That recording is **not** included. Upload it under **Music tracks** only if Mbuzi Munch holds a licence to play it publicly (in Kenya, via the music rights bodies such as MCSK, KAMP and PRISK); otherwise use a royalty-free track.

## Music button

The spinning goat record (bottom-left) plays background music.

- **With no track uploaded:** it plays an original kalimba-and-drums groove generated in the browser (`static/js/music.js`), so there's nothing to license.
- **To use your own track:** upload it in admin under **Music tracks** (MP3/M4A). The newest active track replaces the generated groove. Only upload music you have the rights to play publicly.
- Music never autoplays on a first visit. If a visitor had it on, it resumes at their first tap on the next page.
- Turning on sound in a reel pauses the music, and vice versa.

## Notes

- The Galleria Mall photo on the old site is only 259 px wide; replace it in admin with a better shot when one is available.
- Instagram photos are the 12 latest posts as of November 2026. To refresh the grid, swap the files in `static/img/social/` (list in `core/views.py`, `INSTAGRAM_IMAGES`) and reels in `static/video/reels/` (`REELS`).
