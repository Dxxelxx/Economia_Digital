document.addEventListener(
    "DOMContentLoaded",
    function () {

        const material =
            document.getElementById("material");

        const suela =
            document.getElementById("suela");

        const herrajes =
            document.getElementById("herrajes");

        const iniciales =
            document.getElementById("iniciales");

        const cantidad =
            document.getElementById("cantidad");

        const precioUnitario =
            document.getElementById(
                "precio-unitario"
            );

        const cantidadResumen =
            document.getElementById(
                "cantidad-resumen"
            );

        const precioTotal =
            document.getElementById(
                "precio-total"
            );

        const fechaEntrega =
            document.getElementById(
                "fecha-entrega"
            );


        const PRECIO_BASE = 150000;


        function calcularPrecio() {

            let precio = PRECIO_BASE;


            if (
                material.value ===
                "cuero_vegetal"
            ) {
                precio += 30000;
            }


            if (
                suela.value ===
                "reciclada"
            ) {
                precio += 20000;
            }


            if (
                herrajes.value ===
                "dorados"
            ) {
                precio += 10000;
            }


            if (
                iniciales.value.trim() !== ""
            ) {
                precio += 15000;
            }


            const cantidadProducto =
                parseInt(
                    cantidad.value
                ) || 1;


            const total =
                precio *
                cantidadProducto;


            precioUnitario.textContent =
                precio.toLocaleString(
                    "es-CO"
                );


            cantidadResumen.textContent =
                cantidadProducto;


            precioTotal.textContent =
                total.toLocaleString(
                    "es-CO"
                );


            calcularFechaEntrega(
                cantidadProducto
            );
        }


        function calcularFechaEntrega(
            cantidadProducto
        ) {

            let dias = 5;


            if (
                cantidadProducto <= 2
            ) {

                dias = 5;

            } else if (
                cantidadProducto <= 10
            ) {

                dias = 8;

            } else {

                dias = 12;

            }


            const fecha =
                new Date();


            fecha.setDate(
                fecha.getDate() + dias
            );


            fechaEntrega.textContent =
                fecha.toLocaleDateString(
                    "es-CO"
                );
        }


        material.addEventListener(
            "change",
            calcularPrecio
        );


        suela.addEventListener(
            "change",
            calcularPrecio
        );


        herrajes.addEventListener(
            "change",
            calcularPrecio
        );


        iniciales.addEventListener(
            "input",
            calcularPrecio
        );


        cantidad.addEventListener(
            "input",
            calcularPrecio
        );


        calcularPrecio();

    }
);