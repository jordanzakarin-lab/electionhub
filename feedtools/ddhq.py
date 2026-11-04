#!/usr/bin/env python3
"""Merge Decision Desk HQ results (output of feedtools/ddhq.js) into the ElectionHub data files.

Usage: python3 feedtools/ddhq.py apply <ddhq_output.txt> [--asof ISO]
Writes data.json, states/governors.json and statewide/data.json in place (repo root = cwd).
Rules: never undo a call; DDHQ "winner" = a DDHQ call; an existing entry is replaced only when
DDHQ has at least as many dem+rep votes counted (or calls the race); every other race is untouched.
"""
import json, sys, re, datetime

ROOT = '.'
FILES = ['data.json', 'states/governors.json', 'statewide/data.json']


def load(p):
    try:
        return json.load(open(f'{ROOT}/{p}'))
    except Exception:
        return {'updated': None, 'sample': False, 'races': []}


def norm(s):
    s = (s or '').lower()
    s = re.sub(r'\b(jr|sr|ii|iii|iv)\.?$', '', s.strip())
    return re.sub(r'[^a-z]', '', s)


def last_of(name):
    parts = [p for p in re.split(r'\s+', (name or '').strip()) if p]
    while len(parts) > 1 and norm(parts[-1]) in ('', 'jr', 'sr', 'ii', 'iii', 'iv'):
        parts.pop()
    return norm(parts[-1]) if parts else ''


def parse(path):
    races = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('MAPPED') or '|' not in line:
            continue
        dd, tot, est, upd, cands = line.split('|', 4)
        cl = []
        for c in cands.split(';'):
            f = c.split('~')
            if len(f) < 7:
                continue
            cl.append({'last': f[0], 'first': f[1], 'party': f[2], 'votes': int(f[3]), 'pct': float(f[4]),
                       'winner': f[5] == '1', 'inc': f[6] == '1'})
        races[int(dd)] = {'tot': int(tot), 'est': int(est or 0), 'upd': upd, 'c': cl}
    return races


def pick(cands, name, party_pref):
    ln = last_of(name)
    m = [c for c in cands if norm(c['last']).endswith(ln) or ln.endswith(norm(c['last']))] if ln else []
    if len(m) > 1:
        fn = norm((name or '').split()[0]) if name else ''
        m2 = [c for c in m if c['inc']] or [c for c in m if fn and norm(c['first']).startswith(fn[:3])]
        m = m2 or m
    if m:
        return m[0]
    m = [c for c in cands if c['party'] in party_pref]
    return m[0] if m else None


def main():
    if len(sys.argv) < 3 or sys.argv[1] != 'apply':
        print(__doc__); sys.exit(1)
    asof = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).isoformat(timespec='seconds')
    if '--asof' in sys.argv:
        asof = sys.argv[sys.argv.index('--asof') + 1]
    dd = parse(sys.argv[2])
    mp = json.load(open(f'{ROOT}/feedtools/ddhq_map.json'))['races']
    base = {}
    b = load('baseline.json')
    for r in b.get('senate', []) + b.get('races', []):
        base[r['id']] = r
    for r in load('states/baseline.json').get('governors', []):
        base[r['id']] = r
    for r in load('statewide/baseline.json').get('races', []):
        base.setdefault(r['id'], r)
    files = {p: load(p) for p in FILES}
    changed, calls, report = set(), [], []
    for eid, m in mp.items():
        x = dd.get(m['ddhq'])
        if not x or eid not in base:
            continue
        bl = base[eid]
        demP = bl.get('demParty', 'D'); repP = bl.get('repParty', 'R')
        dc = pick(x['c'], bl.get('dem'), ['IND'] if demP == 'I' else ['DEM', 'DFL'])
        rc = pick(x['c'], bl.get('rep'), ['IND', 'NPA'] if repP == 'I' else ['GOP', 'REP'])
        if rc is dc:
            rc = None
        def slot(c):
            if c is None: return None
            if c is dc: return demP
            if c is rc: return repP
            return 'I'
        top = max(x['c'], key=lambda c: c['votes']) if x['c'] else None
        win = next((c for c in x['c'] if c['winner']), None)
        dv = dc['votes'] if dc else 0; rv = rc['votes'] if rc else 0
        e = {'id': eid,
             'status': 'Called' if win else 'Counting',
             'leader': slot(win or top) if (win or (top and top['votes'] > 0)) else None,
             'reporting': (f"{min(99, round(100 * x['tot'] / x['est']))}%" if x['est'] and not win else
                           (f"{min(100, round(100 * x['tot'] / x['est']))}%" if x['est'] else '')),
             'dem': {'name': bl.get('dem') or (dc and f"{dc['first']} {dc['last']}"), 'votes': dv, 'pct': round(dc['pct'], 1) if dc else 0},
             'rep': {'name': bl.get('rep') or (rc and f"{rc['first']} {rc['last']}"), 'votes': rv, 'pct': round(rc['pct'], 1) if rc else 0},
             'marginPts': round((dc['pct'] if dc else 0) - (rc['pct'] if rc else 0), 1),
             'marginVotes': abs(dv - rv),
             'calledBy': 'DDHQ' if win else None,
             'source': f"https://votes.decisiondeskhq.com/races/2026-11-03/{m['slug']}",
             'asOf': asof,
             'ddhqUpdated': x['upd']}
        others = [c for c in x['c'] if c is not dc and c is not rc and c['votes'] > 0][:3]
        if others:
            e['others'] = [{'name': f"{c['first']} {c['last']}", 'party': c['party'], 'votes': c['votes'], 'pct': round(c['pct'], 1)} for c in others]
        f = files[m['file']]
        races = f.setdefault('races', [])
        old = next((r for r in races if r.get('id') == eid), None)
        if old:
            old_called = old.get('status') == 'Called'
            oldv = ((old.get('dem') or {}).get('votes') or 0) + ((old.get('rep') or {}).get('votes') or 0)
            if not win and oldv > dv + rv:
                continue  # existing source has more counted; leave it
            if old_called and not win:
                for k in ('status', 'leader', 'calledBy'):
                    e[k] = old.get(k)
            if old.get('status') in ('Runoff', 'RCV') and not win:
                e['status'] = old['status']
            races[races.index(old)] = e
        else:
            races.append(e)
        changed.add(m['file'])
        if win and not (old and old.get('status') == 'Called'):
            held = bl.get('held')
            flip = ' FLIP' if held and e['leader'] and e['leader'] != held else ''
            calls.append(f"{eid}: DDHQ called for {win['first']} {win['last']} ({win['party']}){flip}")
        report.append(f"{eid} {e['leader'] or '-'} {e['marginPts']:+.1f} {e['reporting']}")
    for p in changed:
        files[p]['updated'] = asof
        files[p]['sample'] = False
        json.dump(files[p], open(f'{ROOT}/{p}', 'w'), indent=1)
    print(f"UPDATED {len(report)} races in {sorted(changed)}")
    for c in calls:
        print('CALL', c)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
