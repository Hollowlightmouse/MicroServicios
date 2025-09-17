import mysql.connector as msql
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YES"
}

DB_NAME = "InventarioDB"

def setup_inventario():
    try:
        connection = msql.connect(**DB_CONFIG)

        if connection.is_connected():
            print("[INFO] Conexión establecida con MySQL.")
            cursor = connection.cursor()

            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")

            # Tabla inventario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id_inventario INT AUTO_INCREMENT PRIMARY KEY,
                    id_producto INT NOT NULL,
                    stock_actual INT NOT NULL DEFAULT 0,
                    stock_reservado INT NOT NULL DEFAULT 0, -- cantidad apartada para pedidos
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS canchas (
                id_canchas INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL,
                Estado TINYINT(1) NOT NULL DEFAULT 1  -- 1 = disponible, 0 = reservada
            )
            """)

            # Insertar canchas de prueba
            cursor.execute("""
                INSERT IGNORE INTO canchas (id_canchas, nombre, Estado)
                VALUES (1, 'Cancha 1', 1), (2, 'Cancha 2', 0), (3, 'Cancha 3', 1)
            """)

            # Historial de movimientos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movimientos_inventario (
                    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
                    id_producto INT NOT NULL,
                    tipo_movimiento ENUM('entrada', 'salida', 'reserva', 'liberacion') NOT NULL,
                    cantidad INT NOT NULL,
                    referencia VARCHAR(100) NULL, -- ej: id_pedido
                    fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP
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
            print("[INFO] Base de datos y tablas de Inventario creadas correctamente.")

    except Error as e:
        print("[ERROR] Al configurar la base de datos:", e)
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    setup_inventario()
