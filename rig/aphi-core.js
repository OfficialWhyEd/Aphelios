const D=__DATA__;
const scene=document.getElementById('scene'), stage=document.getElementById('stage'), statoEl=document.getElementById('stato');
const G=D.geo, CX=G.meta.CX, CHIN=G.meta.chin;
function mk(name,ox,oy,z){const g=G[name];const i=new Image();i.src=D.parts[name].src;i.style.left=g.x+'px';i.style.top=g.y+'px';i.style.width=g.w+'px';i.style.height=g.h+'px';i.style.transformOrigin=ox+'px '+oy+'px';i.style.zIndex=z;scene.appendChild(i);return i;}
// pezzi ricavati dalla posa base, alle loro coordinate originali (1024x1024)
// ---- corpo: mesh con ossa e pesi (skinning) in WebGL. Le pieghe sono morbide, niente snodi rigidi ----
const MESH=D.mesh;
// due livelli WebGL: busto+gambe dietro la testa, braccia davanti a tutto (come nei disegni: il braccio alzato passa accanto alla testa)
function makeLayer(z,names){
  const cv=document.createElement('canvas'); cv.width=1536; cv.height=1536; cv.style.cssText=`position:absolute;left:0;top:0;width:1024px;height:1024px;z-index:${z};pointer-events:none`; scene.appendChild(cv);
  // WebGL2 quando c'e': mipmap sulle texture (niente scalettature quando il disegno a 3x viene rimpicciolito) e bordo
  // dell'alpha a soglia morbida (smoothstep su fwidth): la sagoma resta netta come nel disegno, e dove due pezzi si
  // sovrappongono il nero e' pieno, senza cuciture chiare. Se manca WebGL2 si torna al vecchio percorso.
  const gl2=cv.getContext('webgl2',{premultipliedAlpha:false,antialias:true}); const gl=gl2||cv.getContext('webgl',{premultipliedAlpha:false,antialias:true});
  const SK=`vec2 sk(int i,vec2 q){for(int k=0;k<8;k++){if(k==i){return (B[k]*vec3(q,1.0)).xy;}}return q;}
void main(){vec2 q=bw.x*sk(int(bi.x+0.5),p)+bw.y*sk(int(bi.y+0.5),p)+bw.z*sk(int(bi.z+0.5),p)+bw.w*sk(int(bi.w+0.5),p);v=t;gl_Position=vec4(q.x/512.0-1.0,1.0-q.y/512.0,0.0,1.0);}`;
  const VS=gl2?`#version 300 es
in vec2 p;in vec2 t;in vec4 bi;in vec4 bw;uniform mat3 B[8];out vec2 v;
`+SK
              :`attribute vec2 p;attribute vec2 t;attribute vec4 bi;attribute vec4 bw;uniform mat3 B[8];varying vec2 v;
`+SK;
  const FS=gl2?`#version 300 es
precision mediump float;uniform sampler2D T;in vec2 v;out vec4 o;void main(){float a=texture(T,v).a;float w=max(fwidth(a)*0.8,0.02);o=vec4(0.078,0.078,0.078,smoothstep(0.5-w,0.5+w,a));}`
              :`precision mediump float;uniform sampler2D T;varying vec2 v;void main(){vec4 c=texture2D(T,v);gl_FragColor=vec4(0.078,0.078,0.078,c.a);}`;
  function shader(t,src){const sh=gl.createShader(t);gl.shaderSource(sh,src);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS))console.error(gl.getShaderInfoLog(sh));return sh;}
  const prog=gl.createProgram(); gl.attachShader(prog,shader(gl.VERTEX_SHADER,VS)); gl.attachShader(prog,shader(gl.FRAGMENT_SHADER,FS)); gl.linkProgram(prog); gl.useProgram(prog);
  const AT={p:gl.getAttribLocation(prog,'p'),t:gl.getAttribLocation(prog,'t'),bi:gl.getAttribLocation(prog,'bi'),bw:gl.getAttribLocation(prog,'bw')};
  const UB=[]; for(let k=0;k<8;k++) UB.push(gl.getUniformLocation(prog,`B[${k}]`));
  gl.enable(gl.BLEND); gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA); gl.clearColor(0,0,0,0);
  function buf(arr,type){const b=gl.createBuffer();gl.bindBuffer(type||gl.ARRAY_BUFFER,b);gl.bufferData(type||gl.ARRAY_BUFFER,arr,gl.STATIC_DRAW);return b;}
  const L={cv,gl,pieces:[]};
  L.pieces=MESH.pieces.filter(pc=>names.includes(pc.name)).map(pc=>{
    const tex=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,tex); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([20,20,20,0]));
    const im=new Image(); im.onload=()=>{gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);if(gl2){gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);}else{gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);}gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);L.draw();}; im.src=D.parts[pc.tex].src;
    return {tex, n:pc.tris.length, p:buf(new Float32Array(pc.verts)), t:buf(new Float32Array(pc.uv)), bi:buf(new Float32Array(pc.bi)), bw:buf(new Float32Array(pc.bw)), idx:buf(new Uint16Array(pc.tris),gl.ELEMENT_ARRAY_BUFFER)};
  });
  L.draw=function(){ gl.viewport(0,0,cv.width,cv.height); gl.clear(gl.COLOR_BUFFER_BIT);
    boneM.forEach((m,k)=>gl.uniformMatrix3fv(UB[k],false,[m[0],m[1],0, m[2],m[3],0, m[4],m[5],1]));
    for(const pc of L.pieces){ gl.bindTexture(gl.TEXTURE_2D,pc.tex);
      for(const [k,b,sz] of [['p',pc.p,2],['t',pc.t,2],['bi',pc.bi,4],['bw',pc.bw,4]]){gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(AT[k]);gl.vertexAttribPointer(AT[k],sz,gl.FLOAT,false,0,0);}
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,pc.idx); gl.drawElements(gl.TRIANGLES,pc.n,gl.UNSIGNED_SHORT,0); } };
  return L; }
const boneM=MESH.bones.map(()=>[1,0,0,1,0,0]);
const bodyLayer=makeLayer(1,['gamba-sx','gamba-dx','busto']), armLayer=makeLayer(5,['braccio-sx','braccio-dx']);
function drawBody(){ bodyLayer.draw(); armLayer.draw(); }
// matrici affini [a,b,c,d,e,f] come CSS: x'=a x+c y+e, y'=b x+d y+f
const I=[1,0,0,1,0,0];
function mul(m,n){return [m[0]*n[0]+m[2]*n[1], m[1]*n[0]+m[3]*n[1], m[0]*n[2]+m[2]*n[3], m[1]*n[2]+m[3]*n[3], m[0]*n[4]+m[2]*n[5]+m[4], m[1]*n[4]+m[3]*n[5]+m[5]];}
function about(px,py,deg,sx,sy){const r=deg*Math.PI/180,c=Math.cos(r),si=Math.sin(r); const a=c*sx,b=si*sx,cc=-si*sy,d=c*sy; return [a,b,cc,d,px-(a*px+cc*py),py-(b*px+d*py)];}
function tr(x,y){return [1,0,0,1,x,y];}
const BONE={}; MESH.bones.forEach((b,i)=>BONE[b.name]=i);
const boneRot=MESH.bones.map(()=>0);
function setBones(par){ // par[i]={rot,sx,sy,tx,ty}: rotazione e scala attorno al perno. Il figlio eredita posizione del perno e
  // rotazione del genitore, NON la sua scala (cosi' l'allungamento di un osso non deforma quello dopo)
  MESH.bones.forEach((b,i)=>{ const q=par[i]||{}; const rot=q.rot||0, sx=q.sx||1, sy=q.sy||1, tx=q.tx||0, ty=q.ty||0;
    const p=b.pivot; let px=p[0],py=p[1],wr=rot;
    if(b.parent>=0){ const W=boneM[b.parent]; px=W[0]*p[0]+W[2]*p[1]+W[4]; py=W[1]*p[0]+W[3]*p[1]+W[5]; wr+=boneRot[b.parent]; }
    boneRot[i]=wr; const r=wr*Math.PI/180,c=Math.cos(r),si=Math.sin(r);
    const a=c*sx,bb=si*sx,cc=-si*sy,d=c*sy;   // R*S
    boneM[i]=[a,bb,cc,d, px+tx-(a*p[0]+cc*p[1]), py+ty-(bb*p[0]+d*p[1])]; }); }
// la mazza sta nella mano destra: segue l'osso dell'avambraccio (matrice CSS)
const gA=G['avambraccio-dx'];
function cssFollow(el,m,ox,oy){ // el ha transform-origin (ox,oy) in coordinate scena
  const X=m[0]*ox+m[2]*oy+m[4]-ox, Y=m[1]*ox+m[3]*oy+m[5]-oy; return `matrix(${m[0]},${m[1]},${m[2]},${m[3]},${X},${Y})`; }

const gT=G.testa;
const headWrap=document.createElement('div'); headWrap.style.cssText=`position:absolute;left:${gT.x}px;top:${gT.y}px;width:${gT.w}px;height:${gT.h}px;transform-origin:${CX-gT.x}px ${CHIN-gT.y}px;z-index:4;will-change:transform`; scene.appendChild(headWrap);
const head=new Image(); head.src=D.parts.testa.src; head.style.cssText=`position:absolute;left:0;top:0;width:${gT.w}px;height:${gT.h}px;pointer-events:none`; headWrap.appendChild(head);
const eyesLayer=document.createElement('div'); eyesLayer.style.cssText=`position:absolute;left:0;top:0;width:${gT.w}px;height:${gT.h}px;-webkit-mask-image:url(${D.parts.testa.src});mask-image:url(${D.parts.testa.src});-webkit-mask-size:100% 100%;mask-size:100% 100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;pointer-events:none`; headWrap.appendChild(eyesLayer);
const R=G.testa.w/2, HY=G.testa.y;
// oggetti: la mazza sta nella mano destra (fondo del braccio), impugnatura nell'angolo in basso a destra dell'immagine
const BW=D.parts.mazza.w*0.95, BH=D.parts.mazza.h*0.95, handX=gA.x+gA.w*0.5, handY=gA.y+gA.h*0.9;
const bat=new Image(); bat.src=D.parts.mazza.src; bat.style.cssText=`position:absolute;left:${handX-BW+22}px;top:${handY-BH+22}px;width:${BW}px;height:${BH}px;transform-origin:${BW-22}px ${BH-22}px;opacity:0;pointer-events:none;z-index:5`; scene.appendChild(bat);
function prop(name,x,y,w,ox,oy,z){const o=D.objs[name]; const h=o.h*(w/o.w); const i=new Image(); i.src=o.src; i.style.cssText=`position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;transform-origin:${ox*w}px ${oy*h}px;z-index:${z};opacity:0;pointer-events:none;max-width:none`; scene.appendChild(i); return i;}
const HW=G.testa.w*1.42, TW=G.busto.w;
const cuffie=prop('cuffie',CX-HW/2,G.testa.y+G.testa.h*0.118,HW,0.5,0.5,3);
const nota1=prop('note',CX+250,G.testa.y+40,90,0.5,1,4), nota2=prop('note',CX-330,G.testa.y+120,70,0.5,1,6);
const tazza=prop('tazza-bordo',CX-TW*0.285,G.busto.y+10,TW*0.57,0.5,0.5,6);
const controller=prop('controller-bordo',CX-TW*0.4,G.busto.y+30,TW*0.8,0.5,0.5,6);
const domanda=prop('punto-interrogativo',CX+300,G.testa.y+5,110,0.5,1,6);
const cuore=prop('cuore',CX+300,G.testa.y+40,110,0.5,1,6);
const zeta=prop('zeta',CX+190,G.testa.y+10,100,0.5,1,4), zeta2=prop('zeta',CX+320,G.testa.y+40,70,0.5,1,6);
const stella=prop('stella',CX-380,G.testa.y+30,110,0.5,0.5,6);
// fumetto per parlare (per il cervello AI): testo bianco su nero
const bubble=document.createElement('div'); bubble.style.cssText=`position:absolute;left:${CX+140}px;top:${G.testa.y-40}px;max-width:340px;background:#141414;color:#F3F1EC;font:600 30px/1.25 "IBM Plex Sans",system-ui,sans-serif;padding:18px 24px;border-radius:28px 28px 28px 6px;opacity:0;z-index:7;pointer-events:none;transform-origin:0 100%`; scene.appendChild(bubble);
function say(t,ms=2600){ bubble.textContent=t; gsap.killTweensOf(bubble); gsap.fromTo(bubble,{opacity:0,scale:.6},{opacity:1,scale:1,duration:.25,ease:'back.out(2)'}); gsap.to(bubble,{opacity:0,duration:.3,delay:ms/1000}); }
const cookie=prop('biscotto-bordo',CX-TW*0.21,G.busto.y-10,TW*0.42,0.5,0.5,6);
// occhi: due img separate; il neutro e' ESATTAMENTE quello del disegno
const EL=G['occhio-sx'], ER=G['occhio-dx'];
const EYE_Y=(EL.y+EL.h/2), EYE_DX=((ER.x+ER.w/2)-(EL.x+EL.w/2))/2, EYE_H=EL.h, PHI=Math.asin(EYE_DX/R);
const eyeL=new Image(), eyeR=new Image(); for(const e of [eyeL,eyeR]){e.style.position='absolute';e.style.zIndex=6;e.style.pointerEvents='none';e.style.maxWidth='none';eyesLayer.appendChild(e);}
let eyeName=''; const eyeDim={L:{w:1,h:1},R:{w:1,h:1}};
function setEyes(n){ if(eyeName===n) return; eyeName=n; const l=D.eyes[n+'-sx'], r=D.eyes[n+'-dx'];
  const dim=(e,ref)=> (n==='neutro') ? {w:ref.w,h:ref.h} : {w:EL.w, h:e.h*(EL.w/e.w)};
  eyeDim.L=dim(l,EL); eyeDim.R=dim(r,ER); eyeL.src=l.src; eyeR.src=r.src;
  for(const [e,d] of [[eyeL,eyeDim.L],[eyeR,eyeDim.R]]){ e.style.width=d.w+'px'; e.style.height=d.h+'px'; e.style.left=(-d.w/2)+'px'; e.style.top=(-d.h/2)+'px'; e.style.transformOrigin='50% 50%'; } }
