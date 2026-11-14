const fs=require('fs');
const k=0.12, ACC='#3b82f6';
const r=(x,y,w,h,extra='')=>`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" ${extra}/>`;
const ln=(x1,y1,x2,y2,extra='')=>`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" ${extra}/>`;
const pg=(pts,extra='')=>`<polygon points="${pts.map(p=>p.map(v=>v.toFixed(1)).join(',')).join(' ')}" ${extra}/>`;
const tx=(x,y,s,extra='')=>`<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" ${extra}>${s}</text>`;
const dimH=(x1,x2,y,label)=>ln(x1,y,x2,y,'class="dim" marker-start="url(#da)" marker-end="url(#da)"')+tx((x1+x2)/2,y-4,label,'text-anchor="middle"');
const dimV=(y1,y2,x,label)=>ln(x,y1,x,y2,'class="dim" marker-start="url(#da)" marker-end="url(#da)"')+tx(x+5,(y1+y2)/2+4,label);
const defs=`<defs><marker id="da" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="currentColor"/></marker></defs>`;
const style='stroke="currentColor" fill="none" stroke-width="1.2" font-family="system-ui, sans-serif" font-size="12" style="max-width:100%;height:auto"';
const wrap=(w,h,label,body)=>`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}" ${style}>${defs}${body}</svg>`;
const LBL='fill="currentColor" stroke="none" font-size="11"';
// Real mm
const H=2300, P=94, BD=145, BEAMS=[700,1300], BEAM_Z0=2155, TIE=[2061,2155], BEARER=[150,244];
const RUN=BEAMS[0]-P/2;                         // leg centreline moves 653 in Y from foot to top
const legY=z=>P/2+RUN*z/BEAM_Z0;                      // front leg centreline
const ROWS=[[244,1660],[544,1478],[844,1296],[1144,1114],[1444,933],[1744,751]];
const COLS=[[550,1498],[850,2061],[1150,2061],[1450,1498]];
const FX=2611, DIV0=614, DIV1=708, DECK=614, SLIDE_X0=104, LEG0=FX-P; // frame width, divider rail, deck, slide, leg left face
const RUNGS=[875.5,1175.5,1475.5,1775.5,2075.5,2375.5];
const SWINGS=[[1236,700],[1911,1300]];
const SEAT_W=440;

// ---------- End elevation (left) and front elevation (right) ----------
{
  const Z=z=>40+(H-z)*k;
  let b='';
  { const ox=40, Y=y=>ox+y*k;                                   // X=2611 face from outside, front (Y=0) on the left
    b+=ln(Y(-160),Z(0),Y(2160),Z(0),'stroke-width="2"');
    for (const m of [false,true]) { const y=v=>m?2000-v:v;
      b+=pg([[Y(y(0)),Z(0)],[Y(y(P)),Z(0)],[Y(y(RUN+P)),Z(BEAM_Z0)],[Y(y(RUN)),Z(BEAM_Z0)]],'fill="currentColor" fill-opacity="0.15"');            // leg
      const dy=RUN*700/BEAM_Z0; b+=pg([[Y(y(0)),Z(0)],[Y(y(P)),Z(0)],[Y(y(P-dy)),Z(-700)],[Y(y(-dy)),Z(-700)]],'stroke-dasharray="3 3"');   // buried stub
    }
    b+=r(Y(legY(TIE[0])+P/2),Z(TIE[1]),(2000-2*(legY(TIE[0])+P/2))*k,(TIE[1]-TIE[0])*k,'fill="currentColor" fill-opacity="0.25"');       // apex tie
    for (const y of BEAMS) b+=r(Y(y-P/2),Z(H),P*k,BD*k,`fill="${ACC}" fill-opacity="0.35" stroke="${ACC}"`);                            // beam ends on the legs
    b+=r(Y(legY(BEARER[0])+P/2),Z(BEARER[1]),(2000-2*(legY(BEARER[0])+P/2))*k,(BEARER[1]-BEARER[0])*k,'fill="currentColor" fill-opacity="0.25"'); // bearer
    for (const [z,w] of ROWS) b+=ln(Y(1000-w/2),Z(z),Y(1000+w/2),Z(z),`stroke="${ACC}" stroke-width="1.6"`);                            // net rows, leg to leg
    for (const [y,zt] of COLS) b+=ln(Y(y),Z(244),Y(y),Z(zt),`stroke="${ACC}" stroke-width="1.6"`);                                       // net columns, ending at the leg or the tie
    for (const y of [850,1150]) b+=`<circle cx="${Y(y).toFixed(1)}" cy="${Z(TIE[0]).toFixed(1)}" r="2" fill="${ACC}" stroke="none"/>`;
    for (const d of [-220,220]) b+=ln(Y(1300),Z(BEAM_Z0),Y(1300),Z(500),'stroke-dasharray="4 3" opacity="0.5"');                           // swing 2 behind
    b+=r(Y(1200),Z(500),200*k,50*k,'fill="currentColor" fill-opacity="0.3"');
    b+=tx(Y(1000),Z(H)-6,'swing end, X = 2611, from outside',`text-anchor="middle" ${LBL}`);
        b+=tx(Y(1000),Z(1000)+4,'net, 300 mesh',`text-anchor="middle" ${LBL} fill="${ACC}"`); b+=tx(Y(1000),Z(1000)+16,'16 mm rope',`text-anchor="middle" ${LBL} fill="${ACC}"`);
    b+=tx(Y(1000),Z(197)+4,'bearer',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=tx(Y(1300),Z(500)+16,'swing 2 behind',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=tx(Y(400),Z(1500),'leg 94 × 94',`text-anchor="end" ${LBL} opacity="0.8"`); b+=tx(Y(370),Z(1380),'3.0 m, 17°',`text-anchor="end" ${LBL} opacity="0.8"`);
    b+=tx(Y(50),Z(-350),'front',`text-anchor="middle" ${LBL} opacity="0.7"`); b+=tx(Y(1950),Z(-350),'rear',`text-anchor="middle" ${LBL} opacity="0.7"`);
    b+=dimV(Z(H),Z(0),Y(2000)+30,'2300');
    b+=dimV(Z(TIE[0]),Z(244),Y(0)-30,'1817');
    b+=dimH(Y(1000-559/2),Y(1000+559/2),Z(H)-26,'559');
    b+=dimH(Y(0),Y(2000),Z(-700)+22,'2000');
    b+=dimH(Y(170),Y(1830),Z(-700)+6,'1660');
  }
  { const ox=330, X=x=>ox+x*k;                                  // front elevation, Y=0 face, looking +Y
    b+=ln(X(-150),Z(0),X(FX+150),Z(0),'stroke-width="2"');
    for (const px of [0,DIV0]) { b+=r(X(px),Z(H),P*k,H*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(X(px),Z(0),P*k,700*k,'stroke-dasharray="3 3"'); }
    b+=r(X(LEG0),Z(H),P*k,H*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(X(LEG0),Z(0),P*k,700*k,'stroke-dasharray="3 3"');     // A legs, raked in Y only: seen edge-on
    b+=r(X(DIV0),Z(H),(FX-DIV0)*k,BD*k,`fill="${ACC}" fill-opacity="0.2" stroke="${ACC}" stroke-dasharray="4 3"`);                       // beams behind
    b+=r(X(0),Z(H),DIV1*k,P*k,'fill="currentColor" fill-opacity="0.15"');                                                                 // tower top rail only
    b+=r(X(0),Z(1500),DECK*k,50*k,'fill="currentColor"');                                                                                 // deck
    b+=r(X(SLIDE_X0),Z(1450),500*k,1450*k,'fill="currentColor" fill-opacity="0.08" stroke-dasharray="4 3"');                                   // slide end-on
    for (const [cx] of SWINGS) { for (const d of [-220,220]) b+=ln(X(cx+d),Z(BEAM_Z0),X(cx+d),Z(500)); b+=r(X(cx-SEAT_W/2),Z(500),SEAT_W*k,50*k,'fill="currentColor"'); }
    b+=r(X(-44),Z(1494),44*k,1394*k,`fill="${ACC}" fill-opacity="0.5" stroke="${ACC}"`);                                                 // wall edge-on
    b+=ln(X(LEG0+P/2),Z(TIE[0]),X(LEG0+P/2),Z(244),`stroke="${ACC}" stroke-width="2.5" stroke-dasharray="2 2"`);                                 // net edge-on, in the leg plane
    b+=r(X(LEG0),Z(TIE[1]),P*k,(TIE[1]-TIE[0])*k,'fill="currentColor" fill-opacity="0.4"'); b+=r(X(LEG0),Z(BEARER[1]),P*k,P*k,'fill="currentColor" fill-opacity="0.4"');
    b+=tx(X(1650),Z(H)-6,'front, Y = 0',`text-anchor="middle" ${LBL}`);
    b+=tx(X(1650),Z(2000)+4,'cross beams, no side rail past the tower',`text-anchor="middle" ${LBL} opacity="0.8"`);
    b+=tx(X(1650),Z(1200),'open',`text-anchor="middle" ${LBL} opacity="0.6"`);
    b+=tx(X(FX+50),Z(1150),'net',`${LBL} fill="${ACC}"`); b+=tx(X(FX+50),Z(1700),'legs',`${LBL} opacity="0.8"`); b+=tx(X(FX+50),Z(1580),'edge-on',`${LBL} opacity="0.8"`);
    b+=tx(X(SLIDE_X0+250),Z(700),'slide',`text-anchor="middle" ${LBL}`); b+=tx(X(SLIDE_X0+250),Z(560),'end-on',`text-anchor="middle" ${LBL}`);
    b+=tx(X(-50),Z(400),'wall',`text-anchor="end" ${LBL} fill="${ACC}"`);
    b+=dimH(X(0),X(DIV1),Z(H)-14,'tower 708');
    b+=dimH(X(0),X(FX),Z(-700)+22,'2611');
    b+=dimV(Z(1500),Z(0),X(0)-40,'1500');
  }
  fs.writeFileSync('aframe_ends.svg',wrap(700,432,'Two elevations of the proposed A-frame swing end. Left, the X equals 2611 face from outside: two 94 by 94 legs rise from the ground corners and lean inwards at 17 degrees to meet under the ends of the two cross beams, tied by a short apex tie at the top and a bearer near the ground; a trapezoidal rope net 1660 wide at the bottom and 559 at the top fills the A on a 300 mesh. Right, the front elevation: the deck tower keeps its top rail, the two cross beams run from it to the A legs, and there is no side rail along the swing bay.',b));
}
// ---------- Plan ----------
{
  const X=x=>60+x*k, Y=y=>30+(2000-y)*k;
  let b='';
  b+=r(X(0),Y(2000),DECK*k,2000*k,'fill="currentColor" fill-opacity="0.12" stroke="none"');                       // deck
  b+=r(X(0),Y(2000),DIV1*k,P*k,'fill="currentColor" fill-opacity="0.15"'); b+=r(X(0),Y(P),DIV1*k,P*k,'fill="currentColor" fill-opacity="0.15"'); // tower side rails
  b+=r(X(0),Y(2000),P*k,2000*k,'fill="currentColor" fill-opacity="0.15"');                                        // near end rail
  b+=r(X(DIV0),Y(2000),P*k,2000*k,'fill="currentColor" fill-opacity="0.15"');                                      // divider rail
  for (const y of BEAMS) b+=r(X(DIV0),Y(y+P/2),(FX-DIV0)*k,P*k,`fill="${ACC}" fill-opacity="0.35" stroke="${ACC}"`);
  for (const x of RUNGS) b+=ln(X(x),Y(BEAMS[0]+P/2),X(x),Y(BEAMS[1]-P/2),'stroke-width="3"');
  for (const [px,py] of [[0,0],[0,1906],[DIV0,0],[DIV0,1906]]) b+=r(X(px),Y(py+P),P*k,P*k,'fill="currentColor" stroke="none"');
  for (const m of [false,true]) { const y=v=>m?2000-v:v;                                                           // A legs: plan sweep from the corner to under the beam
    b+=r(X(LEG0),Y(Math.max(y(0),y(BEAMS[0]+P/2))),P*k,(BEAMS[0]+P/2)*k,'fill="currentColor" fill-opacity="0.12" stroke-dasharray="3 2"');
    b+=r(X(LEG0),Y(y(P)>y(0)?y(P):y(0)),P*k,P*k,'fill="currentColor" stroke="none"');
    b+=ln(X(LEG0+P/2),Y(y(P)),X(LEG0+P/2),Y(y(BEAMS[0]-P/2)),'marker-end="url(#da)" stroke-width="1.5"'); }
  b+=r(X(LEG0),Y(1300-P/2),P*k,(600-P)*k,'fill="currentColor" fill-opacity="0.35"');                              // apex tie between the beam ends
  for (const [cx,cy] of SWINGS) { b+=r(X(cx-SEAT_W/2),Y(cy+100),SEAT_W*k,200*k,'fill="currentColor" fill-opacity="0.25"'); for (const d of [-220,220]) b+=`<circle cx="${X(cx+d).toFixed(1)}" cy="${Y(cy).toFixed(1)}" r="2.5" fill="currentColor" stroke="none"/>`; }
  b+=r(X(-44),Y(2000),44*k,2000*k,`fill="${ACC}" fill-opacity="0.5" stroke="${ACC}"`);                            // wall
  b+=ln(X(0),Y(2000)-4,X(FX),Y(2000)-4,'stroke-dasharray="2 4" opacity="0.4"'); b+=ln(X(0),Y(0)+4,X(FX),Y(0)+4,'stroke-dasharray="2 4" opacity="0.4"');
  b+=tx(X(1650),Y(1960)+4,'no side rail outside the beams',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=tx(X(1650),Y(1700)+4,'six rungs at 300',`text-anchor="middle" ${LBL}`);
  b+=tx(X(1236),Y(480)+4,'seat',`text-anchor="middle" ${LBL} opacity="0.7"`); b+=tx(X(1911),Y(1520)+4,'seat',`text-anchor="middle" ${LBL} opacity="0.7"`);
  b+=`<text transform="translate(${X(DECK/2).toFixed(1)} ${Y(1000).toFixed(1)}) rotate(-90)" text-anchor="middle" ${LBL}>deck tower</text>`;
  b+=tx(X(FX)+8,Y(350)+4,'leg rises',`${LBL} opacity="0.8"`); b+=tx(X(FX)+8,Y(230)+4,'to the beam',`${LBL} opacity="0.8"`);
  b+=tx(X(FX)+8,Y(1000)+4,'apex tie',`${LBL} opacity="0.8"`);
  b+=dimH(X(0),X(FX),Y(0)+28,'2611');
  b+=dimV(Y(2000),Y(0),X(0)-30,'2000');
  fs.writeFileSync('aframe_plan.svg',wrap(560,330,'Plan of the proposed layout: the 708 deep tower at the left keeps its rails, the two cross beams run to the far end where each A leg rises from a ground corner to the beam end, an apex tie joins the two beam ends, and the swing bay has no side rails. The footprint is 2611 by 2000.',b));
}
console.log('ok');
