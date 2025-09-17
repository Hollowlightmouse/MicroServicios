import mysql.connector
import uuid, json, logging
from mysql.connector import Error
from jwt_utils import generate_token, validate_token, has_role
from pythonjsonlogger import jsonlogger
import threading

# ===============================
# Configuración del logger
# ===============================
logger = logging.getLogger("orquestador")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Variable para almacenar el request_id en contexto local de hilo
thread_local = threading.local()

def set_request_id(request_id):
    thread_local.request_id = request_id

def get_request_id():
    return getattr(thread_local, 'request_id', None)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True

logger.addFilter(RequestIdFilter())

# ===============================
# Conexión a BD
# ===============================
def conectar_bd(host, user, password, database):
    return mysql.connector.connect(
        host=host,
        user=user,
        password= "YES",
        database=database
    )

# Conexiones globales
pedidos_db = conectar_bd("localhost", "root", "", "PedidosDB")
inventario_db = conectar_bd("localhost", "root", "", "InventarioDB")
pagos_db = conectar_bd("localhost", "root", "", "PagosDB")
catalogo_db = conectar_bd("localhost", "root", "", "CatalogoDB")

# ===============================
# Funciones auxiliares
# ===============================
def check_or_create_cliente(cliente_id):
    c = pedidos_db.cursor()
    c.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (cliente_id,))
    if not c.fetchone():
        c.execute(
            "INSERT INTO clientes (id_cliente, nombre, correo) VALUES (%s, %s, %s)",
            (cliente_id, f'Cliente {cliente_id}', f'cliente{cliente_id}@example.com')
        )
        pedidos_db.commit()
    c.close()

def log_evento(pedido_id, servicio, accion, estado='pendiente', mensaje=None):
    c = pedidos_db.cursor()
    c.execute("""
        INSERT INTO eventos_saga (id_pedido, servicio, accion, estado_evento, mensaje)
        VALUES (%s, %s, %s, %s, %s)
    """, (pedido_id, servicio, accion, estado, mensaje))
    pedidos_db.commit()
    eid = c.lastrowid
    c.close()
    return eid

def update_evento(evento_id, estado, mensaje=None):
    c = pedidos_db.cursor()
    c.execute("UPDATE eventos_saga SET estado_evento=%s, mensaje=%s WHERE id_evento=%s",
              (estado, mensaje, evento_id))
    pedidos_db.commit()
    c.close()

# ===== IDEMPOTENCIA =====
def already_processed(conn, request_id):
    c = conn.cursor()
    c.execute("SELECT 1 FROM processed_requests WHERE request_id=%s", (request_id,))
    exists = c.fetchone() is not None
    c.close()
    return exists

def mark_processed(conn, request_id, servicio):
    c = conn.cursor()
    c.execute("INSERT INTO processed_requests (request_id, servicio) VALUES (%s, %s)",
              (request_id, servicio))
    conn.commit()
    c.close()

# ===== OUTBOX =====
def add_outbox_event(conn, aggregate_type, aggregate_id, event_type, payload):
    c = conn.cursor()
    c.execute("""
        INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
        VALUES (%s, %s, %s, %s)
    """, (aggregate_type, str(aggregate_id), event_type, json.dumps(payload)))
    conn.commit()
    c.close()

# ===============================
# Decorador para validar token y roles
# ===============================
def requires_auth(role=None):
    def decorator(func):
        def wrapper(token, *args, **kwargs):
            try:
                payload = validate_token(token)
                if role and not has_role(payload, role):
                    logger.error("Acceso denegado: rol insuficiente")
                    return False
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Autenticación fallida: {e}")
                return False
        return wrapper
    return decorator

# ===============================
# Función de login simulada
# ===============================
def login(user_id):
    # En un caso real, validar credenciales antes de generar token
    roles = ["cliente"] if user_id != "admin" else ["admin"]
    token = generate_token(user_id, roles)
    logger.info(f"Token generado para usuario {user_id}: {token}")
    return token

# ===============================
# Función principal de la reserva protegida con JWT
# ===============================
@requires_auth(role="cliente")
def procesar_reserva_protegida(cliente_id, id_cancha, monto):
    return procesar_reserva(cliente_id, id_cancha, monto)

