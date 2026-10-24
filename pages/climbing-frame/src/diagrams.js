const fs=require('fs');
const k=0.12, ACC='#3b82f6';
const r=(x,y,w,h,extra='')=>`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" ${extra}/>`;
const ln=(x1,y1,x2,y2,extra='')=>`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" ${extra}/>`;
const tx=(x,y,s,extra='')=>`<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" ${extra}>${s}</text>`;
const dimH=(x1,x2,y,label)=>ln(x1,y,x2,y,'class="dim" marker-start="url(#da)" marker-end="url(#da)"')+tx((x1+x2)/2,y-4,label,'text-anchor="middle"');
const dimV=(y1,y2,x,label)=>ln(x,y1,x,y2,'class="dim" marker-start="url(#da)" marker-end="url(#da)"')+tx(x+5,(y1+y2)/2+4,label);
const defs=`<defs><marker id="da" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="currentColor"/></marker></defs>`;
const style='stroke="currentColor" fill="none" stroke-width="1.2" font-family="system-ui, sans-serif" font-size="12" style="max-width:100%;height:auto"';
const wrap=(w,h,label,body)=>`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}" ${style}>${defs}${body}</svg>`;
const LBL='fill="currentColor" stroke="none" font-size="11"';
// Layout constants (real mm)
const FX=2611, DIV0=614, DIV1=708, DECK=614, SLIDE_X0=104, SLIDE_W=500; // frame width, divider rail, deck, slide and ladder (real mm)
const BEAMS=[700,1300];            // cross beam centrelines (Y), 94 x 145 on edge, X DIV0..FX
const BW=94, BD=145;               // beam width (plan) and depth (elevation)
const RUNGS=[875.5,1175.5,1475.5,1775.5,2075.5,2375.5]; // rung X positions, 35 mm, 300 pitch
const SWINGS=[[1236,700],[1911,1300]]; // seat centre X, beam Y
const SEAT_W=440;
const WALL_T=44, WALL_Z0=100, WALL_Z1=1494;          // climbing wall boards on the X=0 face
const STILES=[700,1300], STILE_W=44;                 // end-ladder stiles (Y centres) on the X=2611 face
const NET_Y=[250,1750], NET_Z=[250,2155], MESH=300;    // rope net on the X=2611 face: 1500 wide, rail underside to bearer top
const BEARER_Z=[150,250];                                // 94 x 94 bottom bearer between the X=2611 posts
const HOLDS=[[400,350],[1250,420],[700,700],[1600,650],[300,1000],[1000,1050],[1800,1000],[600,1300],[1400,1350]]; // [Y, Z]