setEyes('neutro');
// ---- pose disegnate: i corpi (testa compresa) presi dalla griglia approvata, con gli occhi separati ----
// ---- pose disegnate: il corpo e' disegnato da un campo di distanza (SDF) e da una posa all'altra SI TRASFORMA
// (morphing della silhouette) invece di scattare. Gli occhi sono pezzi separati dentro una maschera a forma di posa.
const POSE={};
for(const [n,p] of Object.entries(D.poses)){
  const w=document.createElement('div'); w.style.cssText=`position:absolute;left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;z-index:6;opacity:0;pointer-events:none;will-change:transform,opacity;-webkit-mask-image:url(${p.src});mask-image:url(${p.src});-webkit-mask-size:100% 100%;mask-size:100% 100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat`; scene.appendChild(w);
  const byArea=[...p.occhi].sort((a,b)=>b.w*b.h-a.w*a.h).slice(0,2);   // solo i due buchi piu' grandi sono occhi (bocca e sopracciglia restano ferme)
  const eyes=[]; p.occhi.forEach(e=>{const i=new Image(); i.src=e.src; i.style.cssText=`position:absolute;left:${e.x-p.x}px;top:${e.y-p.y}px;width:${e.w}px;height:${e.h}px;transform-origin:50% 50%;max-width:none`; w.appendChild(i); if(byArea.includes(e)) eyes.push(i);});
  POSE[n]={wrap:w,eyes,x:p.x,y:p.y};
}
// livello WebGL del morph: un quadrato 1024 che campiona due SDF e li mescola
const morph=(function(){
  const cv=document.createElement('canvas'); cv.width=1024; cv.height=1024; cv.style.cssText='position:absolute;left:0;top:0;width:1024px;height:1024px;z-index:5;pointer-events:none;transform-origin:512px 985px;visibility:hidden'; scene.appendChild(cv);
  const gl2=cv.getContext('webgl2',{premultipliedAlpha:false,antialias:false}); const gl=gl2||cv.getContext('webgl',{premultipliedAlpha:false,antialias:false});
  const VS=gl2?`#version 300 es
in vec2 p;out vec2 v;void main(){v=vec2(p.x*0.5+0.5,0.5-p.y*0.5);gl_Position=vec4(p,0.0,1.0);}`
             :`attribute vec2 p;varying vec2 v;void main(){v=vec2(p.x*0.5+0.5,0.5-p.y*0.5);gl_Position=vec4(p,0.0,1.0);}`;
  const FS=gl2?`#version 300 es
precision highp float;uniform sampler2D A;uniform sampler2D B;uniform float t;uniform float k;in vec2 v;out vec4 o;
void main(){float a=texture(A,v).r,b=texture(B,v).r;float d=(mix(a,b,t)*255.0-128.0)/k;float w=max(fwidth(d)*0.7,0.01);o=vec4(0.078,0.078,0.078,1.0-smoothstep(-w,w,d));}`
             :`precision highp float;uniform sampler2D A;uniform sampler2D B;uniform float t;uniform float k;varying vec2 v;
void main(){float a=texture2D(A,v).r,b=texture2D(B,v).r;float d=(mix(a,b,t)*255.0-128.0)/k;float al=clamp(0.5-d,0.0,1.0);gl_FragColor=vec4(0.078,0.078,0.078,al);}`;
  function sh(t,src){const x=gl.createShader(t);gl.shaderSource(x,src);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))console.error(gl.getShaderInfoLog(x));return x;}
  const pr=gl.createProgram(); gl.attachShader(pr,sh(gl.VERTEX_SHADER,VS)); gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,FS)); gl.linkProgram(pr); gl.useProgram(pr);
  const b=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,b); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const ap=gl.getAttribLocation(pr,'p'); gl.enableVertexAttribArray(ap); gl.vertexAttribPointer(ap,2,gl.FLOAT,false,0,0);
  const U={A:gl.getUniformLocation(pr,'A'),B:gl.getUniformLocation(pr,'B'),t:gl.getUniformLocation(pr,'t'),k:gl.getUniformLocation(pr,'k')};
  gl.uniform1i(U.A,0); gl.uniform1i(U.B,1); gl.uniform1f(U.k,D.sdf.scale); gl.enable(gl.BLEND); gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA); gl.clearColor(0,0,0,0);
  const tex={}; let loaded=0;
  for(const [n,src] of Object.entries(D.sdf.tex)){ const t=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,t); gl.texImage2D(gl.TEXTURE_2D,0,gl.LUMINANCE,1,1,0,gl.LUMINANCE,gl.UNSIGNED_BYTE,new Uint8Array([255]));
    const im=new Image(); im.onload=()=>{gl.bindTexture(gl.TEXTURE_2D,t);gl.texImage2D(gl.TEXTURE_2D,0,gl.LUMINANCE,gl.LUMINANCE,gl.UNSIGNED_BYTE,im);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);loaded++;}; im.src=src; tex[n]=t; }
  return {cv, draw(a,b,t){ gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,tex[a]); gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D,tex[b]); gl.uniform1f(U.t,t); gl.viewport(0,0,cv.width,cv.height); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP,0,4); }};
})();
// stato del morph: forma di partenza, forma di arrivo, avanzamento
let morphBlink=1; let curPose=null; const M={from:'base',to:'base',t:1,dur:0.32,t0:0}; let rigA=1;
const now=()=>(window.__aphi&&__aphi._manual)?__aphi._t:gsap.ticker.time;
function showPose(n,instant){ // n=null: torna al rig (forma 'base'). instant: fotogramma di un ciclo (morph breve)
  if(curPose===n) return; curPose=n;
  const target=n||'base'; const cur=M.t>=1?M.to:M.to;   // se un morph e' a meta', riparto dalla forma di arrivo (evita scatti indietro)
  M.from=(M.t>=1)?M.to:M.to; M.to=target; M.t=0; M.dur=instant?0.11:0.32; M.t0=now();
}
function ease(x){ return x<0.5?2*x*x:1-Math.pow(-2*x+2,2)/2; }
function fadeLayers(){
  // avanzamento del morph sul tempo di GSAP (cosi' funziona anche nei test a tempo manuale)
  if(M.t<1){ M.t=Math.min(1,(now()-M.t0)/M.dur); }
  const showRig=(!curPose&&M.t>=1);
  const tr=showRig?1:0; rigA+=(tr-rigA)*0.6; if(Math.abs(rigA-tr)<0.01) rigA=tr;
  for(const el of [bodyLayer.cv,armLayer.cv,headWrap]) el.style.opacity=rigA;
  if(!showRig&&M.t<1) morph.draw(M.from,M.to,ease(M.t));
  // occhi: quelli della forma di arrivo entrano, gli altri escono
  // occhi: durante il morph tiene quelli di partenza fino a meta', poi quelli di arrivo, con una sbattuta di palpebre nel mezzo
  const half=M.t<0.5; morphBlink=(M.t>=1)?1:Math.min(1,Math.abs(M.t-0.5)*2.2);
  // posa ferma: il corpo e' il PNG della posa (2x, netto) come maschera con fondo nero; il campo di distanza (piu' grosso)
  // si vede solo durante la trasformazione da una forma all'altra
  const still=(M.t>=1);
  for(const n in POSE){ const w=POSE[n].wrap; const on=!showRig&&(half?(n===M.from&&M.from!=='base'):(n===M.to)); w.style.opacity=on?1:0; w.style.background=(on&&still)?'#141414':'transparent'; }
  morph.cv.style.visibility=(showRig||still)?'hidden':'';
}
// ciclo di fotogrammi (camminata, corsa): frames = nomi delle pose, fps
function cycle(frames,fps){ const st={i:-1}; return {tick(t){ const i=Math.floor(t*fps)%frames.length; if(i!==st.i){ st.i=i; showPose(frames[i],true); } }}; }
const S={walkX:0,dir:1,lookX:0,lookY:0,ears:0,body:0,armL:0,armR:0,elbL:0,elbR:0,strL:1,strR:1,blink:1,headRot:0,headY:0,eye:1,near:0,eyeL:1,eyeR:1,pop:1};
function render(){
  const th=S.lookX*0.62, ps=S.lookY*0.35;
  const sinT=Math.sin(th);
  const bob=S.body*-10, zoom=1+S.near*0.14;
  const hx=R*sinT*0.28, hy=S.lookY*10+S.headY+bob+S.near*26;
  const rot=S.headRot+S.ears*6+S.lookX*3;
  headWrap.style.transform=`translate(${hx}px,${hy}px) rotate(${rot}deg) scale(${(1-0.09*Math.abs(sinT))*zoom},${(1-S.body*0.03)*zoom})`;
  for(const [e,sg,k] of [[eyeL,-1,'eyeL'],[eyeR,1,'eyeR']]){ const phi=sg*PHI; const near=-sg*sinT; const depth=1+0.28*near; const x=(CX-gT.x)+R*Math.sin(phi+th)+sg*Math.max(0,S.eye*depth-1)*90; const wsc=Math.min(1,Math.max(0.3,Math.cos(phi+th)/Math.cos(phi)));
    const y=(EYE_Y-gT.y)+R*0.5*Math.sin(ps)+(near<0?-near*44:0);
    const sc=S.eye*depth*S[k]*S.pop;
    e.style.transform=`translate(${x}px,${y}px) scale(${sc*wsc},${sc*S.blink})`; }
  const tx=hx*0.25, ty=bob*0.5, kL=S.strL, kR=S.strR;
  const loc=[];
  loc[BONE.spine]={rot:S.lean||0,sx:1+S.body*0.02,sy:1-S.body*0.04,tx,ty};
  loc[BONE.upperL]={rot:S.armL,sy:kL,sx:1+(kL-1)*0.6}; loc[BONE.foreL]={rot:S.elbL,sy:1+(kL-1)*0.4,sx:1+(kL-1)*0.6};
  loc[BONE.upperR]={rot:-S.armR,sy:kR,sx:1+(kR-1)*0.6}; loc[BONE.foreR]={rot:-S.elbR,sy:1+(kR-1)*0.4,sx:1+(kR-1)*0.6};
  loc[BONE.legL]={rot:S.legL||0,sy:1-S.body*0.06}; loc[BONE.legR]={rot:S.legR||0,sy:1-S.body*0.06};
  setBones(loc); if(!curPose) drawBody();
  fadeLayers();
  { const tf=`translate(${S.walkX}px,${bob*0.6}px) rotate(${S.headRot*0.35}deg) scale(${(1+S.body*0.015)*S.dir},${1-S.body*0.03})`;
    morph.cv.style.transform=tf;
    for(const n in POSE){ const P=POSE[n]; if(+P.wrap.style.opacity>0){ P.wrap.style.transformOrigin=`${512-P.x}px ${985-P.y}px`; P.wrap.style.transform=tf; for(const e of P.eyes) e.style.transform=`scale(${S.eye*S.pop},${S.eye*S.blink*S.pop*morphBlink})`; } } }
  bat.style.transform=cssFollow(bat,boneM[BONE.foreR],handX,handY)+' rotate(238deg)';
}
gsap.ticker.add(render);
function fit(){ const s=stage.clientWidth/1024; scene.style.transform=`scale(${s})`;
  const px=Math.min(2048,Math.max(1024,Math.ceil(1024*s*(window.devicePixelRatio||1))));
  for(const cv of [bodyLayer.cv,armLayer.cv,morph.cv]){ if(cv.width!==px){ cv.width=px; cv.height=px; } }
  if(!curPose) drawBody(); }
