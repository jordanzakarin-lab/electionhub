#!/usr/bin/env python3
"""Pull official machine-readable results for North Carolina, Minnesota and Washington
and write feeds/congress.json and feeds/states.json for ElectionHub.

These files only ever hold vote counts (status "Counting"); race calls come from the
Claude scheduled tasks. The pages merge them: a call always wins, otherwise the entry
with more votes counted wins.

Usage:
  python3 feedtools/pull.py                    # election night: 2026 files, poll-closing gate on
  python3 feedtools/pull.py --date 20241105 --no-gate --out test-feeds   # dry run on 2024 data
"""
import argparse, csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timezone, timedelta

ET = timezone(timedelta(hours=-5))  # EST; DST ends Nov 1, 2026
UA = {'User-Agent': 'Mozilla/5.0 (ElectionHub results bot; electionhub.org; jordanzakarin@gmail.com)'}
# Polls closed in each state (ET, Nov 3, 2026). Before this, the state's files may hold test data.
POLLS_CLOSE = {'NC': (19, 30), 'MN': (21, 0), 'WA': (23, 0)}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')


def party_of(raw):
    p = (raw or '').upper()
    if p in ('DEM', 'DFL', 'D') or 'DEMOCRAT' in p:
        return 'D'
    if p in ('REP', 'R') or 'REPUBLICAN' in p or p == 'GOP':
        return 'R'
    if p in ('WI', '') or 'WRITE' in p:
        return 'W'
    return 'I'


def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def build(cands, reporting, source, as_of):
    """cands: list of (name, party, votes). Returns a race dict or None if no votes yet."""
    total = sum(v for _, _, v in cands)
    if total <= 0:
        return None
    real = [c for c in cands if c[1] != 'W']
    real.sort(key=lambda c: -c[2])
    top = real[0] if real else None
    d = next((c for c in real if c[1] == 'D'), None)
    r = next((c for c in real if c[1] == 'R'), None)
    if d is None or r is None:
        # one-party field (WA top-two D vs D, or uncontested): fill the empty slot with the runner-up
        others = [c for c in real if c is not d and c is not r]
        if d is None and others:
            d = others.pop(0)
        if r is None and others:
            r = others.pop(0)
    slot = lambda c: {'name': c[0], 'votes': c[2], 'pct': pct(c[2], total)} if c else {}
    used = {id(x) for x in (d, r) if x}
    other = sum(c[2] for c in cands if id(c) not in used)
    dp = pct(d[2], total) if d else 0.0
    rp = pct(r[2], total) if r else 0.0
    return {
        'status': 'Counting', 'leader': (top[1] if top and top[1] in 'DR' else 'I') if top else None,
        'reporting': reporting, 'dem': slot(d), 'rep': slot(r), 'other': other,
        'marginPts': round(dp - rp, 1), 'marginVotes': abs((d[2] if d else 0) - (r[2] if r else 0)),
        'calledBy': None, 'source': source, 'asOf': as_of, 'feed': True, 'totalVotes': total,
    }


# ---------- per-state readers: return {contest_key: (cands, reporting, source)} ----------

def read_nc(date):
    url = f'https://er.ncsbe.gov/enr/{date}/data/results_0.txt'
    rows = json.loads(fetch(url))
    out = {}
    for x in rows:
        cnm = x['cnm']
        if re.match(r'US SENATE\b', cnm):
            key = ('SEN', None)
        elif m := re.match(r'US HOUSE OF REPRESENTATIVES DISTRICT 0*(\d+)', cnm):
            key = ('HOUSE', m.group(1))
        elif m := re.match(r'NC STATE SENATE DISTRICT 0*(\d+)', cnm):
            key = ('upper', m.group(1))
        elif m := re.match(r'NC HOUSE OF REPRESENTATIVES DISTRICT 0*(\d+)', cnm):
            key = ('lower', m.group(1))
        else:
            continue
        e = out.setdefault(key, [[], '', url])
        e[0].append((x['bnm'], party_of(x['pty']), int(x['vct'] or 0)))
        prt, ptl = int(x['prt'] or 0), int(x['ptl'] or 0)
        e[1] = f'{round(100 * prt / ptl)}%' if ptl else ''
    return out


def read_mn(date):
    out = {}
    base = f'https://electionresultsfiles.sos.mn.gov/{date}/'
    for f in ('ussenate.txt', 'ushouse.txt', 'stsenate.txt', 'LegislativeByDistrict.txt'):
        try:
            text = fetch(base + f)
        except Exception as e:
            print(f'MN {f}: {e}', file=sys.stderr)
            continue
        for line in text.splitlines():
            p = line.split(';')
            if len(p) < 16:
                continue
            office, dist, name, party = p[4], p[5].strip(), p[7], p[10]
            if office.startswith('U.S. Senator'):
                key = ('SEN', None)
            elif office.startswith('U.S. Representative'):
                key = ('HOUSE', dist.lstrip('0'))
            elif office.startswith('State Senator'):
                key = ('upper', dist.lstrip('0'))
            elif office.startswith('State Representative'):
                key = ('lower', dist.lstrip('0'))
            else:
                continue
            e = out.setdefault(key, [[], '', base + f])
            e[0].append((name, party_of(party), int(p[13] or 0)))
            rep, tot = int(p[11] or 0), int(p[12] or 0)
            e[1] = f'{round(100 * rep / tot)}%' if tot else ''
    return out


