import urllib.request, re, json, sys
H={'User-Agent':'Mozilla/5.0 (ElectionHub results bot; jordanzakarin@gmail.com)'}
def get(u, n=600):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); b=r.read()
        print(f'\n### {u}\n status={r.status} type={r.headers.get("content-type")} bytes={len(b)}')
        t=b.decode('utf-8','replace'); print(t[:n]); return t
    except Exception as e: print(f'\n### {u}\n ERROR {e}'); return ''
t=get('https://er.ncsbe.gov/enr/20241105/data/results_0.txt',800)
try:
    d=json.loads(t); print('NC records',len(d)); print([x for x in d if 'DISTRICT 01' in x.get('cnm','') and 'HOUSE' in x.get('cnm','')][:3])
except Exception as e: print('nc parse',e)
get('https://er.ncsbe.gov/enr/20261103/data/results_0.txt',200)
get('https://electionresultsfiles.sos.mn.gov/20241105/',1500)
get('https://electionresultsfiles.sos.mn.gov/20241105/ushouse.txt',600)
get('https://electionresultsfiles.sos.mn.gov/20241105/LegislativeByDistrict.txt',600)
get('https://electionresultsfiles.sos.mn.gov/20261103/',600)
t=get('https://results.enr.clarityelections.com/CO/',1500)
print('CO links:',sorted(set(re.findall(r'/CO/(\d{5,7})',t)))[:40])
get('https://results.vote.wa.gov/results/20241105/export/20241105_AllState.csv',800)
get('https://results.vote.wa.gov/results/20241105/export/20241105_Legislative.csv',400)
get('https://results.vote.wa.gov/results/20261103/export/20261103_AllState.csv',200)
get('https://www.electionreturns.pa.gov/',800)
get('https://www.electionreturns.pa.gov/api/ElectionReturn/GetElectionsList',600)
get('https://results.arizona.vote/',800)
get('https://silverstateelection.nv.gov/',600)
