# Your essay site

## How to add a new essay

1. Create a new file in `essays/`, e.g. `essays/my-second-essay.md`
2. Start it with two lines:
   ```
   title: My Second Essay
   date: August 2026
   ```
3. Leave a blank line, then write your essay. Separate paragraphs with a blank line — that's it, no markdown syntax required.
4. Run:
   ```
   python build.py
   ```
   (On Windows with your PATH setup, you'll likely need `python -m build` won't
   work since build.py isn't a module — just run `python build.py` directly,
   or `py build.py` if `python` isn't recognized.)
5. This regenerates everything in `docs/` — that folder is your actual website.

## How to put it online for free (GitHub Pages)

1. Create a new repo on GitHub (public), e.g. `my-essays`.
2. Push this whole folder to it:
   ```
   git init
   git add .
   git commit -m "first essay site"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/my-essays.git
   git push -u origin main
   ```
3. On GitHub: go to the repo → Settings → Pages → under "Build and deployment",
   set Source to "Deploy from a branch", branch = `main`, folder = `/docs`. Save.
4. After a minute or two your site is live at:
   `https://YOUR-USERNAME.github.io/my-essays/`

Every time you write a new essay: edit the `.md` file, run `python build.py`,
then `git add . && git commit -m "new essay" && git push`. That's the whole
workflow — no server, no hosting bill, no CMS to maintain.

## Optional: auto-publish from Google Docs

If you'd rather write in Google Docs than edit `.md` files directly, there's
an automated pipeline: `gdrive-to-github.gs` + `.github/workflows/deploy.yml`.

**How it works:** a Google Apps Script checks a Drive folder every 15
minutes. Any Doc that's new or edited gets exported as plain text and
pushed into your GitHub repo's `essays/` folder (using the Doc's filename
as the title). A GitHub Action then automatically runs `build.py` and
commits the rebuilt site — so nothing runs on your machine.

**Setup:**
1. Push this whole repo (including `.github/workflows/deploy.yml`) to GitHub
   following the steps above.
2. Create a Drive folder for your essays. Copy its ID from the URL
   (`drive.google.com/drive/folders/THIS_PART_IS_THE_ID`).
3. Create a GitHub personal access token: GitHub → Settings → Developer
   settings → Personal access tokens → Fine-grained tokens → give it
   **Contents: Read and write** access, scoped to this one repo.
4. Go to script.google.com → New project → paste in `gdrive-to-github.gs`.
5. Project Settings (gear icon) → Script Properties → add:
   - `DRIVE_FOLDER_ID` — from step 2
   - `GITHUB_TOKEN` — from step 3
   - `GITHUB_REPO` — e.g. `yourusername/my-essays`
   - `GITHUB_BRANCH` — `main`
6. Run the `syncEssays` function once manually to authorize it.
7. Triggers (clock icon, left sidebar) → Add Trigger → function
   `syncEssays` → Time-driven → Minutes timer → Every 15 minutes.

From then on: create a Doc in that folder, write your essay, close the tab.
Within 15 minutes it's live on your site.

**Worth knowing:**
- Formatting is plain-text only for now (bold/links won't carry over) — same
  limitation as writing `.md` files directly. Upgrading this to preserve
  formatting means exporting the Doc as HTML instead of text; possible later,
  just more moving parts.
- Editing a Doc again just republishes it (overwrites the same file) — there's
  no "unpublish" yet if you want to pull something down, you'd delete the
  `.md` file from the repo manually.
- The trigger runs on your Google account's own execution quota, which is
  generous enough that 15-minute polling costs you nothing.

## Later, if you want to go further
- Custom domain: buy one (~$10/yr) and point it at GitHub Pages — the only
  non-free part of this whole setup if you want it.
- Real Markdown (bold, links, lists): swap the paragraph-splitting logic in
  `build.py` for the `markdown` pip package (`pip install markdown --break-system-packages`)
  and call `markdown.markdown(body_text)` instead.
- RSS feed: easy to bolt on once you have more than a couple essays.
