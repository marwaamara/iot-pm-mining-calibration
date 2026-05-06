# Upload guide — get this code onto GitHub and Zenodo (~25 minutes total)

This guide walks you through:

1. Creating a GitHub account (skip if you have one)
2. Installing Git on your Windows machine (already done if you have Git Bash)
3. Creating a new repository on github.com
4. Pushing this `github/` folder to it
5. Linking Zenodo to your repo to get a permanent **DOI**
6. Citing the DOI in your manuscript Data Availability section

By the end of this you will have a public GitHub URL **and** a Zenodo
DOI you can paste into the manuscript.

---

## Before you start — final pre-upload checklist

Run this checklist once. If anything is "no", fix before pushing.

| Check | How |
|---|---|
| ☐ No personal credentials, API keys, or `.env` files in `code/` | `git diff` will show; also `grep -r "api_key\|password\|secret" code/`  |
| ☐ Email in code matches your manuscript | search `code/` for old emails |
| ☐ All `*.py` files have a docstring at the top | `head -5 code/*.py` |
| ☐ The repo runs end-to-end from a clean clone | see "Smoke test" at the bottom |
| ☐ `LICENSE`, `README.md`, `requirements.txt`, `CITATION.cff` all present | `ls` the repo root |

If any check fails, fix it locally, then proceed.

---

## Step 1 — Create a GitHub account (skip if you already have one)

1. Go to <https://github.com/signup>
2. Sign up with your **NBU email**: `Marwa.amara@nbu.edu.sa`
3. Choose a username — short, professional. Suggestion: `marwa-amara` or
   `marwaamara-nbu`. **The username will appear in the public repo URL**,
   so pick something you're happy to put in a CV.
4. Verify your email
5. (Recommended) After signup, request the GitHub Education Pack at
   <https://education.github.com/pack> — it's free for academics and gives
   you private repos, copilot, and other goodies.

**Estimated time: 3 minutes.**

---

## Step 2 — Install Git (if not already installed)

You already have Git Bash from your local TeXstudio / MiKTeX setup, so
this is probably done. Verify:

```bash
git --version
```

If it says `git version 2.x.x`, you're good. If not:

* Download from <https://git-scm.com/download/win>
* Run installer; accept all defaults
* Re-open your terminal

**Configure git once with your name and email** (Git uses these to label
each commit you make):

```bash
git config --global user.name "Marwa Amara"
git config --global user.email "Marwa.amara@nbu.edu.sa"
```

**Estimated time: 2 minutes.**

---

## Step 3 — Create the repository on github.com

1. Go to <https://github.com/new>
2. Fill in:
   * **Repository name:** `iot-pm-mining-calibration`
     (this becomes part of the public URL)
   * **Description:** *AI-enhanced calibration of IoT particulate matter
     sensors in open-pit mining: reproducibility code for Measurement
     manuscript MEAS-D-26-03768.*
   * **Public** (selected) — required for Zenodo to mint a DOI
   * **DO NOT** tick "Add a README file"
   * **DO NOT** tick "Add .gitignore"
   * **DO NOT** tick "Choose a license"

   (You're not ticking those because we already have these files locally,
   and ticking them creates a conflict.)

3. Click **Create repository**.

GitHub will now show you a page titled "Quick setup". Keep this page
open — you'll need the URL on it for Step 4.

**Estimated time: 2 minutes.**

---

## Step 4 — Push this folder to your new GitHub repo

Open **Git Bash** (or PowerShell, both work). Navigate to the `github/`
folder of this project:

```bash
cd "c:/Users/amara/Documents/mining scetor/github"
```

Then run these six commands, **one at a time**:

```bash
git init
git add .
git status                    # quick sanity check; you should see ~30 files staged
git commit -m "Initial release: reproducibility package for MEAS-D-26-03768"
git branch -M main
git remote add origin https://github.com/marwaamara/iot-pm-mining-calibration.git
git push -u origin main
```

Replace `marwaamara` with the GitHub username you chose in Step 1.

The first `git push` will prompt for authentication. **Use a Personal
Access Token, not your password** (GitHub disabled password auth in 2021):

