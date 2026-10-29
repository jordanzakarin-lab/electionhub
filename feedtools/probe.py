import urllib.request, json
H={'User-Agent':'Mozilla/5.0 (ElectionHub results bot; jordanzakarin@gmail.com)','Accept':'application/json,text/plain,*/*'}
def get(u,n=500):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30); b=r.read()
        print(f'\n### {u}\n status={r.status} type={r.headers.get("content-type")} bytes={len(b)}'); t=b.decode('utf-8','replace'); print(t[:n]); return t
    except Exception as e: print(f'\n### {u}\n ERROR {e}'); return ''
for f in ['ushouse.txt','ussenate.txt','LegislativeByDistrict.txt','stsenate.txt','sthouse.txt','StateRepresentatives.txt']:
    get('https://electionresultsfiles.sos.mn.gov/20261103/'+f,300)
for eid in ['126592','122598']:
    v=get(f'https://results.enr.clarityelections.com/CO/{eid}/current_ver.txt',100).strip()
    if v:
        get(f'https://results.enr.clarityelections.com/CO/{eid}/{v}/json/en/summary.json',800)
        get(f'https://results.enr.clarityelections.com/CO/{eid}/{v}/json/en/electionsettings.json',400)
        get(f'https://results.enr.clarityelections.com/CO/{eid}/{v}/json/ALL.json',300)
