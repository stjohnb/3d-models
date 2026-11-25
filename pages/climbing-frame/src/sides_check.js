// Climbing wall boards and end-ladder rungs: Eurocode-style quick checks.
// Load: 30 kg child x dynamic 3 = 900 N point load mid-span; also a 90 kg adult x 3 = 2700 N for the ladder rung.
const fmd={C16:16*0.9/1.3, C24:24*0.9/1.3, beech:60*0.9/1.3}; // N/mm2 service class 3 short term (rough)
const E={C16:8000,C24:11000};
function board(name,b,h,L,P,grade){ // b width (bending axis length), h thickness in load direction
  const M=P*L/4, Z=b*h*h/6, I=b*h*h*h/12, s=M/Z, d=P*L**3/(48*E[grade]*I);
  console.log(`${name}: span ${L}, P ${P} N -> M ${(M/1000).toFixed(2)} kNm, sigma ${s.toFixed(1)} MPa, util ${(100*s/fmd[grade]).toFixed(0)}% ${grade}, defl ${d.toFixed(1)} mm`);
}
console.log('--- climbing wall boards, horizontal, point load at mid-span, bending about thin axis');
board('27x120 over 2000',120,27,2000,900,'C16');
board('27x120 over 1000 (mid stile)',120,27,1000,900,'C16');
board('44x94 over 2000',94,44,2000,900,'C16');
board('44x94 over 1000 (mid stile)',94,44,1000,900,'C16');
board('44x94 over 1000 adult',94,44,1000,2700,'C24');
board('32x150 over 1000',150,32,1000,900,'C16');
console.log('--- 18 mm ply between battens at 500 (300 mm effective width, fm ~ 20 MPa)');
{ const P=900,L=500,b=300,h=18; const M=P*L/4,Z=b*h*h/6; console.log(`sigma ${(M/Z).toFixed(1)} MPa`); }
console.log('--- rungs, 35 mm, clear span 556 between 44 mm stiles at Y 700/1300');
for (const [name,P] of [['child x3',900],['adult x3',2700]]) {
  const L=556, M=P*L/4;
  const Zd=Math.PI*35**3/32; console.log(`${name}: beech dowel sigma ${(M/Zd).toFixed(1)} MPa (fmd ~${fmd.beech.toFixed(0)}), util ${(100*M/Zd/fmd.beech).toFixed(0)}%`);
  const D=33.7,t=3.2, I=Math.PI/64*(D**4-(D-2*t)**4), Zs=I/(D/2); console.log(`${name}: steel tube 33.7x3.2 sigma ${(M/Zs).toFixed(0)} MPa of 275 -> ${(100*M/Zs/275).toFixed(0)}%`);
}
console.log('--- board count: wall from Z=100 to deck top 1500, 94 wide boards, 6 mm gaps');
{ let n=Math.floor((1400+6)/(94+6)); console.log(`n=${n}, top at ${100+n*94+(n-1)*6}`); n=14; console.log(`n=14 -> top ${100+14*94+13*6}; 15 -> ${100+15*94+14*6}`); }
console.log('--- end ladder rungs at 300 pitch from 250: ', Array.from({length:7},(_,i)=>250+300*i).join(', '), ' gap to rail underside 2155 from top rung 2050 =',2155-2050-17.5);
console.log('--- bars pitch options: 250 -> gap',250-35,'; 300 -> gap',300-35,'; 6 rungs at 300 from 750:',Array.from({length:6},(_,i)=>750+300*i).join(','));
console.log('--- swing 2 clearance to end face: seat edge',1875+220,'-> face 2500:',2500-2095,'; chain to stile line 2522:',2522-2095);
console.log('    if swing 2 at X=1800: seat edge',2020,' clearance',2500-2020,'; seats X-gap', (1800-220)-(1125+220));
console.log('--- wall holds: grid ~ 450 x 400 over 2000 x 1400 -> cols',Math.floor(2000/450),'rows',Math.floor(1400/400));
console.log('--- model scale 1:20: 94 board ->',94/20,'mm; 6 gap ->',6/20,'; hold 80x40 proud ->',80/20,'x',40/20,'; rung 35 ->',35/20);
