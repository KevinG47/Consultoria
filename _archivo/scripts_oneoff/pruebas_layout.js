/* Pruebas del ajuste visual: izquierda = formularios, derecha = lista o ficha.
 * Simula el DOM y ejercita el flujo completo: filtrar -> listar -> clic en un ID
 * -> ver la ficha -> volver a la lista.
 */
const fs = require("fs");
const path = require("path");

const RAIZ = path.resolve(__dirname, "..", "..");
const HTML = path.join(RAIZ, "documentacion_auditoria", "data", "memoria",
                       "herramienta_trayectorias.html");
const TMP = path.join(__dirname, "_app_layout.js");
const texto = fs.readFileSync(HTML, "utf8");
const m = texto.match(/<script id="app">([\s\S]*?)<\/script>/);
if (!m) { console.error("FALLO: no se encontro <script id=\"app\">"); process.exit(1); }

/* ---- stub de DOM ---- */
const { instalar } = require("./stub_dom.js");
const registro = instalar();

let fallos = 0;
function ok(c, e, x) {
  if (c) console.log("   OK   " + e + (x ? "  -> " + x : ""));
  else { console.log("   FALLO " + e + (x ? "  -> " + x : "")); fallos++; }
}
function cab(t) { console.log("\n=== " + t + " ==="); }
const visible = function (id) { return registro[id] && registro[id].style.display !== "none"; };

fs.writeFileSync(TMP, m[1], "utf8");
const T = require(TMP);
const $ = function (id) { return document.getElementById(id); };

/* --------------------------------------------------- A. estructura del HTML */
cab("A. Estructura: la lista vive en el panel derecho");
const iControles = texto.indexOf("CONTROLES");
const iDerecho = texto.indexOf("PANEL DERECHO");
const iPie = texto.indexOf('<div class="pie">');
const bloqueIzq = texto.slice(iControles, iDerecho);
const bloqueDer = texto.slice(iDerecho, iPie);
ok(bloqueIzq.indexOf("cardResultados") < 0,
   "la columna izquierda ya no contiene la tarjeta de resultados");
ok(bloqueDer.indexOf("cardResultados") >= 0,
   "la tarjeta de resultados esta en el panel derecho");
ok(bloqueDer.indexOf('id="panelFicha"') >= 0,
   "el panel derecho tambien contiene la ficha");
ok(bloqueIzq.indexOf('id="q"') >= 0 && bloqueIzq.indexOf('id="inst"') >= 0 &&
   bloqueIzq.indexOf('id="fArea"') >= 0,
   "la columna izquierda conserva los tres formularios");
ok(texto.indexOf('id="panelDerecho"') >= 0, "existe el contenedor #panelDerecho");

/* ------------------------------------------------------- B. estado inicial */
cab("B. Estado inicial");
ok(visible("panelFicha") === true || registro["panelFicha"] === undefined,
   "la ficha (con la ayuda) es lo visible al abrir");
ok(!visible("cardResultados"), "la lista empieza oculta");

/* ------------------------------------------------------- C. filtro -> lista */
cab("C. Filtrar por institucion muestra la lista a la derecha");
$("inst").value = "UNIVERSIDAD INDUSTRIAL DE SANTANDER";
$("btnInst").onclick();
ok(visible("cardResultados"), "se muestra la tarjeta de resultados");
ok(!visible("panelFicha"), "se oculta la ficha");
ok($("listaIds").children.length > 0, "hay identificadores listados",
   String($("listaIds").children.length));
const primerChip = $("listaIds").children[0];
const idClic = primerChip.textContent;
console.log("        primer ID listado: " + idClic);

/* ------------------------------------------------ D. clic en ID -> la ficha */
cab("D. Clic en un ID: la lista se reemplaza por la ficha");
primerChip.onclick();
ok(!visible("cardResultados"), "la lista se oculta");
ok(visible("panelFicha"), "la ficha se muestra en el mismo panel derecho");
ok($("panelFicha").innerHTML.indexOf(idClic) >= 0, "la ficha es la del ID clicado", idClic);
ok($("panelFicha").innerHTML.indexOf("Ficha de trayectoria") >= 0, "se construyo la ficha");

