import mysql.connector as msql
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YES"
}

DB_NAME = "CatalogoDB"

def setup_catalogo():
    try:
        connection = msql.connect(**DB_CONFIG)

        if connection.is_connected():
            print("[INFO] Conexión establecida con MySQL.")
            cursor = connection.cursor()

            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")

            # Tabla productos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    categoria VARCHAR(50) NULL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Tabla processed_requests
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_requests (
                    request_id VARCHAR(36) PRIMARY KEY,
                    servicio VARCHAR(50) NOT NULL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla outbox
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outbox (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    aggregate_type VARCHAR(50),
                    aggregate_id VARCHAR(50),
                    event_type VARCHAR(50),
                    payload JSON,
                    published TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    published_at DATETIME NULL
                )
            """)


            # Insertar producto de prueba
            cursor.execute("""
                INSERT IGNORE INTO productos (id_producto, nombre, precio)
                VALUES (1, 'Reserva Cancha', 75000)
            """)

            connection.commit()
            print("[INFO] Base de datos y tablas de Catálogo creadas correctamente.")

    except Error as e:
        print("[ERROR] Al configurar la base de datos:", e)
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    setup_catalogo()
