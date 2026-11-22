// Animasyonu kare kare kaydedip MP4'e çevirir.
// Kullanım: node video_olustur.js [fps] [çıktı.mp4] [--onizleme t1,t2,...]
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const KOK = path.resolve(__dirname, "..");
const R = JSON.parse(fs.readFileSync(path.join(KOK, "analiz", "ek_analiz.json"), "utf8"));
const S = Object.fromEntries(R.sektor.map(o => [o.sektor, o]));
const [ck, cn] = R.cdn_fisher.cdn.split("/").map(Number);
const [ok_, on] = R.cdn_fisher.kendi.split("/").map(Number);
const VERI = {
  n: S["TÜMÜ"].n, pq: S["TÜMÜ"].pq_k, pq_yuzde: S["TÜMÜ"].pq, tls12: S["TÜMÜ"].tls12,
  cdn_n: cn, cdn_k: ck, oz_n: on, oz_k: ok_,
  sektor: R.sektor.filter(o => o.sektor !== "TÜMÜ").map(o => [o.sektor, o.pq]),
  ch_k: R.ag.ch_klasik, ch_h: R.ag.tarayici_ch_medyan, ek: R.ag.yazilan_fark + R.ag.okunan_fark,
  liste: R.liste_boyutu, banka_k: S["Banka"].pq_k, banka_n: S["Banka"].n, kazanan: R.zaman.pq_kazanan,
};
const ZY = path.join(__dirname, "zaman.json");
if (fs.existsSync(ZY)) VERI.sahneler = JSON.parse(fs.readFileSync(ZY, "utf8"));

(async () => {
  const fps = Number(process.argv[2] || 30);
  const cikti = process.argv[3] || path.join(KOK, "Rumeysa_Betul_Ozyurt_Proje_Videosu.mp4");
  const oni = process.argv.indexOf("--onizleme");
  const tarayici = await chromium.launch();
  const sayfa = await tarayici.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await sayfa.addInitScript(v => { window.VERI = v; window.KAYIT = true; }, VERI);
  await sayfa.goto("file://" + path.join(__dirname, "animasyon.html"));
  await sayfa.evaluate(async () => { await document.fonts.load("700 40px Inter"); await document.fonts.load("400 40px Inter"); await document.fonts.ready; });
  const sure = await sayfa.evaluate(() => window.SURE);

  if (oni > 0) {   // belirli anların görüntüsü (kontrol için)
    for (const t of process.argv[oni + 1].split(",").map(Number)) {
      await sayfa.evaluate(t => window.render(t), t);
      await sayfa.screenshot({ path: path.join(process.argv[oni + 2] || ".", `kare_${t}.png`) });
    }
    await tarayici.close(); return;
  }

  const ff = spawn("ffmpeg", ["-y", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "18", "-movflags", "+faststart", cikti],
    { stdio: ["pipe", "ignore", "inherit"] });
  const N = Math.round(sure * fps);
  for (let i = 0; i < N; i++) {
    await sayfa.evaluate(t => window.render(t), i / fps);
    const kare = await sayfa.screenshot({ type: "png" });
    if (!ff.stdin.write(kare)) await new Promise(r => ff.stdin.once("drain", r));
    if (i % 150 === 0) console.log(`kare ${i}/${N}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await tarayici.close();
  console.log("Video:", cikti);
})();
