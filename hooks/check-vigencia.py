#!/usr/bin/env python3
"""
Dispara el chequeo de vigencia normativa cuando el prompt es sobre legales.

Por qué existe: la instrucción de "verificar vigencia antes de escribir" ya está
en el SKILL.md, pero depende de que el modelo la lea y la obedezca. Este hook la
convierte en algo determinístico, y además aporta el dato que el modelo no puede
calcular solo: cuántos días pasaron desde que cada tabla se verificó contra
fuente primaria.

Un modelo no sabe qué día es en relación con la fecha escrita en un archivo. El
hook sí, y por eso el tono del aviso escala con la antigüedad real.

Entrada: JSON por stdin con `user_prompt` (formato de UserPromptSubmit).
Salida: JSON con `systemMessage`, o nada si el prompt no es sobre legales.
"""

import json
import os
import re
import sys
from datetime import date

# Umbrales en días desde la última verificación contra fuente.
# 180 no es arbitrario: en los 18 meses previos a la primera verificación
# cambiaron tres normas centrales solo en Argentina.
TIBIO = 90
VIEJO = 180

DISPARADORES = [
    # Español
    r"t[eé]rminos y condiciones", r"pol[ií]tica de privacidad", r"pol[ií]tica de seguridad",
    r"bot[oó]n de arrepentimiento", r"bot[oó]n de baja", r"legales", r"habeas data",
    r"ley 25\.?326", r"aaip", r"anpd", r"datos personales", r"defensa del consumidor",
    r"cl[aá]usulas? contractuales?", r"encargad[oa] de tratamiento", r"encarregado",
    # Inglés
    r"terms (of service|and conditions)", r"privacy polic", r"security polic",
    r"data protection", r"gdpr", r"rgpd", r"lgpd", r"ccpa", r"cpra", r"bipa", r"tcpa",
    r"\bdpo\b", r"\bdpa\b", r"data processing agreement", r"cookie (banner|consent)",
    r"right to be forgotten", r"subject access request", r"\bico\b",
    # Preguntas típicas que también deberían disparar
    r"puedo grabar", r"can i record", r"record (these |this )?calls?",
    r"cumplo con", r"am i compliant", r"compliance",
]

PATRON = re.compile("|".join(DISPARADORES), re.IGNORECASE)

NOMBRES = {
    "ar": "🇦🇷 Argentina", "eu": "🇪🇺 Unión Europea", "us": "🇺🇸 Estados Unidos",
    "br": "🇧🇷 Brasil", "uk": "🇬🇧 Reino Unido",
}


def leer_fechas(raiz):
    """Extrae la fecha de verificación del encabezado de cada tabla normativa."""
    ref = os.path.join(raiz, "skills", "legal-docs", "references")
    fechas = {}
    try:
        archivos = sorted(os.listdir(ref))
    except OSError:
        return fechas
    for nombre in archivos:
        m = re.fullmatch(r"normativa-([a-z]{2})\.md", nombre)
        if not m:
            continue
        try:
            with open(os.path.join(ref, nombre), encoding="utf-8") as f:
                cabecera = f.read(1200)
        except OSError:
            continue
        # "> **Verificado contra fuente el 2026-08-18**" y variantes
        f_m = re.search(r"[Vv]erificad[oa][^\n]*?(\d{4})-(\d{2})-(\d{2})", cabecera)
        if f_m:
            fechas[m.group(1)] = date(*map(int, f_m.groups()))
    return fechas


def main():
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = entrada.get("user_prompt") or ""
    if not PATRON.search(prompt):
        return 0  # No es sobre legales: no molestar.

    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    fechas = leer_fechas(raiz)
    if not fechas:
        return 0

    hoy = date.today()
    filas, mas_viejo = [], 0
    for codigo, fecha in sorted(fechas.items(), key=lambda x: x[1]):
        dias = (hoy - fecha).days
        mas_viejo = max(mas_viejo, dias)
        marca = "🔴" if dias > VIEJO else ("🟡" if dias > TIBIO else "🟢")
        filas.append(f"  {marca} {NOMBRES.get(codigo, codigo.upper()):<22} "
                     f"verificada {fecha.isoformat()}  ({dias} días)")

    if mas_viejo > VIEJO:
        encabezado = (
            f"⚠️ ALTO: la tabla más antigua tiene {mas_viejo} días sin verificar. "
            "Muy probablemente algo haya cambiado. Verificá contra fuente primaria "
            "ANTES de escribir, y avisale al usuario que el material puede estar viejo."
        )
    elif mas_viejo > TIBIO:
        encabezado = (
            f"La tabla más antigua tiene {mas_viejo} días. Correr § Verificación "
            "obligatoria antes de escribir."
        )
    else:
        encabezado = (
            "Las tablas son recientes, pero la verificación sigue siendo obligatoria: "
            "una norma puede cambiar cualquier día."
        )

    mensaje = (
        "[legal-docs] Este pedido parece ser sobre documentos legales.\n\n"
        f"{encabezado}\n\n"
        "Estado de las tablas normativas:\n" + "\n".join(filas) + "\n\n"
        "Antes de escribir una sola línea de texto legal:\n"
        "  1. Determinar la jurisdicción — NO se deduce del código. Preguntarla.\n"
        "  2. Correr § Verificación obligatoria de cada tabla que aplique.\n"
        "  3. Leer el producto: esquema, proveedores y su país, píxeles, flujo de baja.\n"
        "  4. No prometer nada que el código no haga.\n\n"
        "Si alguna tabla resultó desactualizada, corregir el archivo con la fecha nueva "
        "además de avisarle al usuario."
    )

    json.dump({"systemMessage": mensaje, "suppressOutput": True}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
