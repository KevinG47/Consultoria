/* Stub de DOM compartido por las pruebas de la herramienta.
 *
 * Fiel en un punto que importa: asignar innerHTML vacia los hijos, igual que en
 * el navegador. Sin eso, un re-render parecia acumular nodos en lugar de
 * reemplazarlos y las pruebas no podian detectar un doble dibujado real.
 */
function crear(tag) {
  const nodo = {
    tag: tag, children: [], style: {}, _html: "",
    textContent: "", className: "", value: "",
    appendChild: function (c) { this.children.push(c); return c; },
    addEventListener: function () {},
    scrollIntoView: function () {},
  };
  Object.defineProperty(nodo, "innerHTML", {
    get: function () { return this._html; },
    set: function (v) { this._html = v; this.children.length = 0; },
    enumerable: true, configurable: true,
  });
  return nodo;
}

function instalar() {
  const registro = {};
  global.document = {
    getElementById: function (id) {
      if (!registro[id]) { registro[id] = crear("div"); registro[id].id = id; }
      return registro[id];
    },
    createElement: crear,
  };
  global.Option = function (text, value) { this.text = text; this.value = value; };
  global.alert = function (msg) { throw new Error("alert inesperado: " + msg); };
  return registro;
}

module.exports = { crear: crear, instalar: instalar };
