import mysql.connector as msql
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YES"
}

DB_NAME = "PagosDB"

def setup_pagos():
    try:
        connection = msql.connect(**DB_CONFIG)

        if connection.is_connected():
            print("[INFO] Conexión establecida con MySQL.")
            cursor = connection.cursor()

            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")

            # Tabla transacciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transacciones (
                    id_transaccion INT AUTO_INCREMENT PRIMARY KEY,
                    id_pedido INT NOT NULL,
                    monto DECIMAL(10,2) NOT NULL,
                    estado ENUM('pendiente', 'pagado', 'fallido', 'reembolsado') NOT NULL DEFAULT 'pendiente',
                    metodo_pago VARCHAR(50) NOT NULL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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


            connection.commit()
            print("[INFO] Base de datos y tablas de Pagos creadas correctamente.")

    except Error as e:
        print("[ERROR] Al configurar la base de datos:", e)
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    setup_pagos()
