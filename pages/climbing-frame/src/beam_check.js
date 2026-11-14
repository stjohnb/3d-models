const P=2700, L=2000, a=550, M=P*a;
for (const [name,b,h,fmk,E] of [["100x100 C16",100,100,16,8000],["100x100 C24",100,100,24,11000],
  ["100x150 C24 on edge",100,150,24,11000],["2 x 47x150 C24 bolted",94,150,24,11000],["120x120 C16",120,120,16,8000]]) {
  const Z=b*h*h/6, I=b*h**3/12, fmd=fmk*0.9/1.3, MR=fmd*Z, d=P*a*(3*L*L-4*a*a)/(24*E*I);
  console.log(`${name.padEnd(26)} M_Ed=${(M/1e6).toFixed(2)} kNm  M_Rd=${(MR/1e6).toFixed(2)} kNm  util=${Math.round(M/MR*100)}%  defl=${d.toFixed(1)} mm (L/360=${(L/360).toFixed(1)})`);
}
