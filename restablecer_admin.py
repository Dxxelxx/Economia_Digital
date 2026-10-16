from getpass import getpass

from app import app
from database.connection import db
from models.usuario import Usuario


def restablecer_contrasena_admin():
    with app.app_context():

        # Buscar la cuenta administradora
        administrador = Usuario.query.filter_by(
            username="admin",
            rol="administrador"
        ).first()

        if administrador is None:
            print(
                "ERROR: No se encontró el usuario administrador."
            )
            return

        print("====================================")
        print(" RESTABLECER ADMINISTRADOR")
        print(" TALLER EL OBRERO")
        print("====================================")

        # Solicitar nueva contraseña
        password = getpass(
            "Escribe la nueva contraseña: "
        )

        confirmar = getpass(
            "Confirma la nueva contraseña: "
        )

        # Validar contraseña
        if len(password) < 8:
            print(
                "ERROR: La contraseña debe tener "
                "al menos 8 caracteres."
            )
            return

        if password != confirmar:
            print("ERROR: Las contraseñas no coinciden.")
            return

        try:
            administrador.establecer_password(password)

            db.session.commit()

            print("\n¡Contraseña actualizada correctamente!")
            print("Usuario: admin")
            print(
                "Ahora puedes iniciar sesión con "
                "tu nueva contraseña."
            )

        except Exception as error:
            db.session.rollback()

            print(
                "ERROR al actualizar la contraseña:"
            )
            print(error)


if __name__ == "__main__":
    restablecer_contrasena_admin()