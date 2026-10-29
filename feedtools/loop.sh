#!/usr/bin/env bash
# Poll official feeds and publish feeds/*.json until END_UTC (epoch seconds), every INTERVAL seconds.
# ONCE=1 does a single pass. Pushes as github-actions, then asks the Pages workflow to deploy
# (pushes made with GITHUB_TOKEN don't trigger other workflows on their own).
set -u
END=${END_UTC:-0}; INTERVAL=${INTERVAL:-120}
git config user.name "jordanzakarin-lab"; git config user.email "jordanzakarin@gmail.com"
# hard stop after the 2026 count window, so the yearly cron dates do nothing in later years
if [ "$(date -u +%Y%m%d)" -gt 20261110 ]; then echo "past 2026 window; exiting"; exit 0; fi
BRANCH=${BRANCH:-main}; PULLARGS=${PULLARGS:-}
[ "$BRANCH" != main ] && { git fetch -q origin "$BRANCH" 2>/dev/null && git checkout -q -B "$BRANCH" "origin/$BRANCH" || git checkout -q -B "$BRANCH"; }
while :; do
  python3 feedtools/pull.py $PULLARGS || echo "pull failed"
  if [ -n "$(git status --porcelain feeds)" ]; then
    git add feeds
    git commit -qm "Official feed results $(TZ=America/New_York date '+%-I:%M %p') ET"
    ok=0
    for i in 1 2 3; do
      if { git pull -q --rebase -X theirs origin "$BRANCH" 2>/dev/null || [ "$BRANCH" != main ]; } && git push -q origin "HEAD:$BRANCH"; then ok=1; break; fi
      sleep 5
    done
    if [ $ok = 1 ]; then
      echo "pushed to $BRANCH"
      [ "$BRANCH" = main ] && { gh workflow run pages.yml --ref main || echo "deploy dispatch failed"; }
    else
      echo "push failed"; git rebase --abort 2>/dev/null; git reset -q --hard "origin/$BRANCH" 2>/dev/null
    fi
  fi
  [ "${ONCE:-0}" = 1 ] && break
  [ "$(date -u +%s)" -ge "$END" ] && break
  sleep "$INTERVAL"
done
