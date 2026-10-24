// Centre-hung swings on cross beams along X, span between divider rail face (X=600) and far rail face (X=2400)
const P = 90 * 9.81 * 3 + 50; // one adult, dynamic factor 3, plus seat ~ 2700 N
const L = 1800, a = 525, b = L - a;
const M_beam = P * a * b / L; // Nmm
const E = 11000; // C24 E0,mean N/mm2
function sec(name, w, h, fmk, Emod) {
  const Z = w * h * h / 6, I = w * h * h * h / 12, fmd = fmk * 0.9 / 1.3;
  const util = M_beam / (Z * fmd) * 100;
  const defl = P * a * a * b * b / (3 * Emod * I * L); // point load deflection under the load
  console.log(`${name}: M_Ed ${(M_beam/1e6).toFixed(2)} kNm, util ${util.toFixed(0)}%, deflection ${defl.toFixed(1)} mm`);
}
console.log('Cross beam, one swing at 525 of 1800:');
sec('94x94 C16', 94, 94, 16, 8000); sec('94x94 C24', 94, 94, 24, 11000); sec('94x145 C24 on edge', 94, 145, 24, 11000);
// divider rail: supports at Y=100 and Y=1900 (span 1800), loads R1 at 700 and R2 at 1300
const R1 = P * b / L, R2 = P * a / L;
console.log(`beam end reactions: near ${R1.toFixed(0)} N, far ${R2.toFixed(0)} N`);
// simply supported, two point loads: compute max moment by sampling
function railM(loads) { // loads: [[pos, F]], supports at 100 and 1900
  const Ls = 1800; let RA = 0; for (const [p, F] of loads) RA += F * (1900 - p) / Ls;
  let best = 0; for (let x = 100; x <= 1900; x += 1) { let M = RA * (x - 100); for (const [p, F] of loads) if (x > p) M -= F * (x - p); best = Math.max(best, M); } return best;
}
const Mr = railM([[700, R1], [1300, R2]]);
for (const [name, w, h, fmk] of [['94x94 C24', 94, 94, 24], ['94x145 C24 on edge', 94, 145, 24]]) {
  const Z = w * h * h / 6, fmd = fmk * 0.9 / 1.3; console.log(`divider/side rail ${name}: M ${(Mr/1e6).toFixed(2)} kNm, util ${(Mr/(Z*fmd)*100).toFixed(0)}%`);
}
// swing geometry
const chain = 2155 - 500;
for (const th of [45, 60]) { const s = chain * Math.sin(th*Math.PI/180); console.log(`chain ${chain}, ${th} deg reach ${s.toFixed(0)} -> from Y=700: ${(700-s).toFixed(0)} / ${(700+s).toFixed(0)}; from Y=1300: ${(1300-s).toFixed(0)} / ${(1300+s).toFixed(0)}`); }
// hanging drop
for (const hgt of [1000, 1100, 1300]) console.log(`child ${hgt} tall hanging from 2250: feet at ${(2250 - hgt*1.22).toFixed(0)} mm`);
