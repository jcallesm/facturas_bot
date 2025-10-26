from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from datetime import datetime
import unicodedata

app = FastAPI()

tickets = {}
contador = 1
usuarios_estados = {}
usuarios_datos = {}

def normalizar(texto: str) -> str:
    texto = texto.strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )  # quita tildes
    return texto

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    global contador
    mensaje_original = Body.strip()
    mensaje = normalizar(mensaje_original)
    estado = usuarios_estados.get(From)

    print(f"📩 Mensaje recibido de {From}: '{mensaje_original}' → Normalizado: '{mensaje}'")
    print(f"📊 Estado actual: {estado}")

    # ---------------------- Paso 0: Inicio ----------------------
    if estado is None:
        usuarios_estados[From] = "concepto"
        usuarios_datos[From] = {}
        return PlainTextResponse(
            "👋 Hola, soy Trancos, tu asistente para gestionar tickets." \
            "\nVamos a crear un nuevo ticket." \
            "\nPor favor, escriba el **concepto** del ticket: " \
            "\n1️⃣ COMPRA"
            "\n2️⃣ VENTA"
            "\n3️⃣  OTRO"
        )

    # ---------------------- Paso 1: Concepto ----------------------
    if estado == "concepto":
        if mensaje in ["compra", "venta", "1", "2"]:
            usuarios_datos[From]["concepto"] = mensaje.capitalize()
            usuarios_estados[From] = "estatus_pago"
            print(f"✅ Concepto registrado: {mensaje}")
            return PlainTextResponse(
                "✅ Entendido. Ahora escriba el **estatus de pago**:" \
                "\n1️⃣ PAGADO" \
                "\n2️⃣ NO PAGADO" \
                "\n3️⃣ PAGO PARCIAL"
            )
        elif mensaje == "otro":
            usuarios_estados[From] = "concepto_otro"
            return PlainTextResponse("✏️ Escriba el concepto personalizado del ticket:")
        else:
            print("⚠️ No entendí el concepto.")
            return PlainTextResponse("❌ No entendí. Escriba 'COMPRA', 'VENTA' u 'OTRO'.")

    # ---------------------- Paso 1B: Concepto personalizado ----------------------
    elif estado == "concepto_otro":
        usuarios_datos[From]["concepto"] = mensaje.capitalize()
        usuarios_estados[From] = "estatus_pago"
        return PlainTextResponse(
            "Perfecto. Ahora escriba el **estatus de pago**:" \
            "\n1️⃣ PAGADO"
            "\n2️⃣ NO PAGADO"
            "\n3️⃣ PAGO PARCIAL"
        )

    # ---------------------- Paso 2: Estatus de pago ----------------------
    elif estado == "estatus_pago":
        opciones = {"1": "PAGADO", "2": "NO PAGADO", "3": "PAGO PARCIAL"}
        if mensaje not in opciones and mensaje not in ["pagado", "no pagado", "pago parcial"]:
            return PlainTextResponse("❌ Opción inválida. Escriba PAGADO, NO PAGADO, PAGO PARCIAL, 1, 2 ò 3.")
        
        estatus = opciones.get(mensaje, mensaje.upper())
        usuarios_datos[From]["estatus_pago"] = estatus

        if estatus == "PAGADO":
            usuarios_estados[From] = "importe_total"
            return PlainTextResponse("💰 Ingresa el **importe total** (solo números).")
        elif estatus == "NO PAGADO":
            usuarios_estados[From] = "importe_por_cobrar"
            return PlainTextResponse("💰 Ingresa el **importe por cobrar** (solo números).")
        elif estatus == "PAGO PARCIAL":
            usuarios_estados[From] = "importe_parcial"
            return PlainTextResponse("💰 Ingresa el **importe parcial pagado** (solo números).")

    # ---------------------- Paso 3A: Importe total ----------------------
    elif estado == "importe_total":
        if not mensaje.replace(".", "", 1).isdigit():
            return PlainTextResponse("❌ Ingrese solo números o decimales válidos (ejemplo: 120 o 89.50).")
        usuarios_datos[From]["importe_total"] = float(mensaje)
        usuarios_datos[From]["por_cobrar"] = 0.0
        usuarios_estados[From] = "comentarios"
        return PlainTextResponse("📝 ¿Quiere agregar algún comentario (lugar, orden, etc)?" \
        "\n1️⃣ NO"
        "\n2️⃣ SÍ, escribir comentario.")

    # ---------------------- Paso 3B: Importe por cobrar ----------------------
    elif estado == "importe_por_cobrar":
        if not mensaje.replace(".", "", 1).isdigit():
            return PlainTextResponse("❌ Ingrese solo números o decimales válidos.")
        usuarios_datos[From]["importe_total"] = 0.0
        usuarios_datos[From]["por_cobrar"] = float(mensaje)

        usuarios_estados[From]='informacion_cliente'
        return PlainTextResponse("📞¿Quiere agregar información del cliente (nombre, contacto, etc)? " \
        "\n1️⃣ NO"
        "\n2️⃣ SÍ, escribir información.") 
        
        usuarios_estados[From] = "comentarios"
        return PlainTextResponse("📝 ¿Quieres agregar algún comentario (lugar, orden, etc)?\n1️⃣ No\n2️⃣ Sí, escribir comentario.")

    # ---------------------- Paso 3C: Pago parcial ----------------------
    elif estado == "importe_parcial":
        if not mensaje.replace(".", "", 1).isdigit():
            return PlainTextResponse("❌ Ingrese solo números o decimales válidos.")
        usuarios_datos[From]["importe_parcial"] = float(mensaje)
        usuarios_estados[From] = "importe_total_parcial"
        return PlainTextResponse("💵 Ingrese el **importe total del ticket** (solo números).")

    elif estado == "importe_total_parcial":
        if not mensaje.replace(".", "", 1).isdigit():
            return PlainTextResponse("❌ Ingrese solo números o decimales válidos.")
        total = float(mensaje)
        parcial = usuarios_datos[From]["importe_parcial"]
        usuarios_datos[From]["importe_total"] = total
        usuarios_datos[From]["por_cobrar"] = round(total - parcial,2)

        usuarios_estados[From]='informacion_cliente'
        return PlainTextResponse("📞¿Quiere agregar información del cliente (nombre, contacto, etc)? " \
        "\n1️⃣ NO" \
        "\n2️⃣ SÍ, escribir información.") 

        usuarios_estados[From] = "comentarios"
        return PlainTextResponse("📝 ¿Quieres agregar algún comentario (lugar, orden, etc)?" \
        "\n1️⃣ NO"
        "\n2️⃣ SÍ, escribir comentario.")
    
    # ---------------------- Paso 4: Información del cliente ----------------------
    elif estado == "informacion_cliente":
        if mensaje in ["1", "no"]:
            usuarios_datos[From]["informacion_cliente"] = "Sin información del cliente"
            usuarios_estados[From] = "comentarios"
            return PlainTextResponse("📝 ¿Quieres agregar algún comentario (lugar, orden, etc)?" \
            "\n1️⃣ NO" \
            "\n2️⃣ SÍ, escribir comentario.")
        elif mensaje in ["2", "si", "sí", "s"]:
            usuarios_estados[From] = "informacion_cliente_texto"
            return PlainTextResponse("✏️ Escribe la información del cliente que deseas agregar.")
        else:
            usuarios_datos[From]["informacion_cliente"] = mensaje
            usuarios_estados[From] = "comentarios"

    # ---------------------- Paso 5: Comentarios ----------------------
    elif estado == "comentarios":
        if mensaje in ["1", "no"]:
            usuarios_datos[From]["comentarios"] = "Sin comentarios"
            return crear_ticket(From)
        elif mensaje in ["2", "si", "sí", "s"]:
            usuarios_estados[From] = "comentario_texto"
            return PlainTextResponse("✏️ Escribe el comentario que deseas agregar.")
        else:
            usuarios_datos[From]["comentarios"] = mensaje
            return crear_ticket(From)

    elif estado == "comentario_texto":
        usuarios_datos[From]["comentarios"] = mensaje
        return crear_ticket(From)

    else:
        usuarios_estados[From] = "concepto"
        return PlainTextResponse("Vamos a crear un nuevo ticket. Escribe 'COMPRA', 'VENTA' u 'OTRO'.")


def crear_ticket(From):
    global contador
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_id = datetime.now().strftime("%Y%m%d")
    concepto = usuarios_datos[From]["concepto"]
    ticket_id = f"{concepto[0].upper()}-{fecha_id}-{contador:03d}"

    ticket = {
        "id": ticket_id,
        "fecha_creacion": fecha_creacion,
        "concepto": concepto,
        "estatus_pago": usuarios_datos[From]["estatus_pago"],
        "importe_total": usuarios_datos[From].get("importe_total", 0.0),
        "por_cobrar": usuarios_datos[From].get("por_cobrar", 0.0),
        "comentarios": usuarios_datos[From].get("comentarios", "Sin comentarios"),
        "cliente": usuarios_datos[From].get("informacion_cliente", "Sin información del cliente")
    }

    tickets[ticket_id] = ticket
    contador += 1
    usuarios_estados.pop(From, None)
    usuarios_datos.pop(From, None)

    print(f"✅ Ticket creado: {ticket_id}")
    return PlainTextResponse(
        f"✅ Ticket creado con éxito.\n\n"
        f"🧾 *ID:* {ticket['id']}\n"
        f"📅 *Fecha:* {ticket['fecha_creacion']}\n"
        f"📘 *Concepto:* {ticket['concepto']}\n"
        f"💰 *Importe total:* ${ticket['importe_total']:,.2f}\n"
        f"💸 *Por cobrar:* ${ticket['por_cobrar']:,.2f}\n"
        f"📊 *Estatus:* {ticket['estatus_pago']}\n"
        f"📞 *Cliente:* {ticket['cliente']}\n"
        f"🗒️ *Comentarios:* {ticket['comentarios']}"
    )
