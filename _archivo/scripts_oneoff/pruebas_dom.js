/* Simulacion del DOM: arranca la interfaz de verdad y ejercita los manejadores.
 * Cubre el punto ciego de las pruebas puras: montar() solo corre en el navegador.
 */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_dom.js");
const m = fs.readFileSync(HTML, "utf8").match(/<script id="app">([\s\S]*?)<\/script>/);

/* ---- stub minimo de DOM ---- */
const { instalar } = require("./stub_dom.js");
const registro = instalar();

let fallos = 0;
function ok(cond, etiqueta, extra) {
  if (cond) console.log("   OK   " + etiqueta + (extra ? "  -> " + extra : ""));
  else { console.log("   FALLO " + etiqueta + (extra ? "  -> " + extra : "")); fallos++; }
}
function cab(t) { console.log("\n=== " + t + " ==="); }

fs.writeFileSync(TMP, m[1], "utf8");
const T = require(TMP);          // al definir document, montar() se ejecuta sola
const $ = function (id) { return document.getElementById(id); };

cab("A. Arranque de la interfaz (montar)");
ok(true, "montar() se ejecuto sin excepciones");
ok($("nFilas").textContent === "77.237", "carga el total de registros",
   JSON.stringify($("nFilas").textContent));
ok($("nPersonas").textContent === "30.086", "carga el total de personas",
   JSON.stringify($("nPersonas").textContent));
ok($("nFilas2").textContent === "77.237", "carga el total en la nota de instituciones");
ok($("nInstMulti").textContent === "569", "carga los 569 registros multivaluados",
   JSON.stringify($("nInstMulti").textContent));
ok($("nInstComp").textContent === "2.762", "carga las 2 762 instituciones",
   JSON.stringify($("nInstComp").textContent));
ok($("pieFuente").textContent.indexOf("bqtm-4y2h") >= 0, "carga la fuente",
   JSON.stringify($("pieFuente").textContent));

cab("B. Controles poblados");
ok($("fArea").children.length === 8, "selector de gran area: 1 + 7 opciones",
   String($("fArea").children.length));
ok($("fCat").children.length === 5, "selector de categoria: 1 + 4 opciones",
   String($("fCat").children.length));
ok($("fAnio").children.length === 7, "selector de convocatoria: 1 + 6 opciones",
   String($("fAnio").children.length));
ok($("listaInst").children.length === 3132, "datalist de instituciones: 3131 + 1",
   String($("listaInst").children.length));
const optArea = $("fArea").children[1];
ok(optArea && optArea.text === T.DATA.areaGran[0] && optArea.value === "0",
   "las opciones de area llevan texto y valor", optArea ? optArea.text : "-");
const optAnio = $("fAnio").children[1];
ok(optAnio && optAnio.text.indexOf("2013") >= 0, "las opciones de anio llevan la fecha",
   optAnio ? optAnio.text : "-");

cab("C. Busqueda por ID desde la interfaz");
$("q").value = "0000000289";
$("btnBuscar").onclick();
const ficha = $("panelFicha").innerHTML;
ok(ficha.indexOf("0000000289") >= 0, "la ficha muestra el ID buscado");
ok(ficha.indexOf("Ficha de trayectoria") >= 0, "se construyo la ficha");
ok(ficha.indexOf("Línea de tiempo") >= 0, "incluye la linea de tiempo");
ok(ficha.indexOf("Ascendió") >= 0, "marca el ascenso");
console.log("        tamano de la ficha: " + ficha.length + " caracteres");

cab("D. ID inexistente desde la interfaz");
$("q").value = "9999999999";
$("btnBuscar").onclick();
ok($("panelFicha").innerHTML.indexOf("Ese ID no está en el padrón") >= 0,
   "muestra el mensaje de ID no encontrado");

cab("E. Ejemplo rapido");
$("btnEjemplo").onclick();
ok($("q").value.length === 10 && T.DATA.personas[$("q").value] !== undefined,
   "el boton de ejemplo carga un ID valido", $("q").value);
ok($("panelFicha").innerHTML.indexOf($("q").value) >= 0,
   "y muestra su ficha");

cab("F. Listado por institucion desde la interfaz");
$("inst").value = "UNIVERSIDAD INDUSTRIAL DE SANTANDER";
$("btnInst").onclick();
ok($("cardResultados").style.display === "", "se muestra el panel de resultados");
ok($("listaIds").children.length > 0, "se listan identificadores",
   String($("listaIds").children.length) + " elementos");
const primerChip = $("listaIds").children[0];
ok(/^\d{10}$/.test(primerChip.textContent), "el primer resultado es un ID de 10 digitos",
   primerChip.textContent);
console.log("        resumen: " + JSON.stringify($("resumenRes").textContent));
ok($("resumenRes").textContent.indexOf("instituciones") >= 0 ||
   $("resumenRes").textContent.indexOf("de «") >= 0,
   "el resumen informa de las instituciones coincidentes");

cab("G. Clic en un ID de la lista abre su ficha");
const idLista = primerChip.textContent;
primerChip.onclick();
ok($("panelFicha").innerHTML.indexOf(idLista) >= 0,
   "la ficha corresponde al ID clicado", idLista);

cab("H. Listado por area + categoria + anio");
$("fArea").value = "2";
$("fCat").value = "0";
$("fAnio").value = "1";
$("btnFiltro").onclick();
ok($("listaIds").children.length > 0, "devuelve identificadores",
   String($("listaIds").children.length));
console.log("        resumen: " + JSON.stringify($("resumenRes").textContent));

cab("I. Limpiar");
$("btnLimpiarInst").onclick();
ok($("cardResultados").style.display === "none", "limpiar institucion oculta resultados");
$("btnLimpiarFiltro").onclick();
ok($("fArea").value === "" && $("fCat").value === "" && $("fAnio").value === "",
   "limpiar filtros vacia los selectores");

console.log("\n" + (fallos === 0 ? "SIMULACION DEL DOM: TODAS PASARON"
                                 : "FALLOS: " + fallos));
fs.unlinkSync(TMP);
process.exit(fallos === 0 ? 0 : 1);