def read_wa(date):
    out = {}
    for f in ('Congressional', 'Legislative'):
        url = f'https://results.vote.wa.gov/results/{date}/export/{date}_{f}.csv'
        try:
            text = fetch(url)
        except Exception as e:
            print(f'WA {f}: {e}', file=sys.stderr)
            continue
        for row in csv.DictReader(io.StringIO(text)):
            race = row['Race']
            if m := re.search(r'Congressional District (\d+)', race, re.I):
                key = ('HOUSE', m.group(1))
            elif m := re.match(r'LEGISLATIVE DISTRICT (\d+) - State Senator', race, re.I):
                key = ('upper', m.group(1))
            elif m := re.match(r'LEGISLATIVE DISTRICT (\d+) - State Representative Pos\.? ?(\d)', race, re.I):
                key = ('lower', f'{m.group(1)} Position {m.group(2)}')
            else:
                continue
            e = out.setdefault(key, [[], '', url])  # WA publishes no share-counted figure
            e[0].append((row['Candidate'], party_of(row['Party']), int(row['Votes'] or 0)))
    return out


READERS = {'NC': read_nc, 'MN': read_mn, 'WA': read_wa}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default='20261103')
    ap.add_argument('--no-gate', action='store_true', help='skip the poll-closing gate (testing on past data only)')
    ap.add_argument('--out', default='feeds')
    ap.add_argument('--root', default='.')
    a = ap.parse_args()

    now = datetime.now(ET)
    as_of = now.isoformat(timespec='seconds')
    cong = json.load(open(os.path.join(a.root, 'baseline.json')))
    sb = json.load(open(os.path.join(a.root, 'states/baseline.json')))
    eday = datetime(2026, 11, 3, tzinfo=ET)

    congress, states, log = [], [], []
    for st, reader in READERS.items():
        h, mi = POLLS_CLOSE[st]
        if not a.no_gate and now < eday.replace(hour=h, minute=mi):
            log.append(f'{st}: polls not closed yet, skipped')
            continue
        try:
            data = reader(a.date)
        except Exception as e:
            log.append(f'{st}: FAILED {e}')
            continue
        n_c = n_s = 0
        # Congress (Senate + House) by baseline id
        for b in cong.get('senate', []) + cong.get('races', []):
            if b['st'] != st:
                continue
            key = ('SEN', None) if b['id'].endswith('-SEN') else ('HOUSE', str(int(b['district'])) if str(b.get('district', '')).isdigit() else None)
            if key not in data:
                continue
            cands, rep, src = data[key]
            race = build(cands, rep, src, as_of)
            if race:
                race['id'] = b['id']
                congress.append(race); n_c += 1
        # Legislature: every district up this year
        for c in sb['chambers']:
            if c['st'] != st or not c.get('election'):
                continue
            for row in c['districts']:
                if not row.get('up'):
                    continue
                d = str(row['d']).lstrip('0')
                keys = [(c['ch'], d)]
                if st == 'WA' and c['ch'] == 'lower':
                    keys = [('lower', f'{d} Position {p}') for p in (1, 2)]
                for k in keys:
                    if k not in data:
                        continue
                    cands, rep, src = data[k]
                    race = build(cands, rep, src, as_of)
                    if not race:
                        continue
                    label = k[1]
                    pref = {'upper': 'SD', 'lower': 'HD'}[c['ch']] if st != 'WA' else 'LD'
                    pos = re.search(r'Position (\d)', label)
                    inc = row.get('inc') or []
                    held = inc[int(pos.group(1)) - 1][1] if pos and len(inc) >= int(pos.group(1)) else (inc[0][1] if inc else None)
                    race.update({'state': st, 'chamber': 'Senate' if c['ch'] == 'upper' else 'House',
                                 'district': f'{pref}-{label}', 'held': held,
                                 'wouldFlip': bool(held and race['leader'] and race['leader'] != held)})
                    states.append(race); n_s += 1
        log.append(f'{st}: {n_c} congressional, {n_s} legislative races with votes')

    os.makedirs(a.out, exist_ok=True)
    for name, races in (('congress.json', congress), ('states.json', states)):
        path = os.path.join(a.out, name)
        try:
            old = json.load(open(path))
        except Exception:
            old = {}
        strip = lambda r: {k: v for k, v in r.items() if k != 'asOf'}
        key = lambda r: r.get('id') or f"{r.get('state')}|{r.get('chamber')}|{r.get('district')}"
        prev = {key(r): r for r in old.get('races', [])}
        for r in races:  # a race whose numbers didn't move keeps the time they last changed
            p = prev.get(key(r))
            if p and strip(p) == strip(r):
                r['asOf'] = p.get('asOf', r['asOf'])
        if old and [strip(r) for r in old.get('races', [])] == [strip(r) for r in races]:
            continue  # nothing new; leave the file unchanged
        json.dump({'updated': as_of, 'source': 'official state results files (NC, MN, WA)', 'races': races},
                  open(path, 'w'), indent=1)
    print('\n'.join(log))


if __name__ == '__main__':
    main()
