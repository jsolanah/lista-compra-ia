"""Autenticacion de usuarios mediante Supabase Auth."""

from src.config import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL


def _obtener_cliente_auth():
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError(
            "Faltan SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY para usar la autenticacion."
        )
    try:
        from supabase import create_client
    except ImportError as error:
        raise RuntimeError(
            "Falta instalar la dependencia supabase. Ejecuta: pip install -r requirements.txt"
        ) from error
    return create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)


def _datos_usuario(usuario) -> dict:
    return {
        "user_id": usuario.id,
        "email": usuario.email or "",
    }


def iniciar_sesion(email: str, password: str) -> dict:
    respuesta = _obtener_cliente_auth().auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    if respuesta.user is None:
        raise RuntimeError("No se ha podido iniciar la sesion.")
    return _datos_usuario(respuesta.user)


def registrar_usuario(email: str, password: str) -> dict | None:
    respuesta = _obtener_cliente_auth().auth.sign_up(
        {"email": email, "password": password}
    )
    if respuesta.user is None:
        raise RuntimeError("No se ha podido crear el usuario.")
    if respuesta.session is None:
        return None
    return _datos_usuario(respuesta.user)