new ResizeObserver(fit).observe(stage); fit();
// controlli
const pad=document.getElementById('pad'), dot=document.getElementById('dot');
let padOn=false;
function padSet(e){ const r=pad.getBoundingClientRect(); const x=Math.max(-1,Math.min(1,((e.clientX-r.left)/r.width-0.5)*2)); const y=Math.max(-1,Math.min(1,((e.clientY-r.top)/r.height-0.5)*2)); gsap.to(S,{lookX:x,lookY:y,duration:.25,overwrite:'auto'}); dot.style.left=(50+x*50)+'%'; dot.style.top=(50+y*50)+'%'; touch(); }
pad.addEventListener('pointerdown',e=>{padOn=true;pad.setPointerCapture(e.pointerId);padSet(e);});
pad.addEventListener('pointermove',e=>{if(padOn)padSet(e);});
pad.addEventListener('pointerup',()=>{padOn=false;});
const sl={armL:document.getElementById('armL'),armR:document.getElementById('armR'),elbL:document.getElementById('elbL'),elbR:document.getElementById('elbR'),ears:document.getElementById('ears'),body:document.getElementById('body'),eye:document.getElementById('eye'),near:document.getElementById('near')};
for(const k in sl){ sl[k].addEventListener('input',e=>{S[k]=+e.target.value;touch();}); }
function syncSliders(){ for(const k in sl) sl[k].value=S[k]; dot.style.left=(50+S.lookX*50)+'%'; dot.style.top=(50+S.lookY*50)+'%'; }
// stati
let cur='', tl=null, manual=null, idleTl=null, hover=false;
const STATES={
  hi(){ showPose('saluta2'); return gsap.timeline().to(S,{headRot:-5,eye:1.06,duration:.3,ease:'back.out(2)'}).to(S,{headRot:4,duration:.22,yoyo:true,repeat:5,ease:'sine.inOut'}).to(S,{headRot:0,eye:1,duration:.3},'+=.3'); },
  idle(){ setEyes('neutro'); gsap.to(S,{eye:1,near:0,eyeL:1,eyeR:1,duration:.4}); return gsap.timeline({repeat:-1}).to(S,{body:0.5,duration:1.4,ease:'sine.inOut'}).to(S,{body:0,duration:1.4,ease:'sine.inOut'}); },
  petting(){ setEyes('cuori'); gsap.to(S,{eye:1.03,duration:.3}); return gsap.timeline({repeat:-1}).to(S,{headRot:5,duration:.7,ease:'sine.inOut'}).to(S,{headRot:-5,duration:.7,ease:'sine.inOut'}); },
  dealer(){ showPose('biscotto'); return gsap.timeline().to(S,{eye:1.08,duration:.25}).to(S,{body:0.6,duration:.15,yoyo:true,repeat:7},.2).to(S,{eye:1,body:0,duration:.3},'+=.5'); },
  slapL(){ showPose('stordito'); return gsap.timeline().to(S,{headRot:-14,duration:.08,ease:'power4.out'}).to(S,{headRot:10,duration:.25,ease:'elastic.out(1,.3)'}).to(S,{headRot:0,duration:.9,ease:'elastic.out(1,.25)'}).to(S,{eye:1.15,duration:.4,yoyo:true,repeat:1},0).to({},{duration:.5}); },
  slapR(){ showPose('stordito'); return gsap.timeline().to(S,{headRot:14,duration:.08,ease:'power4.out'}).to(S,{headRot:-10,duration:.25,ease:'elastic.out(1,.3)'}).to(S,{headRot:0,duration:.9,ease:'elastic.out(1,.25)'}).to(S,{eye:1.15,duration:.4,yoyo:true,repeat:1},0).to({},{duration:.5}); },
  angry(){ showPose('indica2'); return gsap.timeline().to(S,{eye:0.92,body:-0.3,duration:.2}).to(S,{headRot:-3,duration:.06,yoyo:true,repeat:11,ease:'none'}).to(S,{headRot:0,body:0,eye:1,duration:.3},'+=.4'); },
  bat(){ showPose('mazza'); return gsap.timeline().to(S,{eye:0.9,duration:.3}).to(S,{headRot:3,body:0.2,duration:.5,yoyo:true,repeat:3,ease:'sine.inOut'}).to(S,{headRot:0,body:0,eye:1,duration:.4}); },
  wow(){ setEyes('tondi'); return gsap.timeline().to(S,{eye:1.12,near:0.35,body:-0.6,ears:-0.5,duration:.15,ease:'back.out(2)'}).to({},{duration:.8}).to(S,{eye:1,near:0,body:0,ears:0,duration:.6,ease:'elastic.out(1,.4)'}); },
  peek(){ showPose('sbircia'); return gsap.timeline().to(S,{eye:1.06,duration:.6,ease:'power2.out'}).to(S,{eye:1.12,duration:.9,yoyo:true,repeat:-1,ease:'sine.inOut'}); },
  look(){ setEyes('neutro'); return gsap.timeline().to(S,{lookX:0.85,lookY:-0.2,near:0.4,eye:1.05,ears:0.3,headRot:6,duration:.6,ease:'power2.out'}); },
  sleep(){ showPose('dorme'); gsap.to(S,{near:0,eye:1,duration:.5}); return gsap.timeline({repeat:-1}).to(S,{body:0.8,duration:2.2,ease:'sine.inOut'}).to(S,{body:0.2,duration:2.2,ease:'sine.inOut'}); },
  stretch(){ showPose('esulta'); return gsap.timeline().to(S,{body:-0.5,eye:1.05,duration:.5,ease:'power2.out'}).to(S,{headRot:-4,duration:.4,yoyo:true,repeat:3},'<').to({},{duration:.6}).to(S,{body:0,eye:1,duration:.4}); },
  music(){ showPose('cuffie'); return gsap.timeline({repeat:-1}).to(S,{body:0.7,headRot:4,duration:.42,ease:'sine.inOut'}).to(S,{body:0,headRot:-4,duration:.42,ease:'sine.inOut'}); },
  coffee(){ showPose('caffe'); return gsap.timeline().to(S,{eye:0.95,duration:.3}).to(S,{headRot:-4,body:0.3,duration:.7,ease:'sine.inOut'},'+=.2').to(S,{headRot:0,body:0,duration:.7,ease:'sine.inOut'},'+=.8').to(S,{eye:1,duration:.3}); },
  think(){ showPose('pensa'); return gsap.timeline().to(S,{eye:1.04,headRot:3,duration:.5,ease:'power2.out'}).to(S,{headRot:-3,duration:.9,yoyo:true,repeat:2,ease:'sine.inOut'}).to(S,{headRot:0,eye:1,duration:.4}); },
  game(){ showPose('gioca'); return gsap.timeline().to(S,{eye:1.08,duration:.3}).to(S,{headRot:-3,duration:.12,yoyo:true,repeat:9,ease:'none'}).to(S,{headRot:3,duration:.12,yoyo:true,repeat:5,ease:'none'}).to(S,{headRot:0,eye:1,duration:.3}); },
  shrug(){ showPose('boh'); return gsap.timeline().to(S,{headRot:4,eye:1.04,duration:.35,ease:'back.out(2)'}).to(S,{headRot:-4,duration:.5,yoyo:true,repeat:1,ease:'sine.inOut'}).to(S,{headRot:0,eye:1,duration:.3},'+=.3'); },
  jump(){ showPose('salta'); return gsap.timeline().to(S,{body:-0.9,duration:.25,ease:'power2.out'}).to(S,{body:0.3,duration:.3,ease:'bounce.out'}).to(S,{body:-0.6,duration:.25}).to(S,{body:0,duration:.35,ease:'bounce.out'}).to({},{duration:.4}); },
  annoyed(){ showPose('scocciato'); return gsap.timeline().to(S,{eye:0.9,duration:.3}).to(S,{headRot:-3,duration:.9,yoyo:true,repeat:1,ease:'sine.inOut'}).to(S,{eye:1,headRot:0,duration:.3},'+=.5'); },
  thumbs(){ showPose('pollice'); return gsap.timeline().to(S,{eye:1.05,body:0.3,duration:.3,ease:'back.out(2)'}).to(S,{body:0,duration:.3}).to({},{duration:1}).to(S,{eye:1,duration:.3}); },
  proud(){ showPose('fiero'); return gsap.timeline().to(S,{body:-0.3,headRot:3,duration:.4,ease:'power2.out'}).to({},{duration:1.2}).to(S,{body:0,headRot:0,duration:.4}); },
  sit(){ showPose('seduto'); return gsap.timeline({repeat:-1}).to(S,{body:0.4,duration:1.6,ease:'sine.inOut'}).to(S,{body:0,duration:1.6,ease:'sine.inOut'}); },
  laptop(){ showPose('laptop'); return gsap.timeline({repeat:-1}).to(S,{body:0.5,headRot:1,duration:.5,ease:'sine.inOut'}).to(S,{body:0,headRot:-1,duration:.5,ease:'sine.inOut'}); },
  run(){ const c=cycle(['corre1','corre2','corre3'],10); const tl=gsap.timeline({repeat:-1,onUpdate(){ c.tick(tl.totalTime()); }});
    // avanti e indietro per il quadro: quando torna si specchia
    tl.fromTo(S,{walkX:-260,dir:1},{walkX:260,duration:1.6,ease:'none'}).set(S,{dir:-1}).fromTo(S,{walkX:260},{walkX:-260,duration:1.6,ease:'none'}).set(S,{dir:1}); return tl; },
  walkPlace(){ const c=cycle(['cammina1','cammina2','cammina3','cammina4','cammina5','cammina6'],8); const tl=gsap.timeline({repeat:-1,onUpdate(){ c.tick(tl.totalTime()); }}); tl.to({},{duration:10}); return tl; },
  runPlace(){ const c=cycle(['corre1','corre2','corre3'],10); const tl=gsap.timeline({repeat:-1,onUpdate(){ c.tick(tl.totalTime()); }}); tl.to({},{duration:10}); return tl; },
  walk(){ const c=cycle(['cammina1','cammina2','cammina3','cammina4','cammina5','cammina6'],8); const tl=gsap.timeline({repeat:-1,onUpdate(){ c.tick(tl.totalTime()); }});
    tl.fromTo(S,{walkX:-240,dir:1},{walkX:240,duration:4,ease:'none'}).set(S,{dir:-1}).fromTo(S,{walkX:240},{walkX:-240,duration:4,ease:'none'}).set(S,{dir:1}); return tl; },
  love(){ showPose('innamorato2'); return gsap.timeline().to(S,{eye:1.05,headRot:-6,duration:.3}).fromTo(cuore,{opacity:0,scale:0,y:0},{opacity:1,scale:1,duration:.35,ease:'back.out(2)'},0).to(cuore,{y:-60,opacity:0,duration:1.2,ease:'power1.out'},.5).to(S,{headRot:6,duration:.6,yoyo:true,repeat:1},.3).to(S,{eye:1,headRot:0,duration:.4}); },
  sad(){ showPose('piange2'); return gsap.timeline().to(S,{headRot:-4,eye:1.1,duration:.5,ease:'power2.out'}).to(S,{body:0.5,duration:.35,yoyo:true,repeat:-1,ease:'sine.inOut'}); }
};
window.__aphi={play:(id)=>play(id),S,render,setEyes,go:(id)=>{touch();manual=(id==='idle')?null:id;play(id);},
  // test deterministici anche a scheda nascosta: tempo avanzato a mano
  _t:0, step(ms){ if(!this._manual){ gsap.ticker.remove(gsap.updateRoot); this._manual=true; this._t=gsap.ticker.time; } for(let t=0;t<ms;t+=33){ this._t+=0.033; gsap.updateRoot(this._t); render(); } },
  goAt(id,ms){ this.go(id); this.step(ms); } };
