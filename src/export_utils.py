"""Exportación de la lista de la compra a texto plano."""


def exportar_a_texto(datos: dict, estado_checks: dict) -> str:
    lineas = ["LISTA DE LA COMPRA", "=" * 30, ""]
    for categoria in datos.get("categorias", []):
        nombre = categoria.get("nombre", "Sin categoría")
        lineas.append(f"## {nombre}")
        for item in categoria.get("items", []):
            clave = f"{nombre}|{item['ingrediente']}"
            marcado = "x" if estado_checks.get(clave) else " "
            lineas.append(f"[{marcado}] {item['ingrediente']} - {item['cantidad']}")
        lineas.append("")
    return "\n".join(lineas)
