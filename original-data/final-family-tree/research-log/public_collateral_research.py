from __future__ import annotations
import json, re, time
from pathlib import Path
from urllib.parse import quote, urlparse
import requests
from bs4 import BeautifulSoup

queries = [
    {
        'id':'Q1','query':'"Anne Rives Muller" obituary','target':['anne','rives','muller'],
        'relatives':['philip','gwen','gwendolyn','charles','bruce','jan']
    },
    {
        'id':'Q2','query':'"Philip Brooks McCormick" obituary','target':['philip','brooks','mccormick'],
        'relatives':['anne','gwen','gwendolyn','charles','sandy','ross','tina']
    },
    {
        'id':'Q3','query':'"Gwendolyn McCormick Hull"','target':['gwendolyn','mccormick','hull'],
        'relatives':['anne','philip','charles','carey','mark','jim']
    },
    {
        'id':'Q4','query':'"Mary Gene Muller Chaffee" obituary','target':['mary','gene','chaffee'],
        'relatives':['arthur','jane','linda','lori','james']
    },
    {
        'id':'Q5','query':'"Jane Muller Swick" obituary','target':['jane','muller','swick'],
        'relatives':['arthur','mary','kathy','john','susan','patti']
    },
    {
        'id':'Q6','query':'"Bruce Muller" "Jan Vollmer"','target':['bruce','muller'],
        'relatives':['jan','arthur','anne','vollmer']
    },
    {
        'id':'Q7','query':'"Arthur Herman Muller" "Elma Lee"','target':['arthur','herman','muller'],
        'relatives':['elma','mary','jane','arthur']
    },
    {
        'id':'Q8','query':'"Charles McCormick" "Judy McCormick" obituary California','target':['charles','mccormick'],
        'relatives':['judy','anne','philip','gwen','gwendolyn']
    },
]

headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122 Safari/537.36'}
s=requests.Session(); s.headers.update(headers)

def clean_text(html:str)->str:
    soup=BeautifulSoup(html,'html.parser')
    for tag in soup(['script','style','noscript','svg']): tag.decompose()
    return re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).lower()

def bing_results(query:str):
    url='https://www.bing.com/search?q='+quote(query)
    r=s.get(url,timeout=25)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    out=[]
    for li in soup.select('li.b_algo'):
        a=li.select_one('h2 a')
        if not a: continue
        href=a.get('href','')
        title=a.get_text(' ',strip=True)
        sn=li.select_one('.b_caption p')
        snippet=sn.get_text(' ',strip=True) if sn else ''
        out.append({'title':title,'url':href,'snippet':snippet})
        if len(out)>=12: break
    return out

bad_domains={'facebook.com','linkedin.com','pinterest.com','instagram.com','youtube.com','tiktok.com'}
log=[]
verified=[]
for q in queries:
    rec={'id':q['id'],'query':q['query'],'results':[]}
    try:
        results=bing_results(q['query'])
    except Exception as e:
        rec['error']=repr(e); log.append(rec); continue
    for item in results:
        u=item['url']; domain=urlparse(u).netloc.lower().removeprefix('www.')
        if any(domain.endswith(x) for x in bad_domains):
            continue
        page_text=''
        status=None
        try:
            rr=s.get(u,timeout=20,allow_redirects=True)
            status=rr.status_code
            if 'text/html' in rr.headers.get('content-type','') and len(rr.text)<8_000_000:
                page_text=clean_text(rr.text)[:300000]
                u=rr.url
                domain=urlparse(u).netloc.lower().removeprefix('www.')
        except Exception:
            pass
        hay=(' '.join([item['title'],item['snippet'],page_text])).lower()
        target_hits=sum(1 for t in q['target'] if t in hay)
        relative_hits=[r for r in q['relatives'] if r in hay]
        exact=' '.join(q['target']) in hay
        score=target_hits*3 + len(set(relative_hits))*2 + (5 if exact else 0)
        enriched={**item,'url':u,'domain':domain,'status':status,'target_hits':target_hits,'relative_hits':sorted(set(relative_hits)),'score':score}
        rec['results'].append(enriched)
        # Only call verified if all target tokens occur and at least one relative or authoritative obituary/genealogy domain.
        auth=any(x in domain for x in ['legacy.com','newspapers.com','findagrave.com','familysearch.org','loc.gov','obituaries','tributes','funeral'])
        if target_hits==len(q['target']) and (relative_hits or auth) and status==200 and score>=11:
            verified.append({'query_id':q['id'],**enriched})
    rec['results']=sorted(rec['results'],key=lambda x:x['score'],reverse=True)
    log.append(rec)
    time.sleep(.5)

out={'queries':log,'verified_candidates':sorted(verified,key=lambda x:x['score'],reverse=True)}
Path('/mnt/data/Fredric_Vollmer_Maternal_Public_Record_Search_Log.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
# Human-readable summary for package.
lines=['PUBLIC RECORD SEARCH LOG — COLLATERAL HOUSEHOLDS','']
for rec in log:
    lines.append(f"{rec['id']}: {rec['query']}")
    if rec.get('error'):
        lines.append('  ERROR '+rec['error'])
    for r in rec.get('results',[])[:5]:
        lines.append(f"  score {r['score']:>2} | {r['title']} | {r['url']}")
        lines.append(f"       target hits={r['target_hits']} relatives={','.join(r['relative_hits']) or '-'} status={r['status']}")
    lines.append('')
lines.append('VERIFIED-CANDIDATE THRESHOLD RESULTS')
for r in out['verified_candidates']:
    lines.append(f"  {r['query_id']} score {r['score']} | {r['title']} | {r['url']}")
Path('/mnt/data/Fredric_Vollmer_Maternal_Public_Record_Search_Log.txt').write_text('\n'.join(lines),encoding='utf-8')
print('queries',len(log),'verified',len(verified))