const LOOP={idle:1,petting:1,sleep:1,peek:1,look:1,sad:1,music:1,sit:1,laptop:1,run:1,walk:1,walkPlace:1,runPlace:1};
const ORDER=['hi','idle','petting','dealer','slapL','slapR','angry','bat','wow','stretch','music','coffee','think','game','sit','laptop','walk','run','love','shrug','jump','annoyed','thumbs','proud','peek','look','sleep','sad'];
const chips=document.getElementById('chips');
for(const id of ORDER){const b=document.createElement('button');b.className='chip';b.type='button';b.dataset.id=id;b.textContent=id;b.addEventListener('click',()=>{touch();manual=(id==='idle')?null:id;play(id);});chips.appendChild(b);}
function rest(){ return manual||(hover?'petting':'idle'); }
function hideProps(){ gsap.set([cuffie,nota1,nota2,tazza,controller,domanda,cuore,zeta,zeta2,stella,bat,cookie],{opacity:0}); }
function play(id){ hideProps(); showPose(null); gsap.killTweensOf(S); gsap.to(S,{walkX:0,dir:1,armL:0,armR:0,elbL:0,elbR:0,strL:1,strR:1,body:0,ears:0,headRot:0,near:0,eye:1,eyeL:1,eyeR:1,blink:1,duration:.25,overwrite:false}); if(tl) tl.kill(); if(idleTl){idleTl.kill();idleTl=null;} if(glanceTl){glanceTl.kill();glanceTl=null;} if(blinkTl){blinkTl.kill();blinkTl=null;} S.blink=1; cur=id; statoEl.textContent=id+(window.AphiBrain?' · '+AphiBrain.mood:''); for(const c of chips.children) c.classList.toggle('on',c.dataset.id===id);
  gsap.to(S,{pop:1.07,duration:.09,yoyo:true,repeat:1});
  const t=STATES[id](); if(LOOP[id]){idleTl=t;} else { tl=t; t.eventCallback('onComplete',()=>{ if(manual===id) manual=null; play(rest()); }); }
  syncSliders(); }
