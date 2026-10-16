import secrets

from flask import Flask, session
from config import Config
from database.connection import db


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    # Identificador nuevo en cada inicio del servidor.
    # Las sesiones anteriores dejarán de ser válidas.
    app.config["SERVER_SESSION_ID"] = secrets.token_urlsafe(32)

    # Inicializar base de datos
    db.init_app(app)

    # =====================================================
    # COMPROBAR LA SESIÓN EN CADA SOLICITUD
    # =====================================================

    @app.before_request
    def comprobar_sesion_servidor():

        # Si no hay usuario autenticado, no hay nada que comprobar.
        if "usuario_id" not in session:
            return None

        sesion_actual = session.get("server_session_id")
        sesion_servidor = app.config["SERVER_SESSION_ID"]

        # Si la sesión pertenece a una ejecución anterior,
        # cerrarla y obligar al usuario a identificarse otra vez.
        if sesion_actual != sesion_servidor:
            session.clear()

        return None

    # =====================================================
    # MODELOS
    # =====================================================

    from models.usuario import Usuario
    from models.cliente import Cliente
    from models.producto import Producto
    from models.configuracion import Configuracion
    from models.pedido import Pedido
    from models.inventario import Inventario
    from models.produccion import Produccion
    from models.factura import Factura

    # =====================================================
    # RUTAS
    # =====================================================

    from routes.principal import principal
    from routes.auth import auth
    from routes.cliente import cliente
    from routes.admin import admin

    from routes.configurador import configurador
    from routes.pedidos import pedidos
    from routes.inventario import inventario
    from routes.produccion import produccion
    from routes.facturacion import facturacion
    from routes.dashboard import dashboard

    # =====================================================
    # REGISTRAR BLUEPRINTS
    # =====================================================

    app.register_blueprint(principal)

    app.register_blueprint(
        auth,
        url_prefix="/auth"
    )

    app.register_blueprint(
        cliente,
        url_prefix="/cliente"
    )

    app.register_blueprint(
        admin,
        url_prefix="/admin"
    )

    app.register_blueprint(
        configurador,
        url_prefix="/configurador"
    )

    app.register_blueprint(
        pedidos,
        url_prefix="/pedidos"
    )

    app.register_blueprint(
        inventario,
        url_prefix="/inventario"
    )

    app.register_blueprint(
        produccion,
        url_prefix="/produccion"
    )

    app.register_blueprint(
        facturacion,
        url_prefix="/facturacion"
    )

    app.register_blueprint(
        dashboard,
        url_prefix="/dashboard"
    )

    # =====================================================
    # CREAR TABLAS
    # =====================================================

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)