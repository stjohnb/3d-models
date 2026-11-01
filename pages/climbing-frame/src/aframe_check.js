// A-frame swing end: legs from the ground corners up to the beam ends at Y 700/1300.
const H=2300, P=94, BEAM=[700,1300], BEAM_Z0=2155, BEARER_Z=150, TIE_H=94;
const footY=P/2, topY=BEAM[0];            // leg centreline Y at ground and at the top
const run=topY-footY, rake=Math.atan(run/H)*180/Math.PI;
const legAbove=Math.hypot(run,H), legBuried=700/Math.cos(rake*Math.PI/180), legTotal=legAbove+legBuried;
const yc=z=>footY+run*z/H;               // front leg centreline Y at height z
const inner=z=>yc(z)+P/2;                // inner face (towards the frame centre)
const netZ0=BEARER_Z+P, netZ1=BEAM_Z0-TIE_H;   // bearer top to apex tie underside
const wBot=2000-2*inner(netZ0), wTop=2000-2*inner(netZ1), hNet=netZ1-netZ0;
const area=(wBot+wTop)/2*hNet/1e6;
console.log({rake:rake.toFixed(1), legAbove:legAbove.toFixed(0), legBuried:legBuried.toFixed(0), legTotal:legTotal.toFixed(0)});
console.log({netZ0,netZ1,hNet,wBot:wBot.toFixed(0),wTop:wTop.toFixed(0),area:area.toFixed(2)});
console.log('bearer clear length', (2000-2*inner(BEARER_Z+P/2)).toFixed(0), 'apex tie clear', (2000-2*inner(BEAM_Z0-TIE_H/2)).toFixed(0));
// Hand-tied: horizontals every 300 from the bearer top, verticals every 300 about Y=1000, each ending at the leg
const MESH=300; let rows=[], cols=[], cross=0, ropeH=0, ropeV=0;
for (let z=netZ0; z<netZ1-50; z+=MESH){ const w=2000-2*inner(z); rows.push([z,Math.round(w)]); ropeH+=w; }
for (let y=250; y<=1750; y+=MESH){ const ym=Math.min(y,2000-y); // distance to the nearer leg's symmetric side
  // vertical at Y runs from netZ0 up until the leg's inner face reaches it: inner(z)=ym -> z
  const zHit=(ym-P/2-footY)*H/run; const zTop=Math.min(netZ1,zHit); if (zTop>netZ0){ cols.push([y,Math.round(zTop)]); ropeV+=zTop-netZ0; for (const [z] of rows) if (z<zTop) cross++; } }
const knots=cross*0.3*2, hitches=(rows.length*2+cols.length*2)*0.6;
console.log({rows:rows.length, cols:cols.length, cross, ropeH:(ropeH/1000).toFixed(1), ropeV:(ropeV/1000).toFixed(1), total:((ropeH+ropeV)/1000+knots+hitches).toFixed(1)});
console.log('rows',JSON.stringify(rows)); console.log('cols',JSON.stringify(cols));
// angle between the leg and a vertical strand / horizontal strand
console.log('leg-to-vertical angle', rake.toFixed(1), 'leg-to-horizontal', (90-rake).toFixed(1), (90+rake).toFixed(1));
// swing 2 at X=1911: seat edge 2131; leg X face 2517; net plane at the leg centre 2564
console.log('seat edge to leg face', 2517-2131, 'to net plane', 2564-2131);
// leg as a column: beam end reaction ~0.8 kN swing + 2 kids on the net 1.8 kN -> axial ~3 kN; 94x94 C16 column 2.39 m
const A=94*94, E=8000, I=94**4/12, Le=2391, Pcr=Math.PI**2*E*I/Le**2;   // N, Euler
console.log('Euler buckling kN', (Pcr/1000).toFixed(0), 'crushing kN at 8 MPa', (A*8/1000).toFixed(0));
// bearer span: between leg inner faces at bearer mid height
const span=2000-2*inner(BEARER_Z+P/2); const M=1000*span/4, fmd=11.1, Z=94*94*94/6;
console.log('bearer span', span.toFixed(0), 'util at 1 kN midspan', (M/Z/fmd*100).toFixed(0)+'%');
