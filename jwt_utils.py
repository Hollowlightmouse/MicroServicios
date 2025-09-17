import jwt
import datetime

# Clave secreta para firmar los tokens (en producción usar variable de entorno)
SECRET_KEY = "mi_clave_secreta_muy_segura"

def generate_token(user_id, roles, expires_in=3600):
    """
    Genera un token JWT con user_id y roles.
    :param user_id: Identificador del usuario
    :param roles: Lista de roles (ej. ['cliente', 'admin'])
    :param expires_in: Tiempo de expiración en segundos (default 1 hora)
    :return: token JWT como string
    """
    payload = {
        "sub": user_id,
        "roles": roles,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def validate_token(token):
    """
    Valida un token JWT y retorna el payload si es válido.
    Lanza excepción si es inválido o expirado.
    :param token: token JWT como string
    :return: payload dict
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expirado")
    except jwt.InvalidTokenError:
        raise Exception("Token inválido")

def has_role(payload, role):
    """
    Verifica si el payload contiene el rol especificado.
    :param payload: payload decodificado del token
    :param role: rol a verificar (string)
    :return: True si tiene el rol, False si no
    """
    return role in payload.get("roles", [])
