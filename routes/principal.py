from flask import Blueprint, render_template

principal = Blueprint(
    "principal",
    __name__
)


@principal.route("/")
def inicio():

    productos = [

        {
            "id": 1,
            "nombre": "Zapato Artesanal Clásico",
            "categoria": "Calzado",
            "precio": 280000,
            "descripcion": "Zapato elaborado artesanalmente en cuero.",
            "imagen": "zapato.jpg"
        },

        {
            "id": 2,
            "nombre": "Bolso Ejecutivo en Cuero",
            "categoria": "Bolsos",
            "precio": 350000,
            "descripcion": "Bolso artesanal para uso diario y ejecutivo.",
            "imagen": "bolso.jpg"
        },

        {
            "id": 3,
            "nombre": "Sombrero Artesanal",
            "categoria": "Sombreros",
            "precio": 180000,
            "descripcion": "Sombrero elaborado con acabados artesanales.",
            "imagen": "sombrero.jpg"
        },

        {
            "id": 4,
            "nombre": "Morrál Artesanal",
            "categoria": "Morrales",
            "precio": 320000,
            "descripcion": "Morral de cuero diseñado para uso urbano.",
            "imagen": "morral.jpg"
        },

        {
            "id": 5,
            "nombre": "Cinturón de Cuero",
            "categoria": "Accesorios",
            "precio": 95000,
            "descripcion": "Cinturón elaborado en cuero de alta calidad.",
            "imagen": "cinturon.jpg"
        },

        {
            "id": 6,
            "nombre": "Billetera Artesanal",
            "categoria": "Accesorios",
            "precio": 85000,
            "descripcion": "Billetera compacta elaborada artesanalmente.",
            "imagen": "billetera.jpg"
        }

    ]

    return render_template(
        "index.html",
        productos=productos
    )