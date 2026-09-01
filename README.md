# Us — a private question game for two

A private, free, mobile-first question game for you and your partner. Answer
questions independently from your own phones; nothing is revealed until
**both** of you have answered. Built with Flask + SQLAlchemy on the backend
and a small vanilla-JS PWA on the frontend — no build step, no framework
lock-in, easy to keep hacking on.

> This app was built to a detailed brief. Section numbers below (e.g. "brief
> §41") refer back to that spec so you can see where a design choice came
> from.

---

## 1. What's here

- **Answer privacy, enforced server-side.** Nothing about a partner's answer
  — not the text, not its length, not a hidden HTML node — is ever sent to
  the browser until the current user has submitted their own answer to the
  same question. See `app/services/privacy.py`.
- **Couples of exactly two**, joined via a 6-character invite code.
- **180 seeded questions** across 8 categories, including an opt-in, tasteful
  **Spicy** category with three intensity levels, private-answer support, and
  a "find your mutual matches" feature.
- **Daily question**, timezone-aware per couple, stable all day and shared by
  both partners.
- **Random questions**, browsing by category, favourites, reactions,
  comments, a Memories history, lightweight stats, and "How Well Do You Know
  Me?" prediction scoring.
- **Installable PWA** — manifest, service worker, home-screen icon.
- **25 automated tests**, including the exact end-to-end privacy scenario
  from the brief (two clients, cross-couple isolation, duplicate-answer
  prevention, private-answer masking).

## 2. Assumptions made (brief §59)

The brief said to make sensible calls on anything unspecified rather than
ask a lot of questions up front. Here's what was decided, and why:

- **One combined Flask app**, not a separate Cloudflare Pages frontend +
  API. The brief allowed this ("if Flask requires a different approach,
  choose a practical solution"). Since auth uses secure session cookies,
  keeping frontend and backend on the same origin avoids cross-site cookie
  and CORS headaches entirely — simpler and more secure for a two-person app.
- **Prediction questions ("How Well Do You Know Me?")** have both partners
  answer *and* predict in the same round (rather than a strict
  predictor/answerer split), since the app is asynchronous and there's no
  natural "whose turn is it" concept. Both directions get scored.
- **The brief's "🔥 Flirty" category (§9)** was folded into the more fully
  specified **Spicy** category from the addendum (§60), which has its own
  "Flirty" tier (level 1) plus Intimate/Adventurous. Having two separate
  optional romantic categories seemed redundant.
- **"Delete my account" (§40/53)** removes your login and personal content
  (answers, reactions, comments, favourites). If you're the last member of
  the couple, the couple is removed too; if your partner is still there,
  their own content is untouched and the couple stays open to a new invite.
- **Spicy "keep private" answers** are never included in match-aggregation,
  in either direction — a private answer contributes to neither a "match"
  nor a "something to discuss" flag.
- **The mutual-match "something to discuss" flag** deliberately never says
  *which* topic differed — only that one exists — matching the brief's own
  example output, which does the same.
- **Streaks** are based on the shared daily question being completed
  (revealed) on consecutive calendar days in the couple's chosen timezone.

## 3. Project structure

```
us-app/
├── app/
│   ├── __init__.py          # app factory, error handlers
│   ├── config.py            # Dev/Prod/Testing config from env vars
│   ├── extensions.py        # db, migrate, login_manager, bcrypt, csrf
│   ├── models/               # Couple, User, Question, Round, Answer, ...
│   ├── routes/                # one blueprint per resource
│   ├── services/              # privacy engine, question picking, stats,
│   │                           prediction scoring, spicy matches
│   ├── templates/             # index.html (PWA shell) + error.html
│   └── static/
│       ├── css/style.css     # the whole design system
│       ├── js/                # vanilla ES modules, no build step
│       ├── icons/             # generated PWA icons
│       └── manifest.json
├── migrations/                # Flask-Migrate/Alembic
├── seed/seed_questions.py     # the 180-question bank (edit this to add more)
├── seed/seed.py                # idempotent seed runner
├── scripts/generate_icons.py   # regenerates the heart-mark app icons
├── tests/                      # pytest suite
├── requirements.txt
├── .env.example
└── run.py
```

## 4. Local setup

```bash
cd us-app
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and set SECRET_KEY to a random string:
python -c "import secrets; print(secrets.token_hex(32))"

export FLASK_APP=run.py           # Windows (PowerShell): $env:FLASK_APP="run.py"
flask db upgrade                  # creates instance/us.db (SQLite) and applies the schema
python seed/seed.py               # loads the 180 starter questions

python run.py
```

Visit **http://127.0.0.1:5000**. Open it in two different browsers (or one
normal + one incognito window) to play as both partners at once.

### Running the tests

```bash
pip install pytest
python -m pytest tests/ -v
```

All 25 tests should pass, including `test_full_scenario_from_brief`, which
walks through the exact 20-step verification scenario from brief §58.

## 5. Adding more questions later (brief §41/42)

No code changes needed. Open `seed/seed_questions.py`, add entries to the
`QUESTIONS` list (each is a small dict — see the existing ones for the
shape), then re-run:

```bash
python seed/seed.py
```

It only inserts questions that aren't already there (matched by exact text +
category), so it's always safe to re-run.

## 6. Deploying for free

This deploys the whole app (frontend + backend together) to **Render**, and
Postgres to **Supabase**, matching the brief's suggested stack. Both have
genuinely usable free tiers as of writing — Render's free web service has no
credit-card requirement; check current limits on each provider's pricing
page before you commit to it, since free-tier terms do shift over time.

**Two things worth knowing up front**, so they don't feel like bugs:

- Render's free web service **spins down after 15 minutes of no traffic**.
  The next visit takes ~30-60 seconds to "wake up." Totally fine for a
  personal app.
- Supabase's free Postgres project **auto-pauses after 7 days with no
  activity**. Your data isn't deleted — just log into the Supabase dashboard
  and click **Restore** if that happens.

### 6.1 Create the database (Supabase)

1. Create a free account at [supabase.com](https://supabase.com) and a new
   project.
2. In **Project Settings → Database → Connection string**, copy the **URI**
   (choose the pooled "Transaction" connection string for a long-running app
   like this one). It looks like:
   `postgresql://postgres.[project-ref]:[password]@aws-...pooler.supabase.com:6543/postgres`
3. Keep this handy — it's your `DATABASE_URL`.

### 6.2 Deploy the app (Render)

1. Push this project to a GitHub repository.
2. At [render.com](https://render.com), **New → Web Service**, connect the
   repo.
3. Settings:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:**
     ```
     flask db upgrade && python seed/seed.py && gunicorn run:app
     ```
     (Both `flask db upgrade` and `seed.py` are safe to re-run on every
     deploy/restart — they only apply what's missing.)
4. Add environment variables (Render dashboard → Environment):
   | Key | Value |
   |---|---|
   | `SECRET_KEY` | a long random string (generate one the same way as local setup) |
   | `DATABASE_URL` | the Supabase URI from step 6.1 |
   | `FLASK_APP` | `run.py` |
   | `FLASK_ENV` | `production` |
   | `SESSION_COOKIE_SECURE` | `true` |
5. Deploy. Render gives you a free `https://your-app.onrender.com` URL — no
   domain purchase needed, and HTTPS is automatic (required for the PWA
   service worker and secure cookies to work).

### 6.3 Test on your phones

1. Open the Render URL on your phone.
2. Create a couple, share the invite code with your partner (or send them
   the same URL and have them tap **Join a Couple**).
3. **Add to Home Screen**: iPhone (Safari) → Share → Add to Home Screen.
   Android (Chrome) → ⋮ menu → Add to Home Screen / Install app.
4. You should get an icon named **Us** that opens full-screen, no browser
   chrome.

## 7. Security notes

- Passwords are hashed with bcrypt (`Flask-Bcrypt`), never stored plaintext.
- Sessions are signed, `HttpOnly`, `SameSite=Lax` cookies via `Flask-Login`.
- Every round/answer/comment/reaction/favourite endpoint checks that the
  resource belongs to the current user's couple **on the server** before
  returning or mutating anything — see `app/services/privacy.py`. A
  cross-couple request gets an identical 404 to a nonexistent one, so it
  never confirms another couple's data exists.
- CSRF protection (`Flask-WTF`) is active on every mutating request; the
  frontend reads the token from a `<meta>` tag and sends it as
  `X-CSRFToken`.
- All user-generated text (names, answers, comments) is HTML-escaped before
  insertion into the DOM (`static/js/utils.js#escapeHtml`) to prevent XSS.
- The Spicy category is off by default and requires **both** partners to
  independently opt in (with an adult-confirmation checkbox) before any
  spicy question, spicy history, or the matches feature becomes reachable.

## 8. Known minor cleanup (non-blocking)

A few SQLAlchemy 2.0 / Python deprecation warnings show up in the test
output (`Query.get()` and `datetime.utcnow()` are both legacy spellings as
of SQLAlchemy 2.0 / Python 3.12). They don't affect correctness on the
current versions pinned in `requirements.txt`, but if you upgrade
dependencies later, a search-and-replace to `db.session.get(...)` and
`datetime.now(timezone.utc)` is a nice follow-up.

## 9. License / credits

Built for personal use. Not affiliated with Paired, Couple Joy, or
CoupleMind — "Us" has its own name, wording, and design.
