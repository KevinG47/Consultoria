/* Pruebas del filtro por institucion, con la semantica corregida:
 * INST_FILIA es multivaluado ("A | B"), el filtro compara institucion por institucion. */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_herramienta.js");
const m = fs.readFileSync(HTML, "utf8").match(/<script id="app">([\s\S]*?)<\/script>/);
if (!m) { console.error("FALLO: no se encontro <script id=\"app\">"); process.exit(1); }
fs.writeFileSync(TMP, m[1], "utf8");
const T = require(TMP);
const DATA = T.DATA;

let fallos = 0;
function ok(cond, etiqueta, extra) {
  if (cond) console.log("   OK   " + etiqueta + (extra ? "  -> " + extra : ""));
  else { console.log("   FALLO " + etiqueta + (extra ? "  -> " + extra : "")); fallos++; }
}
function cab(t) { console.log("\n=== " + t + " ==="); }

cab("A. Estructura de INST_FILIA");
ok(DATA.inst.length === 3131, "3131 valores distintos de INST_FILIA", String(DATA.inst.length));
ok(DATA.instMulti === 569, "569 registros multivaluados", String(DATA.instMulti));
ok(T.COMPONENTES_UNICOS.length === 2762, "2762 instituciones una vez separadas",
   String(T.COMPONENTES_UNICOS.length));
ok(DATA.instComponentes === 2762, "el contador embebido coincide",
   String(DATA.instComponentes));
const multi = DATA.inst.filter(function (v) { return v.indexOf(" | ") >= 0; });
ok(multi.length === 550, "550 valores con dos instituciones", String(multi.length));

cab("B. Filtro: coincidencia por institucion, no por texto");
const consulta = "UNIVERSIDAD INDUSTRIAL DE SANTANDER";
const insts = T.institucionesQueCoinciden(consulta);
ok(insts.every(function (n) {
  return T.normalizar(n).indexOf(T.normalizar(consulta)) >= 0;
}), "todas las coincidencias contienen el texto", insts.length + " instituciones");
console.log("        primeras 3: " + insts.slice(0, 3).join(" | "));

const ids = T.filtrarPorInstitucion(consulta);
const permitidas = {};
insts.forEach(function (n) { permitidas[T.normalizar(n)] = true; });
const cumple = function (id) {
  return DATA.personas[id].some(function (r) {
    if (r[6] < 0) return permitidas[T.normalizar(T.SIN_INSTITUCION)] === true;
    return T.COMPONENTES_UNICOS && DATA.inst[r[6]].split(" | ").some(function (c) {
      return permitidas[T.normalizar(c.trim())] === true;
    });
  });
};
ok(ids.every(cumple), "cada ID devuelto tiene esa institucion entre sus afiliaciones",
   ids.length + " personas");
const inverso = Object.keys(DATA.personas).filter(cumple);
ok(inverso.length === ids.length, "no falta ninguna persona que cumpla",
   "esperadas " + inverso.length + " / devueltas " + ids.length);

cab("C. La coincidencia exacta ya es unica");
const exacta = T.institucionesQueCoinciden("UNIVERSIDAD INDUSTRIAL DE SANTANDER")
  .filter(function (n) { return T.normalizar(n) === T.normalizar("UNIVERSIDAD INDUSTRIAL DE SANTANDER"); });
ok(exacta.length === 1, "el nombre completo aparece una sola vez como institucion",
   exacta.join(""));
const soloUIS = ids.filter(function (id) {
  return DATA.personas[id].some(function (r) {
    if (r[6] < 0) return false;
    return DATA.inst[r[6]].split(" | ").some(function (c) {
      return T.normalizar(c.trim()) === T.normalizar("UNIVERSIDAD INDUSTRIAL DE SANTANDER");
    });
  });
});
console.log("        personas con la UIS entre sus afiliaciones: " + soloUIS.length);

cab("D. Registro multivaluado concreto");
const conMulti = Object.keys(DATA.personas).filter(function (id) {
  return DATA.personas[id].some(function (r) {
    return r[6] >= 0 && DATA.inst[r[6]].indexOf(" | ") >= 0;
  });
});
ok(conMulti.length > 0, "hay personas con institucion multivaluada",
   conMulti.length + " personas");
const ejemplo = conMulti[0];
const reg = DATA.personas[ejemplo].filter(function (r) {
  return r[6] >= 0 && DATA.inst[r[6]].indexOf(" | ") >= 0;
})[0];
ok(T.instTexto(reg[6]).indexOf(" · ") >= 0,
   "instTexto muestra las instituciones separadas por ' ·'",
   T.instTexto(reg[6]));
console.log("        ejemplo: " + ejemplo + " -> " + T.instTexto(reg[6]));
ok(T.filtrarPorInstitucion(DATA.inst[reg[6]].split(" | ")[0]).indexOf(ejemplo) >= 0,
   "se encuentra por la primera institucion del par");
ok(T.filtrarPorInstitucion(DATA.inst[reg[6]].split(" | ")[1]).indexOf(ejemplo) >= 0,
   "y tambien por la segunda");

cab("E. Acentos, mayusculas y casos limite");
ok(T.filtrarPorInstitucion("universidad industrial de santander").length === ids.length,
   "mayusculas/minusculas no alteran el resultado");
const conT = T.filtrarPorInstitucion("FUNDACIÓN"), sinT = T.filtrarPorInstitucion("FUNDACION");
ok(conT.length === sinT.length, "las tildes no alteran el resultado",
   conT.length + " personas");
ok(T.filtrarPorInstitucion("XYZ NO EXISTE").length === 0,
   "institucion inexistente -> lista vacia");
ok(T.institucionesQueCoinciden("XYZ NO EXISTE").length === 0,
   "y ninguna institucion coincide");
const sinInst = T.filtrarPorInstitucion(T.SIN_INSTITUCION);
ok(sinInst.length === 6093, "personas sin institucion registrada", String(sinInst.length));
ok(sinInst.every(function (id) {
  return DATA.personas[id].some(function (r) { return r[6] === -1; });
}), "todas tienen al menos un registro sin institucion");
ok(T.institucionesQueCoinciden(T.SIN_INSTITUCION).length === 1,
   "la opcion especial se reconoce como una sola");

console.log("\n" + (fallos === 0 ? "PRUEBAS DE INSTITUCION: TODAS PASARON"
                                 : "FALLOS: " + fallos));
fs.unlinkSync(TMP);
process.exit(fallos === 0 ? 0 : 1);
