document.addEventListener("DOMContentLoaded", function () {


    // Animación de entrada de tarjetas

    const cards = document.querySelectorAll(
        ".lesson-card, .admin-card, .ai-card"
    );


    cards.forEach((card, index) => {

        card.style.opacity = "0";

        card.style.transform = "translateY(30px)";


        setTimeout(() => {

            card.style.transition = "0.5s ease";

            card.style.opacity = "1";

            card.style.transform = "translateY(0)";


        }, index * 150);


    });



    // Confirmación antes de salir

    const logoutLinks = document.querySelectorAll(
        'a[href*="logout"]'
    );


    logoutLinks.forEach(link => {


        link.addEventListener(
            "click",
            function(event) {


                let confirmLogout = confirm(
                    "¿Seguro que quieres cerrar sesión?"
                );


                if (!confirmLogout) {

                    event.preventDefault();

                }


            }
        );


    });



    // Efecto al escribir en textos largos

    const textareas = document.querySelectorAll(
        "textarea"
    );


    textareas.forEach(textarea => {


        textarea.addEventListener(
            "input",
            function() {

                this.style.height = "auto";

                this.style.height =
                this.scrollHeight + "px";

            }
        );


    });



});
