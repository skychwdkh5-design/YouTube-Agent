import hashlib, os, requests, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
D=os.path.dirname(os.path.abspath(__file__)); S=requests.Session()
UP={'/cesium/':'https://cdn.jsdelivr.net/npm/cesium@1.120.0/','/gibs/':'https://gibs.earthdata.nasa.gov/'}
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        p=self.path.split('?')[0]
        if p in('/','/index.html'):
            b=open(D+'/index.html','rb').read(); return self.out(200,b,'text/html')
        for k,v in UP.items():
            if p.startswith(k):
                u=v+p[len(k):]; f=D+'/cache/'+hashlib.md5(u.encode()).hexdigest()
                if os.path.exists(f) and os.path.exists(f+'.ct'):
                    d=open(f,'rb').read(); ct=open(f+'.ct').read()
                    return self.out(200,d,ct)
                try: r=S.get(u,timeout=30)
                except Exception as e: return self.out(502,str(e).encode(),'text/plain')
                ct=r.headers.get('content-type','application/octet-stream')
                if r.status_code==200:
                    open(f+'.ct','w').write(ct); tmp=f+'.tmp%d'%os.getpid()+str(id(r)); open(tmp,'wb').write(r.content); os.replace(tmp,f)
                else: sys.stderr.write('%d %s\n'%(r.status_code,u)); sys.stderr.flush()
                return self.out(r.status_code,r.content,ct)
        self.out(404,b'',  'text/plain')
    def out(self,c,b,ct):
        self.send_response(c); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
