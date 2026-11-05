#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
using namespace std;
const double PI=3.141592653589793;
struct V{double x,y,z;V operator+(V b)const{return{x+b.x,y+b.y,z+b.z};}V operator-(V b)const{return{x-b.x,y-b.y,z-b.z};}V operator*(double s)const{return{x*s,y*s,z*s};}V operator/(double s)const{return (*this)*(1/s);}};
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}V cross(V a,V b){return{a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}V unit(V a){return a/sqrt(max(1e-15,dot(a,a)));}
V mix(V a,V b,double t){return a*(1-t)+b*t;}double clamp(double x,double a=0,double b=1){return max(a,min(b,x));}double smooth(double t){t=clamp(t);return t*t*(3-2*t);}double rnd(int a){double x=sin(a*78.233+3.4)*43758.5453;return x-floor(x);}
struct Tri{V a,b,c,col;double metal;bool shadow;};vector<Tri> tris;
void tri(V a,V b,V c,V col,double m=0,bool sh=true){tris.push_back({a,b,c,col,m,sh});}
void quad(V a,V b,V c,V d,V col,double m=0,bool sh=true){tri(a,b,c,col,m,sh);tri(a,c,d,col,m,sh);}
V rotZ(V p,double a){return{p.x*cos(a)-p.y*sin(a),p.x*sin(a)+p.y*cos(a),p.z};}
V rotY(V p,double a){return{p.x*cos(a)+p.z*sin(a),p.y,-p.x*sin(a)+p.z*cos(a)};}
void box(V c,V size,V col,double rz=0,double ry=0,double metal=0){
 V p[8];for(int k=0;k<8;k++){V a={(k&1?.5:-.5)*size.x,(k&2?.5:-.5)*size.y,(k&4?.5:-.5)*size.z};p[k]=c+rotY(rotZ(a,rz),ry);}
 int f[6][4]={{0,2,3,1},{4,5,7,6},{0,4,6,2},{1,3,7,5},{0,1,5,4},{2,6,7,3}};
 for(auto &q:f)quad(p[q[0]],p[q[1]],p[q[2]],p[q[3]],col,metal);
}
void cylinder(V c,double radius,double length,V col,int n=24,double spin=0,double metal=0){
 for(int k=0;k<n;k++){double a=2*PI*k/n+spin,b=2*PI*(k+1)/n+spin;V p={c.x+radius*cos(a),c.y+radius*sin(a),c.z-length*.5},q={c.x+radius*cos(b),c.y+radius*sin(b),c.z-length*.5};V r=q+V{0,0,length},s=p+V{0,0,length};quad(p,q,r,s,col,metal);tri(c+V{0,0,-length*.5},q,p,col*.82,metal);tri(c+V{0,0,length*.5},s,r,col*.82,metal);}
}
void rod(V a,V b,double r,V col,int n=8){V axis=unit(b-a),u=unit(cross(axis,abs(axis.y)<.9?V{0,1,0}:V{1,0,0})),v=cross(axis,u);
 for(int k=0;k<n;k++){double x=k*2*PI/n,y=(k+1)*2*PI/n;V p=(u*cos(x)+v*sin(x))*r,q=(u*cos(y)+v*sin(y))*r;quad(a+p,a+q,b+q,b+p,col,.2);}}
void lump(V c,V r,V col,int seed,int n=10,int rings=5){
 for(int j=0;j<rings;j++)for(int k=0;k<n;k++){
  auto pt=[&](int jj,int kk){double a=2*PI*(kk%n)/n,b=PI*jj/rings;double noise=.88+.2*rnd(seed+jj*n+kk%n);return c+V{sin(b)*cos(a)*r.x,cos(b)*r.y,sin(b)*sin(a)*r.z}*noise;};
  V p=pt(j,k),q=pt(j,k+1),r1=pt(j+1,k+1),s=pt(j+1,k);V cc=col*(.85+.22*rnd(seed+j*n+k));quad(p,q,r1,s,cc);
 }
}
void crystal(V c,double h,double r,double angle){
 V col={.91,.69,.20};int n=6;
 for(int k=0;k<n;k++){double a=2*PI*k/n+angle,b=2*PI*(k+1)/n+angle;V p=c+V{cos(a)*r,0,sin(a)*r},q=c+V{cos(b)*r,0,sin(b)*r};V p1=p+V{.03,h*.74,.01},q1=q+V{.03,h*.74,.01},tip=c+V{.04,h,.015};quad(p,q,q1,p1,col*(k%2?.85:1.14),.35);tri(p1,q1,tip,{1.0,.82,.36},.5);}
}
void rockHalf(V c,int sign,double split){
 int n=18,m=12;V color={.23,.145,.095};
 auto trans=[&](V p){return c+V{sign*.28*split,.015*split,0}+rotZ(p,-sign*.17*split);};
 auto pt=[&](int j,int k){double v=PI*j/m,u=-PI*.5+PI*k/n;double rough=.96+.045*sin(j*7+k*13);return trans(V{sign*.4*sin(v)*cos(u),.265*cos(v),.32*sin(v)*sin(u)}*rough);};
 for(int j=0;j<m;j++)for(int k=0;k<n;k++){V col=color*(.86+.22*rnd(j*33+k));quad(pt(j,k),pt(j+1,k),pt(j+1,k+1),pt(j,k+1),col);}
 for(int k=0;k<36;k++){double a=2*PI*k/36,b=2*PI*(k+1)/36;tri(trans({0,0,0}),trans({0,.25*cos(a),.30*sin(a)}),trans({0,.25*cos(b),.30*sin(b)}),{.35,.22,.095},.05);}
}
double height(double x,double z){return .012*sin(x*3+z*2)+.009*cos(z*7+x);}
vector<Tri> ground;
void buildGround(){tris.clear();
 int nx=70,nz=70;double st=.55;
 for(int iz=-20;iz<nz-20;iz++)for(int ix=-nx/2;ix<nx/2;ix++){
  auto p=[&](int xx,int zz){double x=xx*st,z=zz*st;return V{x,height(x,z),z};};
  V col={.43,.235,.145};col=col*(.86+.24*rnd(ix*17+iz*113));quad(p(ix,iz),p(ix+1,iz),p(ix+1,iz+1),p(ix,iz+1),col);
 }
 for(int i=0;i<270;i++){
  double x=rnd(i*7)*18-9,z=rnd(i*7+1)*13-5;if(abs(x-.9)<.7&&abs(z+.7)<.7)continue;
  double s=.018+pow(rnd(i*7+2),3)*.12;lump({x,s*.3,z},{s,s*.55,s*.8},{.29,.18,.13},i,6,3);
 }
 for(int i=0;i<19;i++){
  double x=i*2.4-20,z=12+rnd(i*33)*6;double h=1.1+rnd(i*77)*3;
  lump({x,h*.15,z},{2.8,h,2.3},{.32,.22,.19},i+400,8,3);
 }
 ground=tris;
}
void scene(double t){tris=ground;
 double x=t<3.6?(-3.0+3.0*smooth(t/3.6)):(2.4*smooth((t-3.6)/3.4));double bump=max(0.,1-abs(t-3.62)/.25)*.11;
 V cream={.78,.77,.67},metal={.47,.51,.49},dark={.065,.075,.085},gold={.56,.36,.10};
 for(double side:{-.64,.64})for(double ax:{-.86,0.,.86}){
  V w={x+ax,.34+(ax>.5?bump:0),side};rod({x+ax*.7,.83,side*.7},w,.035,metal);
  cylinder(w,.33,.27,dark,32,-x/.33,.05);double outer=side+(side<0?-.15:.15);cylinder({w.x,w.y,outer},.225,.024,{.42,.44,.40},24,-x/.33,.4);cylinder({w.x,w.y,outer+(side<0?-.02:.02)},.09,.03,{.70,.64,.43},16);
  for(int k=0;k<16;k++){double a=k*2*PI/16-x/.33;V c=w+V{cos(a)*.327,sin(a)*.327,0};box(c,{.075,.032,.29},{.10,.115,.12},a+PI/2);}
  for(int k=0;k<8;k++){double a=k*PI/4-x/.33;rod({w.x,w.y,outer},{w.x+cos(a)*.205,w.y+sin(a)*.205,outer},.014,{.70,.72,.65},5);}
 }
 box({x,.96+bump*.45,0},{2.05,.38,1.12},cream,0,0,.2);box({x,1.17+bump*.45,0},{1.88,.08,1.03},{.89,.86,.73},0,0,.12);
 box({x-.7,1.34,0},{.39,.3,.67},gold,0,0,.25);box({x+.48,1.3,0},{.38,.24,.50},cream);
 for(int k=0;k<7;k++)box({x-.75+k*.23,.97,-.569},{.11,.1,.02},{.14,.17,.16});
 for(double z:{-.48,.48})rod({x-.87,1.23,z},{x+.87,1.23,z},.024,metal);
 rod({x+.45,1.35,0},{x+.45,2.1,0},.055,cream,10);box({x+.49,2.16,-.02},{.5,.23,.28},cream,0,0,.2);
 for(double xx:{-.13,.13})cylinder({x+.49+xx,2.16,-.18},.072,.075,{.035,.065,.075},20,0,.7);
 rod({x-.68,1.48,.15},{x-.85,2.02,.15},.012,metal);lump({x-.85,2.02,.15},{.035,.035,.035},gold,35,6,3);
 double arm=smooth((t-4.5)/.7);V a1={x+.95,.95,-.35},a2={x+1.30,.75+arm*.16,-.54},a3={x+1.55,.58+arm*.22,-.75};rod(a1,a2,.045,cream);rod(a2,a3,.035,metal);cylinder(a3,.07,.10,dark,12);
 // Split rock halves are real mesh objects; their transforms reverse with world time.
 double split=smooth((t-3.67)/.46);V rock={.92,.19,-.76};
 for(int sign:{-1,1})rockHalf(rock,sign,split);
 if(split>.02)for(int j=0;j<11;j++){double xx=(rnd(j*5)-.5)*.24,zz=(rnd(j*5+1)-.5)*.30;crystal({rock.x+xx,.045,rock.z+zz},(.18+.22*rnd(j*5+2))*split,.035+.02*rnd(j+90),j*.7);}
 if(t>3.67&&t<4.9){double q=(t-3.67)/1.23;for(int j=0;j<23;j++){double a=j*2.399,s=.2+.65*rnd(j+90);V c=rock+V{cos(a)*q*s,sin(PI*q)*(.12+.35*rnd(j+18)),sin(a)*q*s};double r=.018*(1-q)+.004;lump(c,{r,r,r},{.56,.37,.23},j+9,5,2);}}
}
struct Camera{V eye,target;double fov;};
struct P{double x,y,z;};
V light=unit({-3,7,-4});
int SW=1024;vector<float> shadow;
V lu,lv;double lightScale=40;
P lightP(V p){return{dot(p,lu)*lightScale+SW*.5,SW*.5-dot(p,lv)*lightScale,dot(p,light)};}
double edge(P a,P b,double x,double y){return(x-a.x)*(b.y-a.y)-(y-a.y)*(b.x-a.x);}
void shadowTri(const Tri&t){if(!t.shadow)return;P a=lightP(t.a),b=lightP(t.b),c=lightP(t.c);double ar=edge(a,b,c.x,c.y);if(abs(ar)<1e-6)return;
 int x0=max(0,(int)floor(min({a.x,b.x,c.x}))),x1=min(SW-1,(int)ceil(max({a.x,b.x,c.x}))),y0=max(0,(int)floor(min({a.y,b.y,c.y}))),y1=min(SW-1,(int)ceil(max({a.y,b.y,c.y})));
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){double u=edge(b,c,x+.5,y+.5)/ar,v=edge(c,a,x+.5,y+.5)/ar,w=1-u-v;if(u<0||v<0||w<0)continue;float z=u*a.z+v*b.z+w*c.z;float &s=shadow[y*SW+x];if(z>s)s=z;}}
int W=1280,H=720;vector<float>depth;vector<unsigned char>rgb;
double shadowAt(V p){P s=lightP(p);int x=(int)s.x,y=(int)s.y;if(x<1||y<1||x>=SW-1||y>=SW-1)return 1;double a=0;for(int j=-1;j<=1;j++)for(int i=-1;i<=1;i++)a+=(s.z+.11>=shadow[(y+j)*SW+x+i]?1.:.22);return a/9;}
void render(Camera camera,double time){
 shadow.assign(SW*SW,-1e8);for(auto&t:tris)shadowTri(t);
 V fw=unit(camera.target-camera.eye),right=unit(cross(fw,{0,1,0})),up=cross(right,fw);double focal=W/(2*tan(camera.fov*PI/360));
 auto project=[&](V p){V q=p-camera.eye;double z=dot(q,fw);return P{W*.5+dot(q,right)*focal/z,H*.5-dot(q,up)*focal/z,z};};
 depth.assign(W*H,1e9);rgb.resize(W*H*3);
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  double v=(double)y/H;V col=mix({.075,.13,.19},{.63,.37,.24},pow(v,.75));double vig=1-.17*(pow((x-W*.5)/(W*.7),2)+pow((y-H*.5)/(H*.9),2));int k=(y*W+x)*3;rgb[k]=255*sqrt(col.x)*vig;rgb[k+1]=255*sqrt(col.y)*vig;rgb[k+2]=255*sqrt(col.z)*vig;
 }
 for(auto&t:tris){P a=project(t.a),b=project(t.b),c=project(t.c);if(min({a.z,b.z,c.z})<.075)continue;double ar=edge(a,b,c.x,c.y);if(abs(ar)<.01)continue;
 int x0=max(0,(int)floor(min({a.x,b.x,c.x}))),x1=min(W-1,(int)ceil(max({a.x,b.x,c.x}))),y0=max(0,(int)floor(min({a.y,b.y,c.y}))),y1=min(H-1,(int)ceil(max({a.y,b.y,c.y})));if(x0>x1||y0>y1)continue;
 V n=unit(cross(t.b-t.a,t.c-t.a));V center=(t.a+t.b+t.c)/3;if(dot(n,camera.eye-center)<0)n=n*-1;double diffuse=max(0.,dot(n,light));V view=unit(camera.eye-center);V half=unit(light+view);double spec=pow(max(0.,dot(n,half)),20)*t.metal*.65;
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){
  double u=edge(b,c,x+.5,y+.5)/ar,v=edge(c,a,x+.5,y+.5)/ar,w=1-u-v;if(u<0||v<0||w<0)continue;
  double iz=u/a.z+v/b.z+w/c.z,z=1/iz;int k=y*W+x;if(z>=depth[k])continue;depth[k]=z;
  V p=(t.a*(u/a.z)+t.b*(v/b.z)+t.c*(w/c.z))*z;double sh=shadowAt(p);double ambient=.19+.10*max(0.,n.y);
  double tex=1;if(t.metal<.1){double a=sin(p.x*213.7+p.y*137.2+p.z*198.3)*43758.5453;tex=.91+.16*(a-floor(a));}
  V cc=t.col*tex;V col=cc*ambient+V{cc.x*1.16,cc.y*.96,cc.z*.76}*(diffuse*sh)+V{1.,.85,.58}*(spec*sh);
  double fog=clamp((z-9)/50,0,.55);col=mix(col,{.43,.29,.24},fog);
  double grain=(rnd(x*17+y*113+(int)(time*30)*23)-.5)*.009;double vign=1-.15*(pow((x-W*.5)/(W*.7),2)+pow((y-H*.5)/(H*.9),2));
  for(int ch=0;ch<3;ch++){double val=ch==0?col.x:ch==1?col.y:col.z;val=pow(clamp(val),.47)*vign+grain;rgb[k*3+ch]=(unsigned char)(clamp(val)*255);}
 }
 }
}
double worldTime(double t){if(t<7.7)return t;if(t<9.2)return 7.6-(7.6-2.4)*smooth((t-7.7)/1.5);if(t<12.5)return 3.25+(4.5-3.25)*(t-9.2)/3.3;return 6.8;}
Camera cam(double t,double wt){
 double x=wt<3.6?(-3+3*smooth(wt/3.6)):(2.4*smooth((wt-3.6)/3.4));
 if(t<2.2)return{{x+3.8,2.6,-5.5},{x+.1,.85,0},43};
 if(t<4.2)return{{1.8,.62,-2.6},{.65,.32,-.64},48};
 if(t<5.7)return{{1.65,.68,-2.05},{.92,.20,-.76},40};
 if(t<7.7){double q=smooth((t-5.7)/2);return{{1.6*cos(q*.8)+.9,.8,-.76-1.6*sin(q*.8)-1.0},{.92,.24,-.76},36};}
 if(t<9.2)return{{3.7,2.4,-4.8},{.45,.85,-.1},43};
 if(t<10.7)return{{1.6,.48,-2.25},{.87,.27,-.7},42};
 if(t<12.5)return{{.02,.8,-2.1},{.92,.20,-.76},39};
 double q=smooth((t-12.5)/2.5);return{{.9+1.2*cos(.3+q*.8),.55+q*.22,-.76-1.2*sin(.3+q*.8)},{.92,.20,-.76},34};
}
int main(int argc,char**argv){lu=unit(cross(light,{0,1,0}));lv=cross(lu,light);buildGround();
 int first=argc>1?atoi(argv[1]):0,last=argc>2?atoi(argv[2]):450;bool ppm=argc>3;
 for(int i=first;i<last;i++){double t=i/30.;double wt=worldTime(t);scene(wt);render(cam(t,wt),t);if(ppm)printf("P6\n%d %d\n255\n",W,H);fwrite(rgb.data(),1,rgb.size(),stdout);if(i%30==0)fprintf(stderr,"frame %d\n",i);}
}
