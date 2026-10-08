/* Pruebas de la herramienta de trayectorias.
 * Extrae el <script id="app"> del HTML autocontenido, lo carga en Node y ejercita
 * las funciones puras (busqueda, filtros, resumen y ficha) sobre datos reales.
 * Uso: node pruebas_herramienta.js
 */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_herramienta.js");

const texto = fs.readFileSync(HTML, "utf8");
const m = texto.match(/<script id="app">([\s\S]*?)<\/script>/);
if (!m) { console.error("FALLO: no se encontro el bloque <script id=\"app\">"); process.exit(1); }
fs.writeFileSync(TMP, m[1], "utf8");
console.log("script extraido:", (m[1].length / 1024).toFixed(1), "KB");

const T = require(TMP);
const DATA = T.DATA;

let fallos = 0;
function ok(cond, etiqueta, extra) {
  if (cond) { console.log("   OK   " + etiqueta + (extra ? "  -> " + extra : "")); }
  else { console.log("   FALLO " + etiqueta + (extra ? "  -> " + extra : "")); fallos++; }
}
function cab(t) { console.log("\n=== " + t + " ==="); }

/* ---------------------------------------------------- 1. integridad datos */
cab("1. Carga de los datos embebidos");
ok(DATA.personas_n === 30086, "30 086 personas", String(DATA.personas_n));
ok(DATA.filas === 77237, "77 237 registros", String(DATA.filas));
ok(Object.keys(DATA.personas).length === 30086, "claves de personas",
   String(Object.keys(DATA.personas).length));
let suma = 0;
Object.keys(DATA.personas).forEach(function (k) { suma += DATA.personas[k].length; });
ok(suma === 77237, "suma de registros por persona", String(suma));
ok(DATA.convocatorias.length === 6, "6 convocatorias",
   DATA.convocatorias.map(function (c) { return c.anio; }).join(", "));

/* ------------------------------------------------------- 2. busqueda por ID */
cab("2. Busqueda por ID");
const casos = [
  ["0000003781", "ejemplo del enunciado, 1 convocatoria"],
  ["0000009172", "6 convocatorias y llega a Emerito"],
  ["0000000289", "6 convocatorias con ascenso y cambio de institucion"],
  ["0000000077", "una sola convocatoria (2021)"],
];
casos.forEach(function (c) {
  const r = T.buscarPorId(c[0]);
  ok(r.encontrado === true, "encontrado " + c[0] + " (" + c[1] + ")",
     r.encontrado ? r.filas.length + " convocatorias" : "NO ENCONTRADO");
  if (r.encontrado) {
    console.log("        cronologia: " + r.filas.map(function (f) {
      return f.anio + "=" + f.catNombre.replace("Investigador ", "");
    }).join(" | "));
  }
});

cab("2b. Casos limite de la busqueda");
let r = T.buscarPorId("9999999999");
ok(r.encontrado === false, "ID inexistente -> no encontrado");
r = T.buscarPorId("3781");
ok(r.encontrado === true && r.id === "0000003781",
   "ID sin ceros se completa automaticamente", r.encontrado ? r.id : "no");
r = T.buscarPorId("  0000003781  ");
ok(r.encontrado === true, "ID con espacios se tolera");
r = T.buscarPorId("");
ok(r.encontrado === false, "cadena vacia -> no encontrado");
r = T.buscarPorId("abcdefg");
ok(r.encontrado === false, "texto no numerico -> no encontrado");

cab("2c. Ficha HTML: mensaje de ID inexistente");
const fichaMala = T.htmlFicha("9999999999");
ok(fichaMala.indexOf("Ese ID no está en el padrón") >= 0,
   "la ficha avisa que el ID no esta en el padron");

/* -------------------------------------------------- 3. resumen trayectoria */
cab("3. Resumen de trayectoria");
r = T.resumenTrayectoria(T.trayectoria("0000009172"));
ok(r.n === 6, "0000009172 aparece en 6 convocatorias", String(r.n));
ok(r.ascensos === 1 && r.descensos === 0, "1 ascenso y 0 descensos",
   "asc=" + r.ascensos + " desc=" + r.descensos);
ok(r.pasoEmerito === true && r.convEmerito === 2021, "paso por Emerito en 2021",
   String(r.convEmerito));
ok(r.primera.catNombre.indexOf("Sénior") >= 0 &&
   r.ultima.catNombre.indexOf("Emérito") >= 0,
   "categoria inicial Senior y final Emerito",
   r.primera.catNombre + " -> " + r.ultima.catNombre);

r = T.resumenTrayectoria(T.trayectoria("0000000289"));
ok(r.ascensos === 1 && r.descensos === 0, "0000000289: 1 ascenso, 0 descensos");
ok(r.pasoEmerito === false, "0000000289 nunca fue Emerito");
ok(r.insts.length === 2, "0000000289 cambio de institucion (2 distintas)",
   r.insts.join(" / "));

