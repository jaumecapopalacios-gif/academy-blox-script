document.addEventListener("DOMContentLoaded", function () {

    /*
     * COPIAR SCRIPTS
     */

    const copyButtons =
        document.querySelectorAll(".copy-button");


    copyButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            async function () {

                const targetId =
                    button.dataset.target;

                const codeElement =
                    document.getElementById(targetId);


                if (!codeElement) {
                    return;
                }


                const code =
                    codeElement.innerText;


                try {

                    await navigator.clipboard.writeText(
                        code
                    );


                    const originalText =
                        button.innerText;


                    button.innerText =
                        "✓ Copiado";


                    setTimeout(
                        function () {

                            button.innerText =
                                originalText;

                        },
                        1500
                    );


                } catch (error) {

                    alert(
                        "No se pudo copiar el script."
                    );

                }

            }
        );

    });



    /*
     * ANIMACIONES
     */

    const cards =
        document.querySelectorAll(
            ".script-card, .lesson-card, .empty-card"
        );


    cards.forEach(function (card, index) {

        card.style.opacity = "0";

        card.style.transform =
            "translateY(15px)";


        setTimeout(function () {

            card.style.transition =
                "opacity .4s ease, transform .4s ease";

            card.style.opacity = "1";

            card.style.transform =
                "translateY(0)";

        }, index * 60);

    });



    /*
     * CONFIRMAR LOGOUT
     */

    const logoutLinks =
        document.querySelectorAll(
            'a[href*="/logout"]'
        );


    logoutLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const confirmed =
                    confirm(
                        "¿Quieres cerrar sesión?"
                    );


                if (!confirmed) {

                    event.preventDefault();

                }

            }
        );

    });

});
