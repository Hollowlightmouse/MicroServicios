import mysql.connector as msql
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": 'YES'
}

DB_NAME = "PedidosDB"

def setup_pedidos():
    try:
        connection = msql.connect(**DB_CONFIG)

        if connection.is_connected():
            print("[INFO] Conexión establecida con MySQL.")
            cursor = connection.cursor()

            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            cursor.execute(f"USE {DB_NAME}")

            # 1. Clientes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    correo VARCHAR(100) UNIQUE NOT NULL,
                    telefono VARCHAR(20) NULL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Estados del pedido
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS estados_pedido (
                    id_estado INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_estado VARCHAR(50) NOT NULL,
                    descripcion VARCHAR(150) NULL
                )
            """)

            # Insertar estados iniciales
            cursor.execute("""
                INSERT IGNORE INTO estados_pedido (id_estado, nombre_estado, descripcion)
                VALUES
                (1, 'pendiente', 'Pedido creado, en espera de procesamiento'),
                (2, 'confirmado', 'Pedido confirmado y en proceso'),
                (3, 'completado', 'Pedido completado con éxito'),
                (4, 'cancelado', 'Pedido cancelado por error en la saga')
            """)

            # Insertar cliente de prueba
            cursor.execute("""
                INSERT IGNORE INTO clientes (id_cliente, nombre, correo)
                VALUES (1, 'Cliente Test', 'test@example.com')
            """)

            # 3. Pedidos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
                    id_cliente INT NOT NULL,
                    estado_id INT NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
                    FOREIGN KEY (estado_id) REFERENCES estados_pedido(id_estado)
                )
            """)

            # 4. Detalle de pedidos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_pedidos (
                    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
                    id_pedido INT NOT NULL,
                    id_producto INT NOT NULL,
                    cantidad INT NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
                )
            """)

            # 5. Eventos de la saga
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos_saga (
                    id_evento INT AUTO_INCREMENT PRIMARY KEY,
                    id_pedido INT NOT NULL,
                    servicio VARCHAR(50) NOT NULL, -- INVENTARIO, PAGO, PEDIDO
                    accion VARCHAR(50) NOT NULL,  -- RESERVAR, COMPENSAR, CONFIRMAR
                    estado_evento ENUM('pendiente', 'exitoso', 'fallido') NOT NULL DEFAULT 'pendiente',
                    mensaje VARCHAR(255) NULL,
                    fecha_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
                )
            """)

            # 6. Tabla para idempotencia
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_requests (
                    request_id VARCHAR(36) PRIMARY KEY,
                    servicio VARCHAR(50) NOT NULL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 7. Tabla para outbox
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
            print("[INFO] Base de datos y tablas de Pedidos creadas correctamente.")

    except Error as e:
        print("[ERROR] Al configurar la base de datos:", e)
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("[INFO] Conexión cerrada.")

if __name__ == "__main__":
    setup_pedidos()