/* ------------------------------------------------ E. volver a la lista */
cab("E. Boton «Volver a la lista»");
ok($("panelFicha").innerHTML.indexOf("Volver a la lista") >= 0,
   "el boton aparece arriba de la ficha");
const btnVolver = document.getElementById("btnVolver");
ok(typeof btnVolver.onclick === "function", "el boton tiene manejador");
btnVolver.onclick();
ok(visible("cardResultados"), "al pulsarlo vuelve la lista");
ok(!visible("panelFicha"), "y se oculta la ficha");
ok($("listaIds").children.length > 0, "la lista se redibuja con los mismos resultados",
   String($("listaIds").children.length));
ok($("listaIds").children[0].textContent === idClic,
   "el primer ID de la lista es el mismo de antes", $("listaIds").children[0].textContent);
ok($("resumenRes").textContent.indexOf("568") >= 0,
   "se conserva el resumen del filtro anterior",
   JSON.stringify($("resumenRes").textContent));

/* ----------------------------------- F. buscar por ID sin lista previa */
cab("F. Buscar por ID conservando la lista anterior");
$("q").value = "0000009172";
$("btnBuscar").onclick();
ok($("panelFicha").innerHTML.indexOf("0000009172") >= 0, "se muestra la ficha buscada");
ok($("panelFicha").innerHTML.indexOf("Volver a la lista") >= 0,
   "el boton sigue disponible para volver al filtro anterior");
document.getElementById("btnVolver").onclick();
ok(visible("cardResultados") && $("listaIds").children[0].textContent === idClic,
   "vuelve exactamente a los resultados del filtro");

/* ------------------------------------------- G. ID inexistente */
cab("G. ID inexistente");
$("q").value = "9999999999";
$("btnBuscar").onclick();
ok($("panelFicha").innerHTML.indexOf("Ese ID no está en el padrón") >= 0,
   "muestra el mensaje de no encontrado");
ok(!visible("cardResultados"), "no deja la lista visible debajo");

/* ------------------------------------------- H. limpiar descarta la lista */
cab("H. Limpiar un filtro");
$("btnLimpiarInst").onclick();
ok($("inst").value === "", "se vacia el campo de institucion");
ok(!visible("cardResultados"), "la lista se oculta");
ok($("panelFicha").innerHTML.indexOf("Volver a la lista") < 0,
   "desaparece el boton de volver: ya no hay lista a la que volver");

/* ------------------------------------------- I. filtro de area/categoria/anio */
cab("I. Filtro por area + categoria + anio");
$("fArea").value = "2"; $("fCat").value = "0"; $("fAnio").value = "1";
$("btnFiltro").onclick();
ok(visible("cardResultados") && !visible("panelFicha"), "se muestra la lista");
ok($("listaIds").children.length > 0, "devuelve identificadores",
   String($("listaIds").children.length));
$("listaIds").children[0].onclick();
ok(visible("panelFicha") && !visible("cardResultados"), "el clic abre la ficha");
ok($("panelFicha").innerHTML.indexOf("Volver a la lista") >= 0, "con boton de volver");

/* ------------------------------------------- J. filtro de institucion vacio */
cab("J. Institucion inexistente");
$("btnLimpiarFiltro").onclick();
$("inst").value = "XYZ NO EXISTE";
$("btnInst").onclick();
ok(visible("cardResultados"), "se muestra la tarjeta de resultados");
ok($("listaIds").innerHTML.indexOf("Ninguna institución") >= 0,
   "con el mensaje especifico de institucion");

console.log("\n" + (fallos === 0 ? "AJUSTE VISUAL: TODAS LAS PRUEBAS PASARON"
                                 : "FALLOS: " + fallos));
fs.unlinkSync(TMP);
process.exit(fallos === 0 ? 0 : 1);
