"""
Agrega la columna 'talla' a la tabla configuraciones (una sola vez).
Es seguro ejecutarlo varias veces. Uso, desde la carpeta principal:
    python agregar_talla.py
Para la base de Render (Neon): pon su DATABASE_URL en tu .env, ejecútalo
y vuelve a dejar tu .env como estaba.
"""
from sqlalchemy import text

from app import app
from database.connection import db

with app.app_context():
    db.session.execute(text(
        "ALTER TABLE configuraciones ADD COLUMN IF NOT EXISTS talla VARCHAR(10)"
    ))
    db.session.commit()
    print("Listo: la columna 'talla' existe en configuraciones.")
