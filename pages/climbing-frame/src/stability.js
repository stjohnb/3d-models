// Swing frame stability: overturning (free-standing) and portal push/pull (concreted)
const g = 9.81, H = 2.3, chain = 1.8;
// peak horizontal chain force / (m g) for release angle th0, pendulum T = mg(3cos th - 2cos th0)
function peakH(th0) {
  let best = 0;
  for (let t = 0; t <= th0; t += 0.001) {
    const T = 3 * Math.cos(t) - 2 * Math.cos(th0);
    best = Math.max(best, T * Math.sin(t));
  }
  return best;
}
const rad = d => d * Math.PI / 180;
for (const a of [45, 60, 90]) console.log(`release ${a} deg: peak horizontal = ${peakH(rad(a)).toFixed(2)} mg, seat reach ${(chain*Math.sin(rad(a))*1000).toFixed(0)} mm, seat height ${(2300 - chain*Math.cos(rad(a))*1000).toFixed(0)} mm`);
// self weight estimate (kg) at 500 kg/m3, PAR finished sizes
function weight(d) {
  const posts = 6 * 0.094 * 0.094 * 2.3;
  const rails = (2 * 2.5 + 2 * d) * 0.094 * 0.094;
  const beam = 0.094 * 0.145 * 2.5;
  const deck = 0.5 * d * 0.032 + 2 * d * 0.047 * 0.094;
  const ladder = 10 / 500, slide = 15 / 500;
  return (posts + rails + beam + deck + ladder + slide) * 500;
}
const cases = [["two 30 kg children, 60 deg", 2 * 30 * peakH(rad(60))], ["two 90 kg adults, 60 deg", 2 * 90 * peakH(rad(60))], ["one 90 kg adult, 90 deg", 90 * peakH(rad(90))]];
for (const d of [2.0, 1.5]) {
  const W = weight(d) * g / 1000; // kN
  console.log(`\ndepth ${d} m: self weight ${weight(d).toFixed(0)} kg, restoring moment about front line ${(W * d / 2).toFixed(2)} kNm`);
  for (const [name, m] of cases) {
    const F = m * g / 1000, M = F * H;
    console.log(`  ${name}: H=${(F*1000).toFixed(0)} N, M=${M.toFixed(2)} kNm, free-standing FS=${(W*d/2/M).toFixed(2)}, portal push/pull per side M/d=${(M/d).toFixed(2)} kN, per rear post ${(M/d/3).toFixed(2)} kN`);
  }
}
// concrete collar weight 300 dia x 600 deep
console.log(`\ncollar 300x600: ${(Math.PI*0.15*0.15*0.6*2400).toFixed(0)} kg each`);
// post cantilever at ground: 94x94 C16, all 6 posts share, or 3 front only
const Z = 94 ** 3 / 6, fmd16 = 16 * 0.9 / 1.3, fmd24 = 24 * 0.9 / 1.3;
console.log(`post 94x94: M_Rd C16 ${(Z*fmd16/1e6).toFixed(2)} kNm, C24 ${(Z*fmd24/1e6).toFixed(2)} kNm`);
for (const [name, m] of cases) { const M = m * g / 1000 * H; console.log(`  ${name}: per post (6 share) ${(M/6).toFixed(2)} kNm = ${(M/6/(Z*fmd16/1e6)*100).toFixed(0)}% C16; (3 front only) ${(M/3).toFixed(2)} kNm = ${(M/3/(Z*fmd16/1e6)*100).toFixed(0)}% C16`); }