# ===============================
# Función principal de la reserva (sin cambios)
# ===============================
def procesar_reserva(cliente_id, id_cancha, monto):
    pedido_created = False
    cancha_reserved = False
    pago_inserted = False
    pedido_id = None

    # ==== idempotencia ====
    request_id = str(uuid.uuid4())
    set_request_id(request_id)
    if already_processed(pedidos_db, request_id):
        logger.info("Saga ya procesada. Abortando.")
        return False
    mark_processed(pedidos_db, request_id, "ORQUESTADOR")

    try:
        # Verificar cliente
        check_or_create_cliente(cliente_id)

        c_pedidos = pedidos_db.cursor()
        c_inventario = inventario_db.cursor()
        c_pagos = pagos_db.cursor()

        # ===== 1. Crear pedido =====
        c_pedidos.execute(
            "INSERT INTO pedidos (id_cliente, estado_id, total) VALUES (%s, %s, %s)",
            (cliente_id, 1, monto)
        )
        pedidos_db.commit()
        pedido_id = c_pedidos.lastrowid
        pedido_created = True
        logger.info(f"Pedido creado {pedido_id}")

        add_outbox_event(
            pedidos_db, "pedido", pedido_id, "PEDIDO_CREADO",
            {"pedido_id": pedido_id, "cliente_id": cliente_id, "monto": float(monto)}
        )

        # ===== 2. Reservar cancha =====
        evento_cancha = log_evento(pedido_id, "INVENTARIO", "RESERVAR", "pendiente")
        c_inventario.execute(
            "UPDATE canchas SET Estado=0 WHERE id_canchas=%s AND Estado=1",
            (id_cancha,)
        )
        if c_inventario.rowcount == 0:
            update_evento(evento_cancha, "fallido", "Cancha no disponible")
            raise Exception("Cancha no disponible")
        inventario_db.commit()
        cancha_reserved = True
        update_evento(evento_cancha, "exitoso")
        logger.info(f"Cancha {id_cancha} reservada")

        add_outbox_event(
            inventario_db, "cancha", id_cancha, "CANCHA_RESERVADA",
            {"pedido_id": pedido_id, "cancha_id": id_cancha}
        )

        # ===== 3. Registrar pago =====
        evento_pago = log_evento(pedido_id, "PAGO", "PAGAR", "pendiente")
        c_pagos.execute(
            "INSERT INTO transacciones (id_pedido, monto, estado, metodo_pago) VALUES (%s,%s,%s,%s)",
            (pedido_id, monto, "pagado", "efectivo")
        )
        pagos_db.commit()
        pago_inserted = True
        update_evento(evento_pago, "exitoso")
        logger.info("Pago registrado")

        add_outbox_event(
            pagos_db, "transaccion", pedido_id, "PAGO_CREADO",
            {"pedido_id": pedido_id, "monto": float(monto), "estado": "pagado"}
        )

        # Actualizar pedido a completado
        c_pedidos.execute("UPDATE pedidos SET estado_id=3 WHERE id_pedido=%s", (pedido_id,))
        pedidos_db.commit()
        logger.info("=== Saga completada con éxito ===")
        return True

    except Exception as e:
        logger.error(f"Fallo en saga: {e}")
        # Compensaciones
        if pedido_created and pedido_id:
            c_pedidos.execute("UPDATE pedidos SET estado_id=4 WHERE id_pedido=%s", (pedido_id,))
            pedidos_db.commit()
            log_evento(pedido_id, "PEDIDO", "COMPENSAR", "exitoso")

        if cancha_reserved:
            c_inventario.execute("UPDATE canchas SET Estado=1 WHERE id_canchas=%s", (id_cancha,))
            inventario_db.commit()
            log_evento(pedido_id, "INVENTARIO", "COMPENSAR", "exitoso")

        if pago_inserted:
            c_pagos.execute("UPDATE transacciones SET estado='reembolsado' WHERE id_pedido=%s", (pedido_id,))
            pagos_db.commit()
            log_evento(pedido_id, "PAGO", "COMPENSAR", "exitoso")

        return False

# ===============================
# Tests
# ===============================
if __name__ == "__main__":
    # Simular login y obtener token
    token_cliente = login("cliente1")
    token_admin = login("admin")

    # Usar token para procesar reserva
    logger.info("\nIntentando procesar reserva con token cliente:")
    procesar_reserva_protegida(token_cliente, 1, 1, 75000)  # cancha libre

    logger.info("\nIntentando procesar reserva con token admin (sin rol cliente):")
    procesar_reserva_protegida(token_admin, 1, 2, 75000)  # cancha ocupada

    pedidos_db.close()
    inventario_db.close()
    pagos_db.close()
    catalogo_db.close()
