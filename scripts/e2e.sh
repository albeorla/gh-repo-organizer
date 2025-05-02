#!/usr/bin/env bash
##############################################################################
# e2e-rewrite-full.sh — fully rebuilds history in logical batches
##############################################################################
set -euo pipefail
shopt -s globstar nullglob

REMOTE_URL=${REMOTE_URL:-git@github.com:albeorla/gh-repo-organizer.git}
MAIN_BRANCH=${MAIN_BRANCH:-main}
NEW_BRANCH=${NEW_BRANCH:-rewrite/zero-based}
SAFE_COPY_DIR=${SAFE_COPY_DIR:-/tmp/repo-rewrite-full}
PY_CMD="poetry run"   # or "pipenv run", etc.

# ── 1. fresh workspace ──────────────────────────────────────────────────────
rm -rf "$SAFE_COPY_DIR"
git clone "$REMOTE_URL" "$SAFE_COPY_DIR/work"
cd       "$SAFE_COPY_DIR/work"

# ── 2. orphan branch, KEEP files, clear index ───────────────────────────────
git checkout --orphan "$NEW_BRANCH"
git rm -r --cached . >/dev/null   # <-- key change

# ── 3. batches ──────────────────────────────────────────────────────────────
BATCHES=(
  "init-skeleton: project layout & tooling:::README.md pyproject.toml .pre-commit-config.yaml .gitignore"
  "domain: core entities & business logic:::src/repo_organizer/domain/**/*"
  "application: use-cases & services:::src/repo_organizer/application/**/*"
  "infrastructure: adapters & gateways:::src/repo_organizer/infrastructure/**/* src/repo_organizer/interface/**/*"
  "bootstrap-cli-config: startup wiring & settings:::src/repo_organizer/bootstrap/**/* src/repo_organizer/cli/**/* src/repo_organizer/config/**/*"
  "cross-cutting: shared utils & misc root files:::src/repo_organizer/shared/**/* src/repo_organizer/utils/**/* src/repo_organizer/services/**/* src/repo_organizer/models/**/* scripts/**/* CLAUDE.md .env.example .python-version"
  "tests: green test-suite:::tests/**/*"
  "docs: user manual & architecture notes:::docs/**/*"
)

quality() {
  echo "      • format"; poetry run ruff format .
  echo "      • lint  "; poetry run ruff check .
  echo "      • tests "; poetry run pytest -q
}

# ── 4. commit each batch ────────────────────────────────────────────────────
for batch in "${BATCHES[@]}"; do
  MSG=${batch%%:::*}
  FILES=${batch#*:::}

  echo -e "\n▶  Staging batch: $MSG"
  git add $FILES 2>/dev/null || true

  if git diff --cached --quiet; then
    echo "      (nothing to commit – skipping)"
    continue
  fi

  echo "      Running quality gates"
  if quality; then
    git commit -m "$MSG"
  else
    echo "✖  Quality checks FAILED – fix and rerun"; exit 1
  fi
done

# ── 5. catch-all (anything still uncommitted) ───────────────────────────────
if ! git diff --quiet; then
  echo -e "\n▶  Catch-all commit"
  git add -A
  quality && git commit -m "final-catchall: add remaining files"
fi

# ── 6. show new history & push instructions ─────────────────────────────────
git --no-pager log --oneline --graph

cat <<EOF

If everything looks good:

  git push --force-with-lease origin HEAD:${MAIN_BRANCH}

EOF
