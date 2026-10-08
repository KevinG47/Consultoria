/* Resumen textual de los IDs de prueba, para reportar cifras exactas. */
const fs = require("fs");
const path = require("path");
const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_resumen.js");
const m = fs.readFileSync(HTML, "utf8").match(/<script id="app">([\s\S]*?)<\/script>/);
fs.writeFileSync(TMP, m[1], "utf8");
const T = require(TMP);
const DATA = T.DATA;

const ids = ["0000003781", "0000009172", "0000000289", "0000000077"];
ids.forEach(function (id) {
  const f = T.trayectoria(id);
  const r = T.resumenTrayectoria(f);
  const c = T.comparacion(f);
  console.log("ID " + id);
  console.log("  convocatorias: " + r.n + " de 6");
  f.forEach(function (x) {
    console.log("    " + x.anio + " " + x.catNombre.replace("Investigador ", "") +
      " | " + x.areaGranNombre + " | " + x.nivelNombre + " | " + x.deptoNombre +
      " | " + (x.instNombre || "(sin institución)") + " | " + x.edadTexto);
  });
  console.log("  inicial=" + r.primera.catNombre.replace("Investigador ", "") +
    "  final=" + r.ultima.catNombre.replace("Investigador ", "") +
    "  ascensos=" + r.ascensos + "  descensos=" + r.descensos +
    "  emerito=" + (r.pasoEmerito ? r.convEmerito : "no") +
    "  deptos distintos=" + r.deptos.length + "  cambios=" + r.cambios.length);
  console.log("  cohorte entrada " + c.cohorte.anio + ": n=" + c.cohorte.n +
    " tasa=" + (c.cohorte.tasa === null ? "sin ventana" :
                (100 * c.cohorte.tasa).toFixed(1) + " %"));
  console.log("  area " + c.areaNombre + ": media=" + c.area.media_convocatorias.toFixed(2) +
    " convocatorias, " + c.area.pct_en_2021.toFixed(1) + " % en 2021, n=" + c.area.n);
  if (c.ret) console.log("  retencion del area en " + c.ret.par + ": " +
    (100 * c.ret.tasa).toFixed(1) + " %");
  console.log("  media global de convocatorias: " + c.mediaGlobal.toFixed(2));
  console.log("");
});

console.log("ID 9999999999 -> encontrado: " + T.buscarPorId("9999999999").encontrado);
fs.unlinkSync(TMP);
