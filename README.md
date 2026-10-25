# ElectionHub

Live election-night results for Nov. 3, 2026, served at electionhub.org.

- `/` — Battleground Congressional Races: 11 key Senate races and the 81 House races Cook rates Likely, Lean or Toss Up (`index.html`, `baseline.json`, `data.json`)
- `/states/` — State Legislature Election Results: all 88 chambers (`states/index.html`, `states/baseline.json`, `states/data.json`)

Mirrors stateselections.org (repo `jordanzakarin-lab/stateelections`). The election-night scheduled tasks push the same `data.json` files to both repos: `congress/data.json` there → `data.json` here, and root `data.json` there → `states/data.json` here.
