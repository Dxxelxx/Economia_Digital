document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "Panel del cliente cargado correctamente."
        );


        const botones =
            document.querySelectorAll(
                ".cliente-card"
            );


        botones.forEach(
            function (boton) {

                boton.addEventListener(
                    "mouseenter",
                    function () {

                        boton.classList.add(
                            "activo"
                        );

                    }
                );


                boton.addEventListener(
                    "mouseleave",
                    function () {

                        boton.classList.remove(
                            "activo"
                        );

                    }
                );

            }
        );

    }
);