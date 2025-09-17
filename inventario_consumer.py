import pika
def callback(ch, method, properties, body):
    print("[Inventario] Recibido:", body.decode())
    # aquí actualizarías BD de Inventario

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='saga', exchange_type='fanout')
queue = channel.queue_declare(queue='', exclusive=True)
channel.queue_bind(exchange='saga', queue=queue.method.queue)

channel.basic_consume(queue=queue.method.queue, on_message_callback=callback, auto_ack=True)
print("[Inventario] Esperando mensajes...")
channel.start_consuming()
