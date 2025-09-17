import mysql.connector
import time, json
import pika

# Config DB
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YES"
}

# Config RabbitMQ
RABBITMQ_HOST = "localhost"
EXCHANGE_NAME = "saga"   # Exchange común para los eventos


# ===============================
# Funciones auxiliares
# ===============================
def conectar_bd(database):
    return mysql.connector.connect(**DB_CONFIG, database=database)

def get_rabbit_connection():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="fanout")
        return connection, channel
    except Exception as ex:
        print(f"[ERROR] No se pudo conectar a RabbitMQ: {ex}")
        return None, None

def publish_event(evento, service_name):
    connection, channel = get_rabbit_connection()
    if not connection or not channel:
        raise Exception("RabbitMQ no disponible")

    body = json.dumps(evento)
    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key="", body=body)
    print(f"[{service_name}] Publicado en RabbitMQ -> {body}")
    connection.close()

def publish_outbox_events(conn, service_name):
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM outbox WHERE published=0 LIMIT 10")
    eventos = c.fetchall()
    for e in eventos:
        try:
            # Validar payload
            try:
                payload = json.loads(e["payload"])
            except Exception as parse_err:
                print(f"[{service_name}] ERROR parseando JSON del evento {e['id']}: {parse_err}")
                continue

            evento = {
                "id": e["id"],
                "aggregate_type": e["aggregate_type"],
                "aggregate_id": e["aggregate_id"],
                "event_type": e["event_type"],
                "payload": payload,
                "service": service_name
            }

            # Publicar en RabbitMQ
            publish_event(evento, service_name)

            # Marcar como publicado
            c2 = conn.cursor()
            c2.execute("UPDATE outbox SET published=1, published_at=NOW() WHERE id=%s", (e["id"],))
            conn.commit()
            c2.close()

        except Exception as ex:
            print(f"[{service_name}] ERROR publicando evento {e['id']}: {ex}")
    c.close()


# ===============================
# Loop principal
# ===============================
if __name__ == "__main__":
    pedidos_db = conectar_bd("PedidosDB")
    inventario_db = conectar_bd("InventarioDB")
    pagos_db = conectar_bd("PagosDB")
    catalogo_db = conectar_bd("CatalogoDB")

    print("[WORKER] Iniciando publicación de eventos Outbox hacia RabbitMQ...")

    while True:
        try:
            publish_outbox_events(pedidos_db, "Pedidos")
            publish_outbox_events(inventario_db, "Inventario")
            publish_outbox_events(pagos_db, "Pagos")
            publish_outbox_events(catalogo_db, "Catalogo")
        except Exception as loop_err:
            print(f"[WORKER] Error en loop principal: {loop_err}")

        time.sleep(5)  # cada 5 segundos
