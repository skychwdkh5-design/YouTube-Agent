import sys,json,re
sys.path.insert(0,'/home/user/YouTube-Agent/.claude/skills/yt-satellite')
import usgs_m2m as u
S='/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad'
all_=json.load(open(S+'/ls/all.json'))
SCENES=[ # (group, label, displayId or prefix)
('EO','1984','LT05_L1TP_177044_19840826_20200918_02_T1'),
('EO','2000','LT05_L1TP_177044_20000111_20200907_02_T1'),
('EO','2010','LT05_L1TP_177044_20100122_20200825_02_T1'),
('EO','2016','LC08_L1TP_177044_20160107_20200907_02_T1'),
('EO','2024','LC09_L1TP_177044_20240105_20240105_02_T1'),
('TW','1999','LT05_L1TP_176044_19990101_20200908_02_T1'),
('TW','2002','LT05_L1TP_176044_20020109_20200905_02_T1'),
('TW','2011','LT05_L1TP_176044_20110102_20200823_02_T1'),
('TW','2021','LC08_L1TP_176044_20211113_20211125_02_T1'),
('TE','1999','LT05_L1TP_175044_19990110_20200908_02_T1'),
('TE','2002','LT05_L1TP_175044_20020118_20200905_02_T1'),
('TE','2011','LT05_L1TP_175044_20110111_20200823_02_T1'),
('TE','2021','LC08_L1TP_175044_20211106_20211117_02_T1')]
out=[]
with u.M2M() as m:
    for g,l,sid in SCENES:
        ent=all_[sid]['entityId']; ds='landsat_tm_c2_l1' if sid.startswith('LT05') else 'landsat_ot_c2_l1'
        rows=m.call("download-options",{"datasetName":ds,"entityIds":[ent]}) or []
        band=[r for r in rows if r.get('productName')=='Landsat Collection 2 Level-1 Band File' and r.get('available')]
        if not band: out.append({'group':g,'label':l,'displayId':sid,'entityId':ent,'error':'no band-file option'});continue
        b=band[0]; sec=b.get('secondaryDownloads') or []
        files={}
        for s in sec:
            suf=s['displayId'].replace(sid+'_','')
            files[suf]={'entityId':s['entityId'],'productId':s.get('id'),'filesize':s.get('filesize'),'checksum':s.get('checksum') or s.get('sha512') ,'keys':[k for k in s.keys()]}
        out.append({'group':g,'label':l,'displayId':sid,'entityId':ent,'dataset':ds,'bandProductId':b.get('id'),'files':files})
json.dump(out,open(S+'/acq/options.json','w'),indent=1)
print('ok',len(out))
