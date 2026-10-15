/*
 * pruebas_dom_dashboard_eda.js
 * ============================
 *
 * Prueba FUNCIONAL de las pestanas del dashboard, sin navegador.
 *
 * El HTML es autocontenido y no se puede abrir con un navegador automatizado en
 * este entorno, asi que se simula el DOM minimo que el script de pestanas usa y
 * se ejecuta el script REAL extraido del HTML. Despues se hace clic en cada
 * pestana y se comprueba cual queda activa y que se pidan los redibujados.
 *
 * Uso:  node _archivo/scripts_oneoff/pruebas_dom_dashboard_eda.js
 */

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const RUTA = path.join(__dirname, "..", "..",
  "documentacion_auditoria", "data", "memoria", "dashboard_eda.html");
const html = fs.readFileSync(RUTA, "utf8");

let fallos = 0;
function comprobar(condicion, mensaje) {
  console.log(`  ${condicion ? "[ok]  " : "[FALLO]"} ${mensaje}`);
  if (!condicion) fallos++;
}

// ---------------------------------------------------------------- datos reales
const botonesHtml = [...html.matchAll(/class="tab-btn[^"]*"\s+data-tab="([^"]+)"/g)]
  .map(m => m[1]);
const panelesHtml = [...html.matchAll(/class="panel[^"]*"\s+id="([^"]+)"/g)]
  .map(m => m[1]);
const graficos = [...html.matchAll(/Plotly\.newPlot\(\s*"([^"]+)"/g)].map(m => m[1]);

console.log(`botones en el HTML : ${botonesHtml.join(", ")}`);
console.log(`paneles en el HTML : ${panelesHtml.join(", ")}`);
console.log(`graficos en el HTML: ${graficos.length}\n`);

// -------------------------------------------------------- DOM simulado minimo
function crearElemento(id, clases) {
  const el = {
    id,
    dataset: {},
    _clases: new Set(clases),
    _oyentes: {},
    classList: {
      toggle(c, forzar) {
        const activo = forzar === undefined ? !el._clases.has(c) : forzar;
        if (activo) el._clases.add(c); else el._clases.delete(c);
        return activo;
      },
      contains: c => el._clases.has(c),
    },
    addEventListener(ev, fn) { (el._oyentes[ev] = el._oyentes[ev] || []).push(fn); },
    disparar(ev) { (el._oyentes[ev] || []).forEach(fn => fn({})); },
    querySelectorAll(sel) {
      // El dashboard pide los graficos con un selector combinado
      // ('.js-plotly-plot, .plotly-graph-div'): en un navegador devuelve la union
      // sin duplicados, asi que el simulador debe aceptar las dos clases.
      if (sel.includes(".js-plotly-plot") || sel.includes(".plotly-graph-div")) {
        return el._grafos || [];
      }
      return [];
    },
  };
  return el;
}

// Se replica la estructura real: 4 paneles, y dentro de cada uno sus graficos.
const reparto = { "tab-univariado": 6, "tab-bivariado": 5,
                  "tab-varianza": 2, "tab-diagnosticos": 4 };
const paneles = panelesHtml.map(id => {
  const p = crearElemento(id, []);
  p._grafos = Array.from({ length: reparto[id] || 0 }, (_, i) => ({ id: `${id}-g${i}` }));
  return p;
});
const botones = botonesHtml.map(id => {
  const b = crearElemento(null, ["tab-btn"]);
  b.dataset.tab = id;
  return b;
});

const redibujados = [];
const contexto = {
  document: {
    querySelectorAll: sel => (sel === ".tab-btn" ? botones
      : sel === ".panel" ? paneles : []),
    getElementById: id => paneles.find(p => p.id === id) || null,
    querySelector: sel => (sel === ".panel.activo"
      ? paneles.find(p => p.classList.contains("activo")) || null : null),
  },
  window: { addEventListener: () => {} },
  requestAnimationFrame: fn => fn(),
  Plotly: { Plots: { resize: g => redibujados.push(g.id) } },
  Array, console,
};
contexto.window.document = contexto.document;
contexto.globalThis = contexto;

// ------------------------------------- ejecutar el script REAL del dashboard
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const scriptPestanas = scripts.find(s => s.includes("tab-btn"));
comprobar(!!scriptPestanas, "se encontro el script de pestanas en el HTML");
comprobar(scripts.length === 19, `bloques <script>: ${scripts.length} (esperado 19)`);

vm.createContext(contexto);
vm.runInContext(scriptPestanas, contexto);

// ------------------------------------------------------------ aserciones
console.log("\n=== estado inicial ===");
comprobar(paneles[0].classList.contains("activo"),
          "la pestana activa por defecto es la primera (Univariado)");
comprobar(!paneles[1].classList.contains("activo"), "las demas empiezan ocultas");
comprobar(botones[0].classList.contains("activo"), "el boton 1 queda marcado");
comprobar(redibujados.length === 6,
          `se redibujaron los 6 graficos de la pestana inicial (${redibujados.length})`);

console.log("\n=== clic en cada pestana ===");
const esperado = { "tab-univariado": 6, "tab-bivariado": 5,
                   "tab-varianza": 2, "tab-diagnosticos": 4 };
for (const boton of botones) {
  redibujados.length = 0;
  boton.disparar("click");
  const id = boton.dataset.tab;
  const activos = paneles.filter(p => p.classList.contains("activo"));
  comprobar(activos.length === 1 && activos[0].id === id,
            `clic en ${id}: queda activo solo ese panel`);
  comprobar(boton.classList.contains("activo"), `clic en ${id}: el boton queda marcado`);
  comprobar(redibujados.length === esperado[id],
            `clic en ${id}: se redibujan sus ${esperado[id]} graficos (${redibujados.length})`);
}

console.log("\n=== volver a la primera ===");
redibujados.length = 0;
botones[0].disparar("click");
comprobar(paneles.filter(p => p.classList.contains("activo")).length === 1,
          "sigue habiendo un solo panel activo tras varios cambios");
comprobar(redibujados.length === 6, "se redibujan los 6 graficos al volver");

console.log(`\nRESUMEN: ${fallos === 0 ? "TODAS LAS PRUEBAS PASAN" : fallos + " FALLO(S)"}`);
process.exit(fallos === 0 ? 0 : 1);
