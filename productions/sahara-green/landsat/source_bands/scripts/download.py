import sys,json,os,time,hashlib
sys.path.insert(0,'/home/user/YouTube-Agent/.claude/skills/yt-satellite')
import usgs_m2m as u
S='/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad'
ROOT=S+'/landsat_work/ep001/src_bands'
BUDGET=2_000_000_000
o=json.load(open(S+'/acq/options.json'))
TM=['B1.TIF','B2.TIF','B3.TIF','B4.TIF','QA_PIXEL.TIF','MTL.txt']
OL=['B2.TIF','B3.TIF','B4.TIF','B5.TIF','QA_PIXEL.TIF','MTL.txt']
local={('EO','2010'):set(TM),('EO','2024'):{'B4.TIF','B5.TIF','QA_PIXEL.TIF','MTL.txt'}}
LOG=ROOT+'/download_log.json'
os.makedirs(ROOT,exist_ok=True)
log=json.load(open(LOG)) if os.path.exists(LOG) else {'files':[]}
done={(f['displayId'],f['suffix']) for f in log['files'] if f['status']=='ok'}
def sha512(p):
    h=hashlib.sha512()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
plan=[]
for s in o:
    want=TM if s['displayId'].startswith('LT05') else OL
    for w in want:
        if w in local.get((s['group'],s['label']),()) or (s['displayId'],w) in done: continue
        plan.append((s,w))
total=sum(s['files'][w]['filesize'] for s,w in plan); print('to fetch',len(plan),'bytes',total,flush=True)
assert total+sum(f['bytes'] for f in log['files'] if f['status']=='ok')<=BUDGET,'over budget'
spent=0
with u.M2M() as m:
  for sid in dict.fromkeys(s['displayId'] for s,_ in plan):
    items=[(s,w) for s,w in plan if s['displayId']==sid]
    dest=f'{ROOT}/{sid}'; os.makedirs(dest,exist_ok=True)
    label='yt-band-%d'%int(time.time())
    try:
        req=m.call("download-request",{"label":label,"downloads":[{"entityId":s['files'][w]['entityId'],"productId":s['files'][w]['productId']} for s,w in items]}) or {}
        avail=list(req.get('availableDownloads') or [])
        deadline=time.time()+180
        while len([d for d in avail if d.get('url')])<len(items) and time.time()<deadline:
            time.sleep(8); ret=m.call("download-retrieve",{"label":label}) or {}
            avail=list(ret.get('available') or [])
        byent={d['entityId']:d for d in avail if d.get('url')}
        if len(byent)!=len(items): raise SystemExit('%s: URL count %d != %d: stop'%(sid,len(byent),len(items)))
        for s,w in items:
            exp=s['files'][w]; d=byent[exp['entityId']]
            if spent+exp['filesize']>BUDGET: raise SystemExit('budget guard')
            try: r=m._fetch(d['url'],dest,exp['entityId'],100)
            except u.M2MError as e:
                print(sid,w,'FAILED',str(e)[:80],flush=True); log.setdefault('failed',[]).append({'displayId':sid,'suffix':w,'error':str(e)[:120]}); json.dump(log,open(LOG,'w'),indent=1); continue
            spent+=r['bytes']
            final=f'{dest}/{sid}_{w}'
            if r['path']!=final: os.replace(r['path'],final)
            digest=sha512(final); want=exp['checksum'][0]['value'] if exp.get('checksum') else None
            ok=(r['bytes']==exp['filesize']) and (want is None or digest==want)
            log['files'].append({'displayId':sid,'suffix':w,'entityId':exp['entityId'],'productId':exp['productId'],'bytes':r['bytes'],'expected_bytes':exp['filesize'],'sha512':digest,'expected_sha512':want,'status':'ok' if ok else 'MISMATCH','path':final})
            json.dump(log,open(LOG,'w'),indent=1)
            print(sid,w,r['bytes'],'ok' if ok else 'MISMATCH',flush=True)
            if not ok: raise SystemExit('checksum/size mismatch: stop')
    finally:
        print('cleanup',m.cleanup_order(label),flush=True)
print('DONE spent',spent,flush=True)
