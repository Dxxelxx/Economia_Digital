/*
 * Pago con MetaMask (ETH).
 *
 * Flujo:
 *  1. Conectar MetaMask y comprobar que esté en la red correcta.
 *  2. Enviar la transacción al taller con el monto exacto.
 *  3. Registrar el hash en el servidor.
 *  4. Preguntar al servidor cada pocos segundos hasta que la
 *     blockchain confirme el pago (el servidor es quien verifica;
 *     este script solo muestra el avance).
 */
(function () {
    "use strict";

    const raiz = document.getElementById("pago-cripto");

    if (!raiz) {
        return;
    }

    const config = {
        destino: raiz.dataset.destino,
        montoWei: raiz.dataset.montoWei,
        chainIdHex: raiz.dataset.chainIdHex,
        urlRegistrar: raiz.dataset.urlRegistrar,
        urlVerificar: raiz.dataset.urlVerificar,
        requeridas: raiz.dataset.requeridas,
        txPendiente: raiz.dataset.txPendiente || ""
    };

    const botonConectar = document.getElementById("btn-conectar");
    const botonPagar = document.getElementById("btn-pagar");
    const estado = document.getElementById("pago-estado");
    const billetera = document.getElementById("pago-billetera");

    let cuenta = null;
    let sondeo = null;
    let intentos = 0;
    const MAX_INTENTOS = 120; // 10 minutos con una consulta cada 5 s.

    function mostrar(mensaje, tipo) {
        estado.textContent = mensaje;
        estado.className = "pago-estado pago-estado-" + (tipo || "info");
        estado.hidden = false;
    }

    function abreviar(direccion) {
        return direccion.slice(0, 6) + "..." + direccion.slice(-4);
    }

    function tieneMetaMask() {
        return typeof window.ethereum !== "undefined";
    }

    // ------------------------------------------------------
    // 1. CONECTAR
    // ------------------------------------------------------

    async function asegurarRed() {

        const actual = await window.ethereum.request({
            method: "eth_chainId"
        });

        if (actual.toLowerCase() === config.chainIdHex.toLowerCase()) {
            return;
        }

        await window.ethereum.request({
            method: "wallet_switchEthereumChain",
            params: [{ chainId: config.chainIdHex }]
        });
    }

    async function conectar() {

        if (!tieneMetaMask()) {
            mostrar(
                "No se encontró MetaMask. Instálalo desde " +
                "metamask.io y recarga la página.",
                "error"
            );
            return false;
        }

        try {

            const cuentas = await window.ethereum.request({
                method: "eth_requestAccounts"
            });

            cuenta = cuentas[0];

            await asegurarRed();

        } catch (error) {

            if (error && error.code === 4001) {
                mostrar("Cancelaste la conexión con MetaMask.", "error");
            } else {
                mostrar(
                    "No se pudo conectar con MetaMask o cambiar a la " +
                    "red de pagos. Cambia de red manualmente e " +
                    "inténtalo de nuevo.",
                    "error"
                );
            }

            return false;
        }

        billetera.textContent = "Conectado: " + abreviar(cuenta);
        botonConectar.hidden = true;
        botonPagar.hidden = false;

        mostrar("Billetera conectada. Ya puedes pagar.", "info");

        return true;
    }

    // ------------------------------------------------------
    // 2. PAGAR
    // ------------------------------------------------------

    async function pagar() {

        botonPagar.disabled = true;

        try {

            await asegurarRed();

            const valorHex = "0x" + BigInt(config.montoWei).toString(16);

            mostrar("Confirma el pago en la ventana de MetaMask...", "info");

            const txHash = await window.ethereum.request({
                method: "eth_sendTransaction",
                params: [{
                    from: cuenta,
                    to: config.destino,
                    value: valorHex
                }]
            });

            mostrar("Transacción enviada. Registrando el pago...", "info");

            await registrar(txHash);

            iniciarSondeo(txHash);

        } catch (error) {

            botonPagar.disabled = false;

            if (error && error.code === 4001) {
                mostrar("Rechazaste la transacción en MetaMask.", "error");
            } else {
                mostrar(
                    (error && error.message) ||
                    "No se pudo enviar la transacción.",
                    "error"
                );
            }
        }
    }

    // ------------------------------------------------------
    // 3. REGISTRAR EN EL SERVIDOR
    // ------------------------------------------------------

    async function llamar(url, cuerpo) {

        const respuesta = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "same-origin",
            body: JSON.stringify(cuerpo)
        });

        let datos = {};

        try {
            datos = await respuesta.json();
        } catch (e) {
            datos = {};
        }

        return { estadoHttp: respuesta.status, datos: datos };
    }

    async function registrar(txHash) {

        const { estadoHttp, datos } = await llamar(config.urlRegistrar, {
            tx_hash: txHash,
            wallet: cuenta
        });

        if (estadoHttp >= 400 || !datos.ok) {
            throw new Error(
                datos.mensaje || "El servidor no pudo registrar el pago."
            );
        }
    }

    // ------------------------------------------------------
    // 4. ESPERAR CONFIRMACIÓN
    // ------------------------------------------------------

    function detenerSondeo() {
        if (sondeo) {
            clearInterval(sondeo);
            sondeo = null;
        }
    }

    async function consultar(txHash) {

        intentos += 1;

        if (intentos > MAX_INTENTOS) {
            detenerSondeo();
            mostrar(
                "La confirmación está tardando más de lo normal. " +
                "Tu pago no se pierde: recarga esta página en unos " +
                "minutos para seguir verificando.",
                "error"
            );
            return;
        }

        try {

            const { datos } = await llamar(config.urlVerificar, {
                tx_hash: txHash
            });

            if (datos.estado === "CONFIRMADO" && datos.redirigir) {
                detenerSondeo();
                mostrar("¡Pago confirmado! Generando tu factura...", "ok");
                window.location.href = datos.redirigir;
                return;
            }

            if (datos.estado === "FALLIDO") {
                detenerSondeo();
                botonPagar.disabled = false;
                mostrar(
                    "El pago no pudo validarse: " +
                    (datos.mensaje || "transacción rechazada.") +
                    " Si ya se descontó de tu billetera, contacta al taller " +
                    "con este hash: " + txHash,
                    "error"
                );
                return;
            }

            const confirmaciones = datos.confirmaciones || 0;

            mostrar(
                "Esperando confirmación en la blockchain (" +
                confirmaciones + " de " + config.requeridas + ")...",
                "info"
            );

        } catch (error) {
            mostrar("Reintentando la verificación...", "info");
        }
    }

    function iniciarSondeo(txHash) {

        detenerSondeo();

        botonConectar.hidden = true;
        botonPagar.hidden = true;

        intentos = 0;

        consultar(txHash);

        sondeo = setInterval(function () {
            consultar(txHash);
        }, 5000);
    }

    // ------------------------------------------------------
    // INICIO
    // ------------------------------------------------------

    botonConectar.addEventListener("click", conectar);
    botonPagar.addEventListener("click", pagar);

    if (tieneMetaMask()) {
        window.ethereum.on("accountsChanged", function (cuentas) {
            if (cuentas.length === 0) {
                cuenta = null;
                billetera.textContent = "";
                botonPagar.hidden = true;
                botonConectar.hidden = false;
            } else {
                cuenta = cuentas[0];
                billetera.textContent = "Conectado: " + abreviar(cuenta);
            }
        });
    } else {
        mostrar(
            "Para pagar necesitas la extensión MetaMask en tu navegador.",
            "error"
        );
    }

    // Si el cliente ya había enviado una transacción, retomarla.
    if (config.txPendiente) {
        mostrar("Retomando la verificación de tu pago anterior...", "info");
        iniciarSondeo(config.txPendiente);
    }
})();