let blinkTl=null, glanceTl=null;
function blink(){ if((cur==='idle'||cur==='petting'||cur==='peek')&&!blinkTl){ blinkTl=gsap.timeline({onComplete:()=>{blinkTl=null;}}).to(S,{blink:0.08,duration:.07}).to(S,{blink:1,duration:.09}); } setTimeout(blink,2500+Math.random()*4000); }
function glance(){ if(cur==='idle'&&!padOn&&!hover&&!glanceTl){ const x=(Math.random()*2-1)*0.9,y=(Math.random()*2-1)*0.5; glanceTl=gsap.timeline({onUpdate:syncSliders,onComplete:()=>{glanceTl=null;}}).to(S,{lookX:x,lookY:y,duration:.35,ease:'power2.out'}).to(S,{lookX:0,lookY:0,duration:.5,ease:'power2.inOut'},'+='+(1.2+Math.random())); } setTimeout(glance,12000+Math.random()*12000); }

// ---- CERVELLO: scelta stocastica non deterministica di cosa fare quando nessuno lo tocca.
// Contesto -> pesi -> campionamento softmax a temperatura. Gancio per Groq/Gemini: AphiBrain.decide(ctx).
const AphiBrain={
  energy:0.9, mood:'curioso', temp:0.9, lastAuto:'', log:[],
  ctx(){ return {idleSec:(Date.now()-lastTouch)/1000, hover, energy:this.energy, mood:this.mood, hour:new Date().getHours(), last:this.lastAuto, cur}; },
  weights(c){
    const w={glance:3, stretch:1.2, wow:0.5, peek:0.8, sad:0.3, bat:0.35, hi:0.2, nap:0.2, none:2.5, music:0.6, coffee:0.5, think:0.7, game:0.4, love:0.15, sit:0.5, laptop:0.5, run:0.25, walk:0.6, dealer:0.3, shrug:0.3, jump:0.25, annoyed:0.2, thumbs:0.2, proud:0.2};
    if(c.idleSec>40) { w.sad+=0.6; w.peek+=0.6; w.none+=1; }
    if(c.idleSec>90) { w.nap+=1.5; }
    if(c.energy<0.35){ w.nap+=2; w.wow*=0.3; w.bat*=0.3; w.stretch+=0.5; }
    if(c.energy>0.8){ w.wow+=0.4; w.bat+=0.3; w.glance+=1; }
    if(c.hour>=0&&c.hour<7){ w.nap+=1.2; w.none+=1; w.coffee+=0.4; }
    if(c.hour>=7&&c.hour<11){ w.coffee+=1; }
    if(c.hour>=21){ w.music+=0.5; w.game+=0.4; }
    if(c.hour>=9&&c.hour<19){ w.laptop+=0.8; }
    if(c.idleSec>60){ w.sit+=0.8; }
    if(c.mood==='giocoso'){ w.bat*=2; w.wow*=1.6; w.hi*=2; w.game*=2; w.music*=1.5; w.jump*=2.5; }
    if(c.mood==='pigro'){ w.annoyed*=2; w.shrug*=1.5; }
    if(c.mood==='pigro'){ w.none*=1.6; w.stretch*=1.5; w.glance*=0.6; }
    if(c.last&&w[c.last]) w[c.last]*=0.35;   // non ripetere subito la stessa cosa
    return w;
  },
  sample(w){ const ks=Object.keys(w); const z=ks.map(k=>Math.exp(Math.log(Math.max(w[k],1e-6))/this.temp)); const Z=z.reduce((a,b)=>a+b,0); let r=Math.random()*Z; for(let i=0;i<ks.length;i++){ r-=z[i]; if(r<=0) return ks[i]; } return ks[ks.length-1]; },
  async decide(c){ return this.sample(this.weights(c)); },   // <- qui si aggancia un LLM: deve restituire una delle chiavi di weights()
  act(k){
    this.lastAuto=k; this.log.push(k); if(this.log.length>30) this.log.shift();
    if(k==='none') return;
    if(k==='glance'){ glance_once(); return; }
    if(k==='stretch'){ manual=null; play('stretch'); return; }
    if(k==='nap'){ manual=null; asleep=true; play('sleep'); return; }
    manual=null; play(k);
    // gli stati che girano in loop durano un po' e poi si torna a riposo
    const dur={sit:[8,15],laptop:[10,20],run:[3,5],walk:[4,9],music:[6,12],sad:[4,7],peek:[3,5]}[k];
    if(dur){ const ms=(dur[0]+Math.random()*(dur[1]-dur[0]))*1000; setTimeout(()=>{ if(cur===k&&!manual) play('idle'); },ms); }
  },
  async tick(){
    if(manual||hover||padOn||document.hidden||cur==='sleep'||cur==='peek'){ this.schedule(); return; }
    if(cur!=='idle'){ this.schedule(); return; }
    const c=this.ctx(); this.energy=Math.max(0,this.energy-0.012); if(Math.random()<0.04) this.mood=['curioso','giocoso','pigro'][Math.floor(Math.random()*3)];
    const k=await this.decide(c); this.act(k); this.schedule();
  },
  schedule(){ const base=cur==='sleep'?9000:4500; setTimeout(()=>this.tick(), base+Math.random()*6000*this.temp); },
  wake(){ this.energy=Math.min(1,this.energy+0.15); }
};
function glance_once(){ if(glanceTl) return; const x=(Math.random()*2-1)*0.9,y=(Math.random()*2-1)*0.5; glanceTl=gsap.timeline({onUpdate:syncSliders,onComplete:()=>{glanceTl=null;}}).to(S,{lookX:x,lookY:y,duration:.35,ease:'power2.out'}).to(S,{lookX:0,lookY:0,duration:.5,ease:'power2.inOut'},'+='+(1.2+Math.random())); }
AphiBrain.say=say; window.AphiBrain=AphiBrain;
// interazione
let lastTouch=Date.now(), pressT=null, asleep=false;
function touch(){ lastTouch=Date.now(); AphiBrain.wake(); if(asleep){asleep=false; manual=null; play(rest());} }
setInterval(()=>{ if(!manual&&!hover&&Date.now()-lastTouch>25000&&!asleep){asleep=true;play('sleep');} },1000);
stage.addEventListener('pointerenter',()=>{hover=true;touch(); if(!manual&&cur==='idle') play('petting');});
stage.addEventListener('pointerleave',()=>{hover=false;touch(); if(cur==='petting'&&!manual) play('idle');});
stage.addEventListener('pointermove',e=>{ if(cur==='petting'||cur==='idle'){ const r=stage.getBoundingClientRect(); const x=((e.clientX-r.left)/r.width-0.5)*2, y=((e.clientY-r.top)/r.height-0.5)*2; const dist=Math.min(1,Math.hypot(x,y)); gsap.to(S,{lookX:x*0.9,lookY:y*0.7,near:(1-dist)*0.4,eye:(cur==='petting'?1.03:1)+(1-dist)*0.1,duration:.3,overwrite:'auto',onUpdate:syncSliders}); } });
stage.addEventListener('pointerdown',e=>{ if(e.button===2) return; if(window.AphiHit&&!window.AphiHit(e)) return; touch(); pressT=setTimeout(()=>{pressT=null;manual=null;play('angry');},450); });
stage.addEventListener('pointerup',e=>{ if(e.button===2) return; if(window.AphiHit&&!window.AphiHit(e)) return; touch(); if(pressT){clearTimeout(pressT);pressT=null;manual=null;play('dealer');} });
stage.addEventListener('pointercancel',()=>{clearTimeout(pressT);pressT=null;});
stage.addEventListener('dblclick',e=>{ if(window.AphiHit&&!window.AphiHit(e)) return; touch();clearTimeout(pressT);pressT=null;manual=null; const r=stage.getBoundingClientRect(); play((e.clientX-r.left)<r.width/2?'slapL':'slapR');});
stage.addEventListener('contextmenu',e=>{e.preventDefault(); if(window.AphiHit&&!window.AphiHit(e)) return; touch();manual=null;play('bat');});
stage.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){e.preventDefault();touch();manual=null;play('dealer');} });
document.addEventListener('mouseleave',()=>{ if(!manual){hover=false;play('peek');} });
document.addEventListener('mouseenter',()=>{ if(cur==='peek'&&!manual) play('idle'); });
document.addEventListener('visibilitychange',()=>{ if(document.hidden&&!manual) play('peek'); else if(cur==='peek'&&!manual) play('idle'); });
play('hi'); setTimeout(blink,2000); setTimeout(glance,9000); AphiBrain.schedule();
setInterval(()=>{ if(cur==='sleep'&&!manual&&Math.random()<0.08){ AphiBrain.energy=0.6; asleep=false; play('stretch'); } },5000);

window.Aphi={play:(id)=>{touch();manual=(id==='idle')?null:id;play(id);},free:()=>{manual=null;play('idle');},say,S,M,morph,get state(){return cur;},setDir:(d)=>{S.dir=d;},brain:AphiBrain,STATES,ORDER};
