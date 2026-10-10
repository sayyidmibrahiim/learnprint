# Publish the source as a new GitHub public repository

The linked GitHub integration used to assemble this package can inspect/edit **existing** repositories but cannot create a new one. Do **not** assume the repo already exists.

1. In GitHub, create an **empty PUBLIC** repository named `learnprint` under the intended account (do not initialize with README/license/gitignore, since those are in the package).
2. Option A (from source ZIP): extract `learnprint-source.zip`, then:

```sh
cd learnprint
git init -b main
git add .
git commit -m "feat: initial evidence-based portable learning skills"
git remote add origin https://github.com/sayyidmibrahiim/learnprint.git
git push -u origin main
```

3. Option B (if a git bundle is supplied): `git clone -b main learnprint.git.bundle learnprint`, then add `origin` and push as above. GitHub authentication must be provided by the owner.
4. Verify the repository's visibility says **Public**, `main` contains both skill dirs and CI runs, and no `my-learning/`, transcripts, private projects or secrets were committed.
5. Install skills into a **separate approved project** with `python scripts/install.py --target <platform> --dest <project> --dry-run` then `--approve`. Existing files are not overwritten.

Do not push a personal profile or history unless the learner independently decides to publish it. The anonymous founder default in this repo was intentionally generalized, and raw assessment chats are excluded.
