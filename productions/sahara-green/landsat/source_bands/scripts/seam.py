import sys, json, numpy as np
from PIL import Image, ImageDraw
sys.argv=['x']; src=open('/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/acq/process.py').read().split("def main")[0]
ns={'__name__':'p'}; exec(src,ns); pcorr,grad=ns['pcorr'],ns['grad']
O='/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/acq/out/'
gW=json.load(open(O+'TW_report.json'))['grid']; gE=json.load(open(O+'TE_report.json'))['grid']
cx=int(round((gE['x0']-gW['x0'])/30)); ry=int(round((gW['y_top']-gE['y_top'])/30)); assert abs((gE['x0']-gW['x0'])/30-cx)<1e-6 and abs((gW['y_top']-gE['y_top'])/30-ry)<1e-6
Wd=np.load(O+'TW_refl_f16.npz'); Ed=np.load(O+'TE_refl_f16.npz')
UW=cx+gE['width']; H=max(gW['height'],ry+gE['height'])  # union size; E rows start at -ry relative to W? E y_top lower => E row = W row - ry
print('offsets cx',cx,'ry',ry,'union',UW,H)
# E top is ry px BELOW W top (ry= (W.ytop-E.ytop)/30 = -32?) 
res={'grid_union':{'epsg':32636,'x0':gW['x0'],'y_top':gW['y_top'],'width':UW,'height':H,'offset_E_px':[cx,ry]},'years':{}}
yrs=['1999','2002','2011','2021']
mos={}
for y in yrs:
    w=Wd[y].astype(np.float32); e=Ed[y].astype(np.float32); vw=Wd['valid_'+y]; ve=Ed['valid_'+y]
    ey0=ry
    U=np.full((H,UW,3),np.nan,np.float32); WT=np.zeros((H,UW),np.float32)
    # weights: feather in overlap columns [cx, gW.width)
    ov0,ov1=cx,gW['width']
    def put(arr,v,x0,y0,wx):
        h,wd=v.shape; wgt=(v*wx[None,:]).astype(np.float32)
        sl=(slice(y0,y0+h),slice(x0,x0+wd))
        a=np.nan_to_num(arr,nan=0)*wgt[...,None]
        U[sl]=np.where(np.isnan(U[sl]),0,U[sl])+a; WT[sl]+=wgt
    wxW=np.ones(gW['width'],np.float32); wxW[ov0:]=np.linspace(1,0,ov1-ov0)
    wxE=np.ones(gE['width'],np.float32); wxE[:ov1-ov0]=np.linspace(0,1,ov1-ov0)
    put(w,vw,0,0,wxW); put(e,ve,cx,ey0,wxE)
    M=np.where(WT[...,None]>0,U/np.maximum(WT[...,None],1e-9),np.nan); mos[y]=M
    # overlap analysis: W cols ov0.., rows ey0..; E cols 0..ov1-ov0
    nrows=min(gW['height']-ey0,gE['height'])
    wo=w[ey0:ey0+nrows,ov0:ov1]; eo=e[:nrows,:ov1-ov0]; m=vw[ey0:ey0+nrows,ov0:ov1]&ve[:nrows,:ov1-ov0]
    gw=grad(np.nan_to_num(wo[...,0]))*m; ge=grad(np.nan_to_num(eo[...,0]))*m
    dx,dy,snr=pcorr(ge,gw)
    d=[float(np.nanmedian((eo[...,c]-wo[...,c])[m])) for c in range(3)]
    rr=[float(np.nanmedian((eo[...,c]/wo[...,c])[m])) for c in range(3)]
    res['years'][y]={'overlap_px':[int(wo.shape[1]),int(wo.shape[0])],'valid_both_fraction':round(float(m.mean()),4),'shift_px_dx_dy':[round(dx,3),round(dy,3)],'snr':round(snr,1),
      'median_E_minus_W_reflectance_rgb':[round(v,4) for v in d],'median_E_over_W_ratio_rgb':[round(v,4) for v in rr],'dates':{'W':[s['date'] for s in json.load(open(O+'TW_report.json'))['scenes'] if s['label']==y][0],'E':[s['date'] for s in json.load(open(O+'TE_report.json'))['scenes'] if s['label']==y][0]}}
    print(y,res['years'][y])
json.dump(res,open(O+'toshka_seam_report.json','w'),indent=1)
# common stretch over union, gamma 1/1.6, saved previews (quarter size)
pool=np.concatenate([mos[y][np.isfinite(mos[y][...,0])][::200] for y in yrs]); lo=np.percentile(pool,1,axis=0); hi=np.percentile(pool,99.5,axis=0)
res['stretch_union']={'lo':[round(float(x),4) for x in lo],'hi':[round(float(x),4) for x in hi]}
json.dump(res,open(O+'toshka_seam_report.json','w'),indent=1)
def rgb8(M): x=np.clip((np.nan_to_num(M)-lo)/(hi-lo),0,1)**(1/1.6); x[~np.isfinite(M[...,0])]=0; return (x*255+.5).astype(np.uint8)
tiles=[]
for y in yrs:
    im=Image.fromarray(rgb8(mos[y])); im.thumbnail((700,700)); d=ImageDraw.Draw(im); d.text((6,6),f'Toshka mosaic {y} (W {res["years"][y]["dates"]["W"]} / E {res["years"][y]["dates"]["E"]})',fill=(255,255,0)); tiles.append(im)
w_,h_=tiles[0].size; sh=Image.new('RGB',(w_*2,h_*2))
for i,t in enumerate(tiles): sh.paste(t,((i%2)*w_,(i//2)*h_))
sh.save(O+'toshka_mosaic_2x2.jpg',quality=82)
# seam crops (full res 600px wide around the seam centre, middle rows)
cxm=(cx+gW['width'])//2; r0=1100
cr=[]
for y in yrs:
    c=Image.fromarray(rgb8(mos[y])[r0:r0+500,cxm-300:cxm+300]); ImageDraw.Draw(c).text((4,4),y,fill=(255,255,0)); cr.append(c)
s2=Image.new('RGB',(1200,1000))
for i,c in enumerate(cr): s2.paste(c,((i%2)*600,(i//2)*500))
s2.save(O+'toshka_seam_crops.jpg',quality=85)
print('ok')
