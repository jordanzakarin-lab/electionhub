// Run in a browser tab on https://votes.decisiondeskhq.com (same-origin API).
// Reads the race map and the live ElectionHub data from GitHub, fetches every mapped
// DDHQ race, and returns one line per race whose DDHQ data changed since the site's
// last DDHQ write and has votes:
// ddhqId|totalVotes|estMid|lastUpdated|cand;cand;...   cand = last~first~PARTY~votes~pct~winner(1/0)~incumbent(1/0)
(async () => {
  const RAW = 'https://raw.githubusercontent.com/jordanzakarin-lab/electionhub/main/';
  const j = p => fetch(RAW + p + '?t=' + Date.now()).then(r => r.json()).catch(() => ({}));
  const [map, d1, d2, d3] = await Promise.all([j('feedtools/ddhq_map.json'), j('data.json'), j('states/governors.json'), j('statewide/data.json')]);
  const seen = {};
  for (const f of [d1, d2, d3]) for (const r of (f.races || [])) if (r.ddhqUpdated) seen[r.id] = r.ddhqUpdated;
  const todo = Object.entries(map.races || {}).map(([id, v]) => [id, v.ddhq]);
  const out = [], fails = [];
  const one = async ([id, dd]) => {
    for (let a = 0; a < 2; a++) {
      try {
        const r = await fetch('/api/races/' + dd);
        if (r.status === 429) { await new Promise(s => setTimeout(s, 2500)); continue; }
        if (!r.ok) { fails.push(id + ':' + r.status); return; }
        const x = await r.json(), rd = x.raceData || {};
        const top = (rd.toplineResults || []).slice().sort((a, b) => b.votes - a.votes);
        const tot = top.reduce((s, c) => s + (c.votes || 0), 0);
        if (!tot && !top.some(c => c.winner)) return;
        if (seen[id] && seen[id] === rd.lastUpdated) return;
        const est = (rd.turnout && rd.turnout.estimated_votes_mid) || 0;
        out.push([dd, tot, est, rd.lastUpdated, top.slice(0, 6).map(c =>
          [(c.lastName || '').replace(/[~;|]/g, ''), (c.firstName || '').replace(/[~;|]/g, ''), c.party && c.party.abbrev, c.votes || 0, (+c.percent || 0).toFixed(2), c.winner ? 1 : 0, c.incumbent ? 1 : 0].join('~')).join(';')].join('|'));
        return;
      } catch (e) { fails.push(id + ':err'); return; }
    }
    fails.push(id + ':429');
  };
  for (let i = 0; i < todo.length; i += 6) {
    await Promise.all(todo.slice(i, i + 6).map(one));
    await new Promise(s => setTimeout(s, 150));
  }
  return 'MAPPED ' + todo.length + ' CHANGED ' + out.length + ' FAILS ' + (fails.join(',') || 'none') + '\n' + out.join('\n');
})()