* Go to <https://github.com/settings/tokens>
* Click **Generate new token (classic)**
* Name: `local-laptop`
* Expiration: 90 days (or longer)
* Scopes: tick **`repo`** (full control of private repositories) — that's
  enough for pushing public repos too
* Click **Generate token**, **copy the token immediately** (it won't be
  shown again), and paste it into the terminal when `git push` prompts
  for "Password".

After the push completes, refresh your repository page on github.com —
you should see all the files.

**Estimated time: 5 minutes.**

---

## Step 5 — Tag a release (this triggers Zenodo)

Releases are how Zenodo decides what to archive and assign a DOI to.

### 5a. On github.com, in your repository:

1. Click **Releases** (right sidebar) → **Create a new release**
2. Click **Choose a tag** → type `v1.0.0` → **Create new tag: v1.0.0 on publish**
3. **Release title:** `v1.0.0 — Major-revision reproducibility package`
4. **Description:**
   ```
   Reproducibility package for the major revision of MEAS-D-26-03768
   (Measurement, Elsevier).

   Headline results:
   - KAPSARC ANN PM2.5: RMSE 9.23 µg/m³, R² 0.952, U 20.07 µg/m³
   - SLV  ANN PM10  : RMSE 12.48 µg/m³, R² 0.766, U 32.76 µg/m³
   - Sensitivity to PMS5003 error-model parameters: |ΔRMSE| ≤ 2.34 µg/m³

   Includes the JCGM-101-compliant uncertainty pipeline (uncertainty.py),
   sensitivity analysis, all reviewer-requested diagnostics, and a
   point-by-point map of reviewer comments to code lines (see
   docs/REVIEWER_VERIFICATION.md).
   ```
5. **DO NOT** tick "This is a pre-release"
6. Click **Publish release**

**Estimated time: 3 minutes.**

---

## Step 6 — Link Zenodo to your repository

Zenodo (a CERN-hosted research-data archive) will mint a permanent DOI
for every GitHub release of your repo. This is the citable artefact you
put in the manuscript.

1. Go to <https://zenodo.org> and click **Log in**
2. Choose **Log in with GitHub** — this links your GitHub identity
3. Authorize Zenodo to access your GitHub account (read-only)
4. Once logged in, click your username (top right) → **GitHub** in the
   dropdown menu → you'll see a list of all your GitHub repos with
   on/off toggles
5. Find `iot-pm-mining-calibration` in the list → **flip the toggle ON**
6. Now go back to github.com and **publish a new release** (any release
   created after enabling Zenodo is auto-archived)

**Important:** the v1.0.0 release you created in Step 5 was *before*
Zenodo was enabled, so it won't have a DOI. Easiest fix:

* On github.com → Releases → **Draft a new release**
* Tag: `v1.0.1`
* Title: `v1.0.1 — DOI-trigger release`
* Description: *Same content as v1.0.0; this release exists to trigger
  Zenodo archival.*
* Click **Publish release**

Within ~2 minutes, Zenodo will create an archive and assign a DOI.
You can check the status at the same Zenodo → GitHub page.

### Get the DOI

1. After ~2 minutes, refresh the Zenodo → GitHub page
2. Click on `iot-pm-mining-calibration` row → you'll see the latest
   release with a DOI badge like `10.5281/zenodo.XXXXXXX`
3. **Copy this DOI** — you'll paste it in the next step

**Estimated time: 5 minutes.**

---

## Step 7 — Cite the DOI in your manuscript

In the Overleaf project, open `main.tex` and find the **Data Availability**
section. Replace the placeholder line with the real Zenodo DOI:

```latex
\section*{Data availability}

The reference PM and environmental data are from the KAPSARC Riyadh Air
Quality Dataset (CC0 licence), available at
\url{https://datasource.kapsarc.org}. The Salt Lake Valley validation
dataset is from \textit{The Hive} repository (CC BY 3.0,
\url{https://doi.org/10.7278/S50d-xbns-3ge3}). The calibration code,
GUM/JCGM-101 uncertainty pipeline, sensitivity-analysis script and all
figure-generation scripts are open-source under the MIT licence at
\url{https://github.com/marwaamara/iot-pm-mining-calibration}
and archived on Zenodo at \url{https://doi.org/10.5281/zenodo.XXXXXXX}.
```

