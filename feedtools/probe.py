import urllib.request, json, collections
H={'User-Agent':'Mozilla/5.0 (ElectionHub results bot; jordanzakarin@gmail.com)'}
def raw(u):
    try: return urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30).read().decode('utf-8','replace')
    except Exception as e: return 'ERR '+str(e)
d=json.loads(raw('https://er.ncsbe.gov/enr/20261103/data/results_0.txt'))
names=sorted(set(x['cnm'] for x in d))
print('NC contests',len(names)); print([n for n in names if any(k in n for k in ('US ','NC STATE SENATE','NC HOUSE'))][:12])
print('NC sample', [x for x in d if x['cnm'].startswith('NC HOUSE OF REPRESENTATIVES DISTRICT 105')])
print('NC keys', sorted(d[0].keys()))
for f in ['Congressional','Legislative','AllState','AllStateExceptLocal']:
    t=raw(f'https://results.vote.wa.gov/results/20241105/export/20241105_{f}.csv'); print('\nWA',f,t[:300])
t=raw('https://results.vote.wa.gov/results/20241105/export/20241105_Congressional.csv'); print([l for l in t.splitlines() if 'District 3' in l][:4])