// ---------- Plan ----------
{
  const X=x=>80+x*k, Y=y=>60+(2400-y)*k;
  let b='';
  b+=r(X(0),Y(2000),DECK*k,2000*k,'fill="currentColor" fill-opacity="0.12" stroke="none"');     // deck
  b+=r(X(0),Y(2000),FX*k,2000*k,'stroke-width="2"');                                            // perimeter rails
  b+=r(X(DIV0),Y(1900),BW*k,1800*k,'fill="currentColor" fill-opacity="0.15"');                     // divider rail
  for (const y of BEAMS) b+=r(X(DIV0),Y(y+BW/2),(FX-DIV0)*k,BW*k,`fill="${ACC}" fill-opacity="0.35" stroke="${ACC}"`); // cross beams
  for (const x of RUNGS) b+=ln(X(x),Y(BEAMS[0]+BW/2),X(x),Y(BEAMS[1]-BW/2),'stroke-width="3"');  // rungs
  for (const [px,py] of [[0,0],[0,1900],[FX-100,0],[FX-100,1900],[DIV0,0],[DIV0,1900]]) b+=r(X(px),Y(py+100),100*k,100*k,'fill="currentColor" stroke="none"');
  for (const [cx,cy] of SWINGS) { b+=r(X(cx-SEAT_W/2),Y(cy+100),SEAT_W*k,200*k,'fill="currentColor" fill-opacity="0.25"'); for (const d of [-220,220]) b+=`<circle cx="${X(cx+d).toFixed(1)}" cy="${Y(cy).toFixed(1)}" r="2.5" fill="currentColor" stroke="none"/>`; }
  b+=r(X(SLIDE_X0),Y(0),SLIDE_W*k,2400*k,'fill="currentColor" fill-opacity="0.08"');                        // slide
  b+=ln(X(SLIDE_X0+SLIDE_W/2),Y(-300),X(SLIDE_X0+SLIDE_W/2),Y(-2100),'marker-end="url(#da)" stroke-dasharray="4 3"');
  b+=r(X(SLIDE_X0),Y(2400),SLIDE_W*k,400*k); for (const y of [2100,2200,2300]) b+=ln(X(SLIDE_X0),Y(y),X(SLIDE_X0+SLIDE_W),Y(y)); // ladder
  b+=r(X(-WALL_T),Y(2000),WALL_T*k,2000*k,`fill="${ACC}" fill-opacity="0.5" stroke="${ACC}"`);          // climbing wall boards
  b+=r(X(-WALL_T-44),Y(1000+47),44*k,94*k,`fill="${ACC}" stroke="${ACC}"`);                               // wall mid stile (behind boards)
  b+=ln(X(FX)+2,Y(NET_Y[1]),X(FX)+2,Y(NET_Y[0]),`stroke="${ACC}" stroke-width="2.5" stroke-dasharray="2 2"`); // rope net, edge-on
  b+=r(X(FX),Y(1906),16*k,1812*k,`stroke="${ACC}" fill="${ACC}" fill-opacity="0.3"`);                      // bottom bearer (drawn 16 proud)
  b+=`<text transform="translate(${(X(-WALL_T)-10).toFixed(1)} ${Y(1000).toFixed(1)}) rotate(-90)" text-anchor="middle" ${LBL} fill="${ACC}">climbing wall</text>`;
  b+=`<text transform="translate(${(X(FX+44)+10).toFixed(1)} ${Y(1000).toFixed(1)}) rotate(-90)" text-anchor="middle" ${LBL} fill="${ACC}">rope net to the bars</text>`;
  // labels
  b+=`<text transform="translate(${X(DECK/2).toFixed(1)} ${Y(1000).toFixed(1)}) rotate(-90)" text-anchor="middle" fill="currentColor" stroke="none">deck at 1.5 m</text>`;
  b+=tx(X(SLIDE_X0+SLIDE_W/2),Y(-1200)-4,'slide','text-anchor="middle" fill="currentColor" stroke="none"');
  b+=tx(X(SLIDE_X0+SLIDE_W+20),Y(2200)+4,'ladder','fill="currentColor" stroke="none"');
  b+=tx(X(1650),Y(1700)+4,'monkey bars at 2.3 m, rungs at 300',`text-anchor="middle" ${LBL}`);
  b+=tx(X(1650),Y(300)+4,'open below the bars',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(1236),Y(480)+4,'seat',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(1911),Y(1520)+4,'seat',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(2250),Y(700)+4,'beam',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(1000),Y(1300)+4,'beam',`text-anchor="middle" ${LBL} opacity="0.7"`);
  // dims
  b+=dimH(X(0),X(FX),Y(-2400)+22,'2611');
  b+=dimH(X(0),X(DECK),Y(2400)-12,'614');
  b+=dimV(Y(2000),Y(0),X(FX)+30,'2000');
  b+=dimV(Y(700),Y(0),X(FX)+62,'700');
  b+=dimV(Y(1300),Y(700),X(FX)+62,'600');
  b+=dimV(Y(0),Y(-2400),X(0)-34,'2400');
  b+=dimV(Y(2400),Y(2000),X(0)-34,'400');
  b+=tx(X(FX)+24,Y(-2400)+22,'X →',`${LBL} opacity="0.7"`);
  b+=tx(X(0)-40,Y(2400)-30,'Y ↑',`${LBL} opacity="0.7"`);
  fs.writeFileSync('plan.svg',wrap(500,700,'Plan view: a 2611 by 2000 frame with a 614 wide deck strip along the left end, a climbing wall of boards on the left end face, a rope net on the right end face under the monkey bars, two cross beams at Y 700 and 1300 running from the deck divider to the far side carrying six monkey-bar rungs at 300, one swing seat hung from each beam at X 1236 and 1911, the slide running 2400 out of the front edge and the ladder 400 out of the rear edge, both centred in the 520 slide bay at X 104 to 604.',b));
}
// ---------- Front elevation ----------
{
  const X=x=>80+x*k, Z=z=>40+(2300-z)*k;
  let b='';
  b+=ln(X(-150),Z(0),X(FX+150),Z(0),'stroke-width="2"');
  for (const px of [0,DIV0,FX-100]) { b+=r(X(px),Z(2300),100*k,2300*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(X(px),Z(0),100*k,700*k,'stroke-dasharray="3 3"'); }
  b+=r(X(DIV0),Z(2300),(FX-DIV0)*k,BD*k,`fill="${ACC}" fill-opacity="0.2" stroke="${ACC}" stroke-dasharray="4 3"`); // cross beams behind the rail
  b+=r(X(0),Z(2300),FX*k,100*k,'fill="currentColor" fill-opacity="0.15"');                                   // front top rail
  b+=r(X(0),Z(1500),DECK*k,50*k,'fill="currentColor"');                                                          // deck
  b+=r(X(SLIDE_X0),Z(1450),SLIDE_W*k,1450*k,'fill="currentColor" fill-opacity="0.08" stroke-dasharray="4 3"');            // slide end-on
  b+=tx(X(SLIDE_X0+SLIDE_W/2),Z(700),'slide',`text-anchor="middle" ${LBL}`); b+=tx(X(SLIDE_X0+SLIDE_W/2),Z(560),'end-on',`text-anchor="middle" ${LBL}`);
  for (const [cx] of SWINGS) { for (const d of [-220,220]) b+=ln(X(cx+d),Z(2300-BD),X(cx+d),Z(500)); b+=r(X(cx-SEAT_W/2),Z(500),SEAT_W*k,50*k,'fill="currentColor"'); }
  b+=r(X(-WALL_T),Z(WALL_Z1),WALL_T*k,(WALL_Z1-WALL_Z0)*k,`fill="${ACC}" fill-opacity="0.5" stroke="${ACC}"`); // wall edge-on
  b+=ln(X(FX)+2,Z(NET_Z[1]),X(FX)+2,Z(NET_Z[0]),`stroke="${ACC}" stroke-width="2.5" stroke-dasharray="2 2"`); // rope net edge-on
  b+=r(X(FX)-94*k,Z(BEARER_Z[1]),110*k,100*k,`fill="${ACC}" fill-opacity="0.5" stroke="${ACC}"`);          // bearer end
  b+=tx(X(-WALL_T)-6,Z(400),'wall',`text-anchor="end" ${LBL} fill="${ACC}"`);
  b+=tx(X(FX+50),Z(1150),'net',`${LBL} fill="${ACC}"`);
  b+=tx(X(1650),Z(2300)-6,'top rail 100 × 100; cross beams 100 × 150 behind it',`text-anchor="middle" ${LBL}`);
  b+=tx(X(1650),Z(1200),'open between deck and beams',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(FX+150),Z(-300)+4,'concreted 700',`${LBL} opacity="0.7"`);
  b+=dimV(Z(2300),Z(0),X(FX)+40,'2300');
  b+=dimV(Z(1500),Z(0),X(0)-40,'1500');
  b+=dimV(Z(500),Z(0),X(1500)-10,'500');
  b+=dimH(X(0),X(FX),Z(-700)+22,'2611');
  b+=dimH(X(0),X(DECK),Z(2300)-14,'614');
  fs.writeFileSync('front.svg',wrap(500,432,'Front elevation: the climbing wall boards edge-on at the left end, a rope net edge-on at the right end, posts 2300 high concreted 700 into the ground, deck at 1500 across the left 614 bay, the slide seen end-on below it, centred in the 520 opening, the two 100 by 150 cross beams dashed behind the front top rail, and two swings hanging from those beams with seats 500 off the ground.',b));
}
// ---------- Side elevation ----------
{
  const Y=y=>40+(y+2400)*k, Z=z=>40+(2300-z)*k;
  let b='';
  b+=ln(Y(-2500),Z(0),Y(2500),Z(0),'stroke-width="2"');
  for (const py of [0,1900]) { b+=r(Y(py),Z(2300),100*k,2300*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(Y(py),Z(0),100*k,700*k,'stroke-dasharray="3 3"'); }
  b+=r(Y(0),Z(2300),2000*k,100*k,'fill="currentColor" fill-opacity="0.15"');                 // side top rail
  b+=r(Y(100),Z(2300),1800*k,BD*k,'fill="currentColor" fill-opacity="0.1" stroke-dasharray="4 3"'); // divider rail 100 x 150 behind
  for (const y of BEAMS) b+=r(Y(y-BW/2),Z(2300),BW*k,BD*k,`fill="${ACC}" fill-opacity="0.35" stroke="${ACC}"`); // cross beams in section
  b+=r(Y(BEAMS[0]+BW/2),Z(2268),(BEAMS[1]-BEAMS[0]-BW)*k,36*k,'fill="currentColor"');        // rung
  b+=r(Y(0),Z(1500),2000*k,50*k,'fill="currentColor"');                                      // deck
  const x0=Y(0), x1=Y(-2400), zt=Z(1500), zb=Z(0);
  b+=`<path d="M${x0.toFixed(1)},${zt.toFixed(1)} C${(x0-110).toFixed(1)},${zt.toFixed(1)} ${(x1+110).toFixed(1)},${(zb-8).toFixed(1)} ${x1.toFixed(1)},${(zb-8).toFixed(1)} L${x1.toFixed(1)},${zb.toFixed(1)} C${(x1+110).toFixed(1)},${zb.toFixed(1)} ${(x0-110).toFixed(1)},${(zt+8).toFixed(1)} ${x0.toFixed(1)},${(zt+8).toFixed(1)} Z" fill="currentColor" fill-opacity="0.12"/>`;
  b+=tx(Y(-1300),Z(1050),'slide','text-anchor="middle" fill="currentColor" stroke="none"');
  const lx0=Y(2000), lz0=Z(1500), lx1=Y(2400), lz1=Z(0);
  b+=ln(lx0,lz0,lx1,lz1,'stroke-width="3"');
  for (let i=1;i<=5;i++){ const t=i/6, cx=lx0+(lx1-lx0)*t, cz=lz0+(lz1-lz0)*t; const ang=Math.atan2(lz1-lz0,lx1-lx0)+Math.PI/2; b+=ln(cx-Math.cos(ang)*5,cz-Math.sin(ang)*5,cx+Math.cos(ang)*5,cz+Math.sin(ang)*5,'stroke-width="2"'); }
  b+=tx(Y(2450),Z(900),'ladder 75°','fill="currentColor" stroke="none"');
  // swing from the Y=700 beam, both arcs at 45 deg
  const px=Y(BEAMS[0]), pz=Z(2300-BD), len=(2300-BD-500)*k;
  b+=ln(px,pz,px,pz+len); b+=r(px-9,pz+len,18,6,'fill="currentColor"');
  const a=Math.PI/4;
  for (const sgn of [-1,1]) { const ex=px+sgn*len*Math.sin(a), ez=pz+len*Math.cos(a); b+=ln(px,pz,ex,ez,'stroke-dasharray="4 3"'); b+=r(ex-9,ez,18,6,'fill="currentColor" fill-opacity="0.3"'); }
  b+=`<path d="M${(px-len*Math.sin(a)).toFixed(1)},${(pz+len*Math.cos(a)).toFixed(1)} A${len.toFixed(1)},${len.toFixed(1)} 0 0 0 ${(px+len*Math.sin(a)).toFixed(1)},${(pz+len*Math.cos(a)).toFixed(1)}" stroke-dasharray="2 3" opacity="0.6"/>`;
  b+=tx(px+len*Math.sin(a)+6,pz+len*Math.cos(a)-8,'45° each way',`${LBL} opacity="0.8"`);
  b+=tx(Y(700),Z(2300)+22,'swing 1 beam',`text-anchor="middle" ${LBL}`);
  b+=tx(Y(1300),Z(2300)+22,'swing 2 beam',`text-anchor="middle" ${LBL}`);
  b+=tx(Y(1000),Z(2300)-6,'rung',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=dimH(Y(-2400),Y(0),Z(-700)+22,'2400');
  b+=dimH(Y(0),Y(2000),Z(-700)+22,'2000');
  b+=dimH(Y(2000),Y(2400),Z(-700)+22,'400');
  b+=dimV(Z(2300),Z(0),Y(2400)+40,'2300');
  b+=dimV(Z(1500),Z(0),Y(2400)+76,'1500');
  b+=tx(Y(-2400),Z(0)+14,'slide foot',`${LBL} opacity="0.7"`);
  fs.writeFileSync('side.svg',wrap(750,432,'Side elevation looking along the cross beams: the slide curves down 2400 from the deck on the left, the two 100 by 150 cross beams sit at Y 700 and 1300 under the top with a rung between them, a swing hangs from the Y 700 beam with dashed 45 degree arcs each way, and the ladder leans out 400 at 75 degrees on the right.',b));
}
console.log('svgs written');

// ---------- End elevations ----------
{
  // left panel: deck end, X=0 face seen from outside (looking +X); Y runs right to left so the front (Y=0) is on the right
  // right panel: swing end, X=2611 face seen from outside (looking -X); Y runs left to right so the front (Y=0) is on the left
  const Z=z=>40+(2300-z)*k;
  const panel=(ox,mirror)=>{ const Y=y=>ox+(mirror?(2000-y):y)*k; let b='';
    b+=ln(Y(-120),Z(0),Y(2120),Z(0),'stroke-width="2"');
    for (const py of [0,1900]) { b+=r(Math.min(Y(py),Y(py+100)),Z(2300),100*k,2300*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(Math.min(Y(py),Y(py+100)),Z(0),100*k,700*k,'stroke-dasharray="3 3"'); }
    return {Y,b}; };
  let b='';
  { const {Y,b:p}=panel(40,true); b+=p;
    b+=r(Y(2000),Z(2300),2000*k,100*k,'fill="currentColor" fill-opacity="0.15"');                                  // side rail
    b+=r(Y(2000),Z(1500),2000*k,50*k,'fill="currentColor"');                                                       // deck edge
    b+=r(Y(2000),Z(WALL_Z1),2000*k,(WALL_Z1-WALL_Z0)*k,`fill="${ACC}" fill-opacity="0.15" stroke="${ACC}"`);  // wall panel
    for (let i=1;i<14;i++) { const z=WALL_Z0+i*100-3; b+=ln(Y(2000),Z(z),Y(0),Z(z),`stroke="${ACC}" stroke-width="0.6" opacity="0.7"`); } // board lines
    b+=r(Y(1047),Z(1450),94*k,1350*k,`stroke="${ACC}" stroke-dasharray="3 3"`);                                 // mid stile, behind
    for (const [y,z] of HOLDS) b+=`<ellipse cx="${Y(y).toFixed(1)}" cy="${Z(z).toFixed(1)}" rx="5" ry="3.5" fill="${ACC}" stroke="none"/>`;
    b+=tx(Y(1000),Z(2300)-6,'deck end, X = 0, from outside',`text-anchor="middle" ${LBL}`);
    b+=tx(Y(1000),Z(1500)-5,'deck top 1500',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=tx(Y(1000),Z(WALL_Z0)+16,'44 × 94 boards, mid stile behind',`text-anchor="middle" ${LBL} fill="${ACC}"`);
    b+=tx(Y(50),Z(-350),'front',`text-anchor="middle" ${LBL} opacity="0.7"`); b+=tx(Y(1950),Z(-350),'rear',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=dimV(Z(WALL_Z1),Z(WALL_Z0),Y(0)+8,'1400');
    b+=dimH(Y(2000),Y(0),Z(-700)+22,'2000');
  }
  { const {Y,b:p}=panel(340,false); b+=p;
    b+=r(Y(0),Z(2300),2000*k,BD*k,'fill="currentColor" fill-opacity="0.15"');                                        // far side rail 94 x 145
    for (const y of BEAMS) b+=r(Y(y-BW/2),Z(2300),BW*k,BD*k,`stroke="${ACC}" stroke-dasharray="3 3"`);          // beam ends behind the rail
    b+=r(Y(94),Z(BEARER_Z[1]),1812*k,94*k,'fill="currentColor" fill-opacity="0.15"');                             // bottom bearer
    for (let y=NET_Y[0]; y<=NET_Y[1]+1; y+=MESH) b+=ln(Y(y),Z(NET_Z[1]),Y(y),Z(NET_Z[0]),`stroke="${ACC}" stroke-width="1.6"`); // net verticals
    for (let z=NET_Z[0]; z<NET_Z[1]; z+=MESH) b+=ln(Y(NET_Y[0]),Z(z),Y(NET_Y[1]),Z(z),`stroke="${ACC}" stroke-width="1.6"`);   // net horizontals
    for (let y=NET_Y[0]; y<=NET_Y[1]+1; y+=MESH) b+=`<circle cx="${Y(y).toFixed(1)}" cy="${Z(NET_Z[1]).toFixed(1)}" r="2" fill="${ACC}" stroke="none"/>`; // eye bolts
    for (const d of [-220,220]) b+=ln(Y(1300),Z(2300-BD),Y(1300),Z(500),'stroke-dasharray="4 3" opacity="0.6"');   // swing 2 chains, behind
    b+=r(Y(1300-100),Z(500),200*k,50*k,'fill="currentColor" fill-opacity="0.4"');                                   // swing 2 seat end-on
    b+=tx(Y(1000),Z(2300)-6,'swing end, X = 2611, from outside',`text-anchor="middle" ${LBL}`);
    b+=tx(Y(1000),Z(2000)+4,'rail 94 × 145, beam ends dashed behind it',`text-anchor="middle" ${LBL} opacity="0.8"`);
    b+=tx(Y(1000),Z(1300)+4,'1.5 × 2.0 m net',`text-anchor="middle" ${LBL} fill="${ACC}"`); b+=tx(Y(1000),Z(1300)+16,'300 mesh, 16 mm rope',`text-anchor="middle" ${LBL} fill="${ACC}"`);
    b+=tx(Y(1000),Z(150)+4,'bearer 94 × 94',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=tx(Y(1300),Z(500)+16,'swing 2 behind',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=tx(Y(50),Z(-350),'front',`text-anchor="middle" ${LBL} opacity="0.7"`); b+=tx(Y(1950),Z(-350),'rear',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=dimV(Z(2300),Z(0),Y(2000)+30,'2300');
    b+=dimV(Z(NET_Z[1]),Z(NET_Z[0]),Y(NET_Y[1])+10,'1905');
    b+=dimH(Y(NET_Y[0]),Y(NET_Y[1]),Z(2300)-26,'1500');
    b+=dimH(Y(0),Y(2000),Z(-700)+22,'2000');
  }
  fs.writeFileSync('ends.svg',wrap(640,432,'Two end elevations. Left, the deck end seen from outside: a climbing wall of horizontal boards fills the 2 m face from 100 above the ground to the deck top at 1500, with nine holds scattered over it. Right, the swing end: a 1.5 by 2.0 m rope net with 300 mm mesh hangs from eye bolts in the far side rail, centred under the monkey-bar beams, and is tied down to a 94 by 94 bearer bolted between the posts just above the ground.',b));
}
