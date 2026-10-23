/*
 * Paso "Confirmar compra": muestra el diseño del cliente en 3D
 * (con sus modelos .glb) y recalcula el total al cambiar la cantidad.
 */

import { Visor3D } from "./visor.js";

const raiz = document.getElementById("confirmar-raiz");
const diseno = JSON.parse(document.getElementById("diseno-json").textContent);
const aviso = document.getElementById("visor-estado");

const iva = Number(raiz.dataset.iva) / 100;
const unitario = Number(raiz.dataset.precio);

const moneda = new Intl.NumberFormat("es-CO", {
    style: "currency", currency: "COP", maximumFractionDigits: 0
});

// ---------- Totales (el servidor vuelve a calcularlos al comprar) ----------
const cantidad = document.getElementById("cantidad");

function totales() {
    const n = Math.min(100, Math.max(1, parseInt(cantidad.value, 10) || 1));
    const subtotal = unitario * n;
    const valorIva = Math.round(subtotal * iva);

    document.getElementById("c-unitario").textContent = moneda.format(unitario);
    document.getElementById("c-subtotal").textContent = moneda.format(subtotal);
    document.getElementById("c-iva").textContent = moneda.format(valorIva);
    document.getElementById("c-total").textContent = moneda.format(subtotal + valorIva);
}

cantidad.addEventListener("input", totales);
totales();

// ---------- Visor 3D ----------
try {
    const visor = new Visor3D(document.getElementById("contenedor-3d"), {
        modelos: JSON.parse(raiz.dataset.modelos || "{}")
    });

    visor.alEstado = (texto) => {
        aviso.hidden = !texto;
        aviso.className = "conf-estado";
        if (texto) aviso.textContent = texto;
    };

    visor.alError = (mensaje) => {
        aviso.hidden = false;
        aviso.className = "conf-estado visor-error";
        aviso.textContent = "No se pudo mostrar el modelo 3D. " + mensaje;
    };

    visor.alListo = () => { window.__confirmar3dListo = true; };

    visor.actualizar(diseno);

} catch (error) {
    console.error("No se pudo iniciar el visor 3D:", error);
    aviso.className = "conf-estado visor-error";
    aviso.textContent =
        "Tu navegador no pudo iniciar el visor 3D. Aun así puedes confirmar tu compra.";
}
