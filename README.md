# ElectionHub

Live election-night results for Nov. 3, 2026, served at electionhub.org. Built by Progress Report.

- `/` — Battleground Congressional Races: 15 key Senate races (including the Florida special election, Mississippi and New Hampshire) and 118 House races: the 81 Cook rates Likely, Lean or Toss Up, plus NY-01 (rated competitive by other forecasters) and six redistricting flips (CA-01, CA-06, CA-41, TX-32, TN-09, UT-01), plus an "Upset watch" group of 30 Republican-held seats Cook rated Solid R where Democrats ran close (added Nov. 4, 12:15am ET). Files: `index.html`, `baseline.json`, `data.json`.
- `/initiatives/` — Ballot Initiatives: the measures on Progress Report's 2026 ballot initiative tracker. Files: `initiatives/index.html`, `initiatives/data.json` (the measure list and results together), `initiatives/baseline.json` (a fixed copy of the measure list with no results, shown only if `data.json` is unreadable or empty).
- `/states/` — State Legislature Election Results: all 88 chambers and 10 competitive governor's races. Files: `states/index.html`, `states/baseline.json`, `states/data.json`, `states/governors.json`.
- `/statewide/` — Statewide Races: every governor, lieutenant governor, attorney general, secretary of state, treasurer and auditor/comptroller race on the Nov. 3 ballot, in all 50 states (states with no such races are listed too). Files: `statewide/index.html`, `statewide/baseline.json`, `statewide/data.json`. Governor results also come from `states/governors.json` (same ids, e.g. `WI-GOV`); the page merges the two, with a call always winning.
- `/legislatures/` — Competitive Legislative Races: the battleground state legislative districts from Jordan's competitive-districts sheet (AZ, PA, MI, MN, WI, NC, KS, NE, CO, NV, WA), seat by seat. Files: `legislatures/index.html`, `legislatures/data.json` (the race list and results together, written by the competitive-legislative-races scheduled task).

`baseline.json` files hold the race lists and stay fixed; scheduled tasks write the results into `data.json` and `states/governors.json` (congress and governors), `states/data.json` (legislatures), `statewide/data.json` (statewide races), `legislatures/data.json` (competitive legislative races) and `initiatives/data.json` (ballot measures) on election night and through Nov. 6. Each page re-checks its data every minute.

The old stateselections.org site is retired and redirects here.

The site deploys through the "Deploy site" GitHub Actions workflow (`.github/workflows/pages.yml`) on every push to main.
