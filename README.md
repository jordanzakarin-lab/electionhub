# ElectionHub

Live election-night results for Nov. 3, 2026, served at electionhub.org. Built by Progress Report.

- `/` — Battleground Congressional Races: 15 key Senate races (including the Florida special election, Mississippi and New Hampshire) and 86 House races: the 81 Cook rates Likely, Lean or Toss Up, plus NY-01 (rated competitive by other forecasters) and four redistricting flips (CA-01, CA-06, TX-32, TN-09). Files: `index.html`, `baseline.json`, `data.json`.
- `/states/` — State Legislature Election Results: all 88 chambers and 10 competitive governor's races. Files: `states/index.html`, `states/baseline.json`, `states/data.json`, `states/governors.json`.

`baseline.json` files hold the race lists and stay fixed; scheduled tasks write the results into `data.json` and `states/governors.json` (congress and governors) and `states/data.json` (legislatures) on election night and through Nov. 6. Each page re-checks its data every minute.

The old stateselections.org site is retired and redirects here.

The site deploys through the "Deploy site" GitHub Actions workflow (`.github/workflows/pages.yml`) on every push to main.