Replace **both** `marwaamara` and `XXXXXXX` with the real values.

Also update `CITATION.cff` in the repo root with the real DOI:

```yaml
identifiers:
  - description: All-versions DOI on Zenodo
    type: doi
    value: 10.5281/zenodo.XXXXXXX     <-- paste real DOI here
```

Then commit and push the update:

```bash
cd "c:/Users/amara/Documents/mining scetor/github"
git add CITATION.cff
git commit -m "Update CITATION.cff with Zenodo DOI"
git push
```

**Estimated time: 5 minutes.**

---

## Smoke test (do this once before pushing)

To confirm a reviewer cloning fresh from your repo will get a working
build, run this in a *different* directory than the one you've been
working in:

```bash
# In a fresh terminal, somewhere outside this project
cd /tmp
git clone https://github.com/marwaamara/iot-pm-mining-calibration.git smoke
cd smoke
python -m venv .venv
.venv\Scripts\activate           # (or `source .venv/bin/activate` on Linux)
pip install -r requirements.txt
python code/uncertainty.py        # should print "True noise std = 1.000;  recovered u_A_model ~ 0.97"
python code/run_revision.py       # full pipeline; ~5–8 min
```

If this completes without errors and the headline numbers match what's
in `README.md`, you're done.

---

## Summary timeline

| Step | Time | Output |
|---|---|---|
| 1 — GitHub account | 3 min | account |
| 2 — git installed and configured | 2 min | configured locally |
| 3 — Create repo on github.com | 2 min | empty public repo |
| 4 — Push code | 5 min | repo is live |
| 5 — Tag v1.0.0 release | 3 min | release page on GitHub |
| 6 — Link Zenodo + tag v1.0.1 | 5 min | **Zenodo DOI** |
| 7 — Update manuscript Data Availability | 5 min | manuscript ready |
| **Total** | **~25 minutes** | **public, citable, DOI-linked code repo** |

---

## What this looks like to a reviewer

When R1 reads your revised manuscript, they will see in the Data
Availability section:

> *Code at `https://github.com/marwa-amara/iot-pm-mining-calibration`,
> archived on Zenodo at `https://doi.org/10.5281/zenodo.XXXXXXX`.*

If they click the GitHub link, they land on the README page. The README
has:

* The exact headline numbers they're being asked to verify
* A link to `docs/REVIEWER_VERIFICATION.md` mapping every one of their
  comments to the relevant code line
* A 3-command quick-start they can follow themselves

If they want to **independently verify your sensitivity claim**, they
clone the repo and run `python code/sensitivity_analysis.py`. That is
the strongest possible response to "your synthetic data limits
applicability".

---

## Mistakes you might make and how to recover

| Mistake | Recovery |
|---|---|
| Pushed an old API key by accident | DELETE the repo on github.com (Settings → Danger Zone → Delete this repository), revoke the key, then re-create following Step 3 |
| Pushed before adding `.gitignore` and committed `__pycache__/` | `git rm -r --cached __pycache__ && git commit -m "Drop cached" && git push` |
| Forgot the Zenodo step before tagging v1.0.0 | Just tag v1.0.1 as in Step 6 — Zenodo only archives releases created *after* the toggle is on |
| `git push` rejected with "remote has changes" | `git pull --rebase origin main` then `git push` again |
| Lost your Personal Access Token | Generate a new one — old one is just gone; nothing else breaks |

---

## Final reminder

Once your repo is public and the DOI is minted, **do not delete the
GitHub repository or the Zenodo record** even if you later want to make
changes — both are designed to be permanent (archive integrity).

If you want to revise, just push a new commit and tag a new version
(`v1.1.0`, `v1.2.0`, etc.). Zenodo archives each version separately and
gives you both a "version-specific" DOI and an "all-versions" DOI; the
all-versions DOI is what should appear in the manuscript so it always
points to the latest release.

Good luck with the resubmission.
