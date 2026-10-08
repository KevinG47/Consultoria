/* Los 4 IDs de prueba recorriendo la interfaz con el nuevo layout:
 * la ficha debe aparecer en el panel derecho y la lista ocultarse.
 */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_ids.js");
const texto = fs.readFileSync(HTML, "utf8");
const m = texto.match(/<script id="app">([\s\S]*?)<\/script>/);
if (!m) { console.error("FALLO: falta el bloque de script"); process.exit(1); }

const { instalar } = require("./stub_dom.js");
const registro = instalar();

let fallos = 0;
function ok(c, e, x) {
  if (c) console.log("   OK   " + e + (x ? "  -> " + x : ""));
  else { console.log("   FALLO " + e + (x ? "  -> " + x : "")); fallos++; }
}
function cab(t) { console.log("\n=== " + t + " ==="); }
const vis = function (id) { return registro[id] && registro[id].style.display !== "none"; };
const ficha = function () { return registro["panelFicha"].innerHTML; };

fs.writeFileSync(TMP, m[1], "utf8");
const T = require(TMP);
const $ = function (id) { return document.getElementById(id); };

/* Primero se crea una lista (filtro por institucion) para comprobar que el boton
   de volver aparece en cada ficha. */
cab("Preparacion: filtro por institucion");
$("inst").value = "UNIVERSIDAD INDUSTRIAL DE SANTANDER";
$("btnInst").onclick();
ok(vis("cardResultados") && !vis("panelFicha"), "la lista ocupa el panel derecho");
const nLista = $("listaIds").children.length;
ok($("resumenRes").textContent.indexOf("568") >= 0, "568 personas en el filtro",
   JSON.stringify($("resumenRes").textContent));

cab("ID 1: 0000003781 (ejemplo del enunciado, 1 convocatoria)");
$("q").value = "0000003781";
$("btnBuscar").onclick();
ok(!vis("cardResultados"), "la lista se oculta");
ok(vis("panelFicha"), "la ficha ocupa el panel derecho");
ok(ficha().indexOf("0000003781") >= 0, "es la ficha del ID buscado");
ok(ficha().indexOf("1 de 6") >= 0, "indica 1 de 6 convocatorias");
ok(ficha().indexOf("Primera convocatoria") >= 0, "marca la fila como primera");
ok(ficha().indexOf("Investigador Junior") >= 0, "categoria Junior");
ok(ficha().indexOf("Volver a la lista") >= 0, "ofrece volver a la lista");
console.log("        " + ficha().match(/Convocatorias en que aparece<\/div><div class="big">[^<]*/)[0]
  .replace(/.*big">/, "convocatorias: "));

cab("ID 2: 0000009172 (6 convocatorias, llega a Emerito)");
$("q").value = "0000009172";
$("btnBuscar").onclick();
ok(ficha().indexOf("0000009172") >= 0, "es la ficha correcta");
ok(ficha().indexOf("6 de 6") >= 0, "indica 6 de 6 convocatorias");
ok(ficha().indexOf("Sí, en 2021") >= 0, "senala que paso por Emerito en 2021");
ok(ficha().indexOf("Ascendió") >= 0, "marca el ascenso a Emerito");
ok(ficha().match(/Emérito/g).length >= 2, "Emerito aparece en la linea de tiempo",
   ficha().match(/Emérito/g).length + " menciones");
ok(ficha().indexOf("UNIVERSIDAD INDUSTRIAL DE SANTANDER") >= 0,
   "muestra su institucion de filiacion");

cab("ID 3: 0000000289 (6 convocatorias, ascenso y cambios de atributo)");
$("q").value = "0000000289";
$("btnBuscar").onclick();
ok(ficha().indexOf("0000000289") >= 0, "es la ficha correcta");
ok(ficha().indexOf("6 de 6") >= 0, "indica 6 de 6 convocatorias");
ok(ficha().indexOf("cambió de categoría") >= 0, "advierte el cambio de categoria");
ok(ficha().indexOf("cambió de institución") >= 0, "advierte el cambio de institucion");
ok(ficha().indexOf("cambió de nivel de formación") >= 0,
   "advierte el cambio de nivel de formacion");
ok(ficha().indexOf("cambió de gran área") >= 0, "advierte el cambio de gran area");
ok(ficha().indexOf("ESUMER") >= 0 && ficha().indexOf("CEIPA") >= 0,
   "aparecen las dos instituciones");

cab("ID 4: 0000000077 (una sola convocatoria, 2021)");
$("q").value = "0000000077";
$("btnBuscar").onclick();
ok(ficha().indexOf("0000000077") >= 0, "es la ficha correcta");
ok(ficha().indexOf("1 de 6") >= 0, "indica 1 de 6 convocatorias");
ok(ficha().indexOf("2021") >= 0, "su unica convocatoria es 2021");
ok(ficha().indexOf("sin ventana de seguimiento") >= 0,
   "la comparacion avisa de que su cohorte no tiene ventana");

cab("ID inexistente: 9999999999");
$("q").value = "9999999999";
$("btnBuscar").onclick();
ok(ficha().indexOf("Ese ID no está en el padrón") >= 0, "muestra el mensaje");
ok(vis("panelFicha") && !vis("cardResultados"), "ocupa el panel derecho y oculta la lista");

cab("Volver a la lista tras los 4 IDs");
ok(ficha().indexOf("Volver a la lista") >= 0, "el boton sigue en la ficha");
document.getElementById("btnVolver").onclick();
ok(vis("cardResultados") && !vis("panelFicha"), "vuelve la lista de 568 IDs");
ok($("listaIds").children.length === nLista, "con el mismo numero de resultados",
   String($("listaIds").children.length));
ok($("listaIds").children.length === 301, "300 chips + 1 aviso de recorte",
   String($("listaIds").children.length));

console.log("\n" + (fallos === 0 ? "LOS 4 IDs Y EL FILTRO: TODO CORRECTO"
                                 : "FALLOS: " + fallos));
fs.unlinkSync(TMP);
process.exit(fallos === 0 ? 0 : 1);