/* ------------------------------------------- 4. avisos de cambio de atributo */
cab("4. Avisos de cambio en la ficha");
const ficha = T.htmlFicha("0000000289");
ok(ficha.indexOf("Ficha de trayectoria") >= 0, "la ficha se construye");
ok(ficha.indexOf("0000000289") >= 0, "incluye el ID");
ok(ficha.indexOf("Ascendió") >= 0, "marca el ascenso");
ok(ficha.indexOf("cambió de categoría") >= 0, "advierte el cambio de categoria");
ok(ficha.indexOf("cambió de institución") >= 0, "advierte el cambio de institucion");
ok(ficha.indexOf("cambió de nivel de formación") >= 0,
   "advierte el cambio de nivel de formacion");
ok(ficha.indexOf("Línea de tiempo") >= 0, "incluye la linea de tiempo");
ok(ficha.indexOf("Resumen de la trayectoria") >= 0, "incluye el resumen");
ok(ficha.indexOf("Comparación con el promedio") >= 0, "incluye la comparacion");
console.log("        longitud de la ficha: " + ficha.length + " caracteres");

/* ------------------------------------------------------------- 5. filtros */
cab("5. Filtro por institucion");
let ids = T.filtrarPorInstitucion("INDUSTRIAL DE SANTANDER");
ok(ids.length > 0, "devuelve IDs", ids.length + " personas");
const coincidentes = {};
T.institucionesQueCoinciden("INDUSTRIAL DE SANTANDER").forEach(function (n) {
  coincidentes[T.normalizar(n)] = true;
});
let todosOk = ids.every(function (id) {
  return DATA.personas[id].some(function (r) {
    if (r[6] < 0) return false;
    return DATA.inst[r[6]].split(" | ").some(function (c) {
      return coincidentes[T.normalizar(c.trim())] === true;
    });
  });
});
ok(todosOk, "cada ID tiene esa institucion entre sus afiliaciones",
   "INST_FILIA es multivaluado: se compara institucion por institucion");
console.log("        primeros 5: " + ids.slice(0, 5).join(", "));

ids = T.filtrarPorInstitucion("industrial de santander");
ok(ids.length > 0, "la busqueda no distingue mayusculas", ids.length + " personas");

ids = T.filtrarPorInstitucion("(sin institución registrada)");
ok(ids.length > 0, "opcion sin institucion registrada", ids.length + " personas");
todosOk = ids.every(function (id) {
  return DATA.personas[id].some(function (r) { return r[6] === -1; });
});
ok(todosOk, "todos los IDs de esa opcion tienen institucion vacia");

ids = T.filtrarPorInstitucion("INSTITUCION QUE NO EXISTE XYZ");
ok(ids.length === 0, "institucion inexistente -> lista vacia");

cab("6. Filtro por area + categoria + anio");
const iArea = DATA.areaGran.indexOf("Ingeniería y Tecnología");
const iCat = DATA.cat.indexOf("Investigador Sénior");
const iConv = 5; // 2021
ids = T.filtrarPorAreaCatAnio(iArea, iCat, iConv);
ok(ids.length > 0, "devuelve IDs", ids.length + " personas");
todosOk = ids.every(function (id) {
  return DATA.personas[id].some(function (r) {
    return r[0] === iConv && r[1] === iCat && r[2] === iArea;
  });
});
ok(todosOk, "cada ID cumple area + categoria + anio a la vez");

ids = T.filtrarPorAreaCatAnio("", "", "");
ok(ids.length === 30086, "sin filtros devuelve el padron completo", String(ids.length));

ids = T.filtrarPorAreaCatAnio(iArea, "", "");
const soloArea = ids.every(function (id) {
  return DATA.personas[id].some(function (r) { return r[2] === iArea; });
});
ok(soloArea, "filtro solo por area funciona");

/* -------------------------------------------------------- 7. comparaciones */
cab("7. Comparacion con promedios");
const c = T.comparacion(T.trayectoria("0000000289"));
ok(c.cohorte !== null, "hay cohorte de entrada para 2013",
   c.cohorte ? "n=" + c.cohorte.n + " tasa=" + c.cohorte.tasa : "null");
ok(c.area !== null, "hay promedio de su gran area",
   c.areaNombre + " media=" + (c.area ? c.area.media_convocatorias.toFixed(2) : "-"));
ok(typeof c.mediaGlobal === "number", "media global de convocatorias",
   c.mediaGlobal.toFixed(3));
const cUlt = T.comparacion(T.trayectoria("0000000077"));
ok(cUlt.cohorte.tasa === null, "cohorte de 2021 sin ventana de seguimiento");

/* ----------------------------------------------------------- 8. coherencia */
cab("8. Coherencia con el analisis longitudinal verificado");
ok(Math.abs(100 * DATA.cohortes["0"].tasa - 56.18) < 0.02,
   "retencion de la cohorte 2013 coincide con el 56,18 % verificado",
   (100 * DATA.cohortes["0"].tasa).toFixed(2) + " %");
ok(DATA.cohortes["0"].n === 8016, "cohorte 2013 = 8 016 personas",
   String(DATA.cohortes["0"].n));

console.log("\n" + (fallos === 0 ? "TODAS LAS PRUEBAS PASARON"
                                 : "HAY " + fallos + " FALLOS"));
fs.unlinkSync(TMP);
process.exit(fallos === 0 ? 0 : 1);
