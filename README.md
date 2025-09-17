
# MICROSERVICIOS PARA RESERVAS CANCHA DE FUTBOL

Este repositorio contiene una sección de microservicios para un programa de **reservación de canchas de fútbol**.  
El sistema está diseñado bajo una arquitectura de **microservicios**, donde cada módulo se encarga de una función específica (catálogo, inventario, pedidos y pagos), logrando una solución **escalable y mantenible**.


ESTRUCTURA DEL PROYECTO
=

MicroServicios:
- Catálogo/  (Carpeta)              -> Servicio para gestión de canchas y su información
- Inventario/ (Carpeta)             -> Servicio para controlar disponibilidad de canchas
-  Pago/   (Carpeta)                 -> Servicio para manejar pagos
- Pedidos/ (Carpeta)               -> Servicio para gestionar reservas de los usuarios
-  docker-compose.yml      -> Configuración para levantar los servicios con Docker
- inventario_consumer.py  -> Consumidor de mensajes del servicio Inventario
- jwt_utils.py            -> Funciones para creación y verificación de JWT
-  orquestador.py          -> Punto de inicio del sistema que coordina los servicios
- outbox_worker.py        -> Trabajador que maneja eventos pendientes (patrón outbox)


ARCHIVOS Y SU FUNCIÓN MAS DETALLADO
=

- Catálogo/  
  -> Maneja la información de las canchas disponibles (tipo de cancha, precio).

- Inventario/  
  -> Controla la disponibilidad de canchas y reservas.

- Pago/  
  -> Procesa los pagos de las reservas.

- Pedidos/  
  -> Gestiona las solicitudes o reservas de los clientes.

- jwt_utils.py  
  -> Funciones para generar y validar tokens JWT (autenticación).

- orquestador.py  
  -> Archivo principal que orquesta los microservicios y coordina el flujo del sistema.

- inventario_consumer.py  
  -> Escucha eventos de inventario desde RabbitMQ (mensajería).

- outbox_worker.py  
  -> Implementa el patrón Outbox para enviar eventos pendientes a otros servicios.

- docker-compose.yml  
  -> Configuración de servicios auxiliares como RabbitMQ y base de datos.


CÓMO CLONAR EL REPOSITORIO
=

1. Abre tu terminal o consola.
2. Ejecuta los siguientes comandos:

    - git clone https://github.com/Hollowlightmouse/MicroServicios.git
    - cd MicroServicios


LIBRERÍAS NECESARIAS
=

Asegúrate de instalar las siguientes dependencias:

- Flask  
    pip install flask  
    -> Framework web para crear servicios REST en Python. Permite definir rutas y exponer microservicios.

- Requests  
    pip install requests  
    -> Librería para hacer peticiones HTTP entre microservicios (ejemplo: el orquestador consulta el inventario).

- PyJWT  
    pip install PyJWT  
    -> Permite generar y validar JSON Web Tokens (JWT) para la autenticación de usuarios.

- Pika  
    pip install pika  
    -> Cliente de Python para RabbitMQ. Se usa para enviar y consumir mensajes entre microservicios.


CÓMO INICIAR EL PROGRAMA
=

1. Instala las librerías necesarias con pip.
2. Si usas Docker, primero levanta los servicios con:

    docker-compose up

   Esto pondrá en marcha dependencias como RabbitMQ.

3. Ejecuta el archivo principal:

    - python orquestador.py

   Esto iniciará el sistema de microservicios y coordinará la comunicación entre ellos.



- Los microservicios se comunican por HTTP (usando requests) y por mensajería con RabbitMQ (usando pika).

COLABORADORES
=
- Johan Lopez
- J3ST
- JULIAN CORREA
- Keta787
