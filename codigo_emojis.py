from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from datetime import datetime
import traceback

# 🚀 Inicializamos la app FastAPI
app = FastAPI()

# 📂 Diccionario para guardar tickets en memoria (puedes cambiarlo a una BD después)
tickets = {}

# 🧮 Contador para generar IDs únicos de tickets
contador = 1

# 🧭 Diccionarios para controlar el flujo de cada usuario
usuarios_estados = {}  # Guarda en qué paso va cada usuario
usuarios_datos = {}    # Guarda la información temporal que va proporcionando

# 🕒 Función auxiliar para obtener la hora actual formateada
def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 📅 Función auxiliar para obtener la fecha actual
def today():
    return datetime.now().strftime("%Y-%m-%d")


@app.api_route("/whatsapp", methods=["POST", "GET"])
async def whatsapp_webhook(
    request: Request,
    From: str = Form(None),
    Body: str = Form(None)
):
    """
    📬 Webhook principal que Twilio llama cuando llega un mensaje de WhatsApp.
    - From: número del usuario
    - Body: mensaje de texto recibido
    """
    global contador
    try:
        # ✅ Aseguramos que solo responda a solicitudes POST
        if request.method != "POST":
            return Response(content="❌ Método no permitido", status_code=405)

        # 🧪 Validamos que Twilio haya enviado los campos esperados
        if From is None or Body is None:
            print("Faltan parámetros:", From, Body)
            return Response(content="❌ Parámetros incompletos", status_code=400)

        # ✍️ Normalizamos el texto del mensaje
        mensaje = Body.strip().lower()

        # 📊 Obtenemos el estado actual del usuario
        estado = usuarios_estados.get(From)

        print(f"📩 Mensaje recibido de {From}: '{mensaje}'")
        print(f"📊 Estado actual: {estado}")

        # ---------------------------------------------------------
        # PASO 0: Si es un nuevo usuario → pedir concepto
        # ---------------------------------------------------------
        if From not in usuarios_estados:
            usuarios_estados[From] = 'concepto'
            usuarios_datos[From] = {}
            return Response(
                content="👋 ¡Hola! Soy el bot de tickets.\n📝 Vamos a crear un nuevo ticket.\nPor favor, dime el **concepto**: COMPRA, VENTA u OTRO.",
                media_type="text/plain; charset=utf-8"
            )

        # ---------------------------------------------------------
        # PASO 1: Concepto (compra, venta u otro)
        # ---------------------------------------------------------
        if estado == 'concepto':
            if mensaje in ["compra", "venta"]:
                usuarios_datos[From]["concepto"] = mensaje.capitalize()
                usuarios_estados[From] = 'estatus_pago'
                return Response(
                    content="✅ Entendido.\n💳 Ahora dime el **estatus de pago**:\n1️⃣ PAGADO\n2️⃣ NO PAGADO\n3️⃣ PAGO PARCIAL",
                    media_type="text/plain; charset=utf-8"
                )
            elif mensaje == "otro":
                usuarios_estados[From] = "concepto_otro"
                return Response(
                    content="✍️ Por favor, escribe el concepto personalizado.",
                    media_type="text/plain; charset=utf-8"
                )
            else:
                return Response(
                    content="❌ No entendí.\nEscribe 'compra', 'venta' u 'otro'.",
                    media_type="text/plain; charset=utf-8"
                )

        # ---------------------------------------------------------
        # PASO 2: Concepto personalizado
        # ---------------------------------------------------------
        elif estado == 'concepto_otro':
            usuarios_datos[From]["concepto"] = mensaje.capitalize()
            usuarios_estados[From] = 'estatus_pago'
            return Response(
                content="✍️ Perfecto.\n💳 Ahora dime el **estatus de pago**:\n1️⃣ PAGADO\n2️⃣ NO PAGADO\n3️⃣ PAGO PARCIAL",
                media_type="text/plain; charset=utf-8"
            )

        # ---------------------------------------------------------
        # PASO 3: Estatus de pago
        # ---------------------------------------------------------
        elif estado == 'estatus_pago':
            opciones_estatus = {"1": "PAGADO", "2": "NO PAGADO", "3": "PAGO PARCIAL"}
            if mensaje in opciones_estatus or mensaje.upper() in opciones_estatus.values():
                estatus = opciones_estatus.get(mensaje, mensaje.upper())
                usuarios_datos[From]["estatus_pago"] = estatus

                if estatus == "PAGADO":
                    usuarios_estados[From] = 'importe_total'
                    return Response(content="💰 Ingresa el **importe total** (solo números).", media_type="text/plain; charset=utf-8")
                elif estatus == "NO PAGADO":
                    usuarios_estados[From] = "importe_por_cobrar"
                    return Response(content="💰 Ingresa el **importe por cobrar** (solo números).", media_type="text/plain; charset=utf-8")
                elif estatus == "PAGO PARCIAL":
                    usuarios_estados[From] = 'importe_parcial_pagado'
                    return Response(content="💰 Ingresa el **importe parcial pagado** (solo números).", media_type="text/plain; charset=utf-8")
            else:
                return Response(
                    content="❌ Opción inválida.\nEscribe PAGADO, NO PAGADO, PAGO PARCIAL, 1, 2 o 3.",
                    media_type="text/plain; charset=utf-8"
                )

        # ---------------------------------------------------------
        # PASO 4A: Importe total
        # ---------------------------------------------------------
        elif estado == 'importe_total':
            if not mensaje.replace(".", "", 1).isdigit():
                return Response(content="⚠️ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).", media_type="text/plain; charset=utf-8")

            importe = float(mensaje)
            usuarios_datos[From]["importe_total"] = importe

            # 🆔 Generamos ID único para el ticket
            ticket_id = f"{today()}-{contador:03d}"
            contador += 1

            # 🧾 Guardamos ticket
            ticket = {
                "fecha_creacion": current_time(),
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total": importe,
                "por_cobrar": 0.0,
                "cliente": From
            }
            tickets[ticket_id] = ticket

            # 🧼 Limpiamos estado temporal
            usuarios_estados.pop(From)
            usuarios_datos.pop(From)

            return Response(
                content=f"✅ Ticket creado con éxito.\n🧾 Concepto: {ticket['concepto']}\n💰 Importe total: ${ticket['importe_total']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}",
                media_type="text/plain; charset=utf-8"
            )

        # ---------------------------------------------------------
        # PASO 4B: Importe por cobrar
        # ---------------------------------------------------------
        elif estado == 'importe_por_cobrar':
            if not mensaje.replace(".", "", 1).isdigit():
                return Response(content="⚠️ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).", media_type="text/plain; charset=utf-8")

            importe = float(mensaje)
            usuarios_datos[From]["importe_por_cobrar"] = importe

            ticket_id = f"{today()}-{contador:03d}"
            contador += 1

            ticket = {
                "fecha_creacion": current_time(),
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total": 0.0,
                "por_cobrar": importe,
                "cliente": From
            }
            tickets[ticket_id] = ticket

            usuarios_estados.pop(From)
            usuarios_datos.pop(From)

            return Response(
                content=f"✅ Ticket creado con éxito.\n🧾 Concepto: {ticket['concepto']}\n💸 Por cobrar: ${ticket['por_cobrar']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}",
                media_type="text/plain; charset=utf-8"
            )

        # ---------------------------------------------------------
        # PASO 4C: Importe parcial pagado
        # ---------------------------------------------------------
        elif estado == 'importe_parcial_pagado':
            if not mensaje.replace(".", "", 1).isdigit():
                return Response(content="⚠️ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).", media_type="text/plain; charset=utf-8")

            importe = float(mensaje)
            usuarios_datos[From]["importe_parcial_pagado"] = importe

            ticket_id = f"{today()}-{contador:03d}"
            contador += 1

            ticket = {
                "fecha_creacion": current_time(),
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total": 0.0,
                "por_cobrar": 0.0,
                "parcial_pagado": importe,
                "cliente": From
            }
            tickets[ticket_id] = ticket

            usuarios_estados.pop(From)
            usuarios_datos.pop(From)

            return Response(
                content=f"✅ Ticket creado con éxito.\n🧾 Concepto: {ticket['concepto']}\n💵 Parcial pagado: ${ticket['parcial_pagado']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}",
                media_type="text/plain; charset=utf-8"
            )

        # ---------------------------------------------------------
        # Si no hay estado válido, reiniciamos el flujo
        # ---------------------------------------------------------
        else:
            usuarios_estados[From] = 'concepto'
            return Response(
                content="📌 Vamos a crear un nuevo ticket. Escribe 'compra', 'venta' u 'otro'.",
                media_type="text/plain; charset=utf-8"
            )

    except Exception as e:
        # 🧯 Capturamos errores para no romper la conversación con Twilio
        print("❌ Error en webhook:", e)
        traceback.print_exc()
        return Response(
            content="🚨 Hubo un error interno. Intenta nuevamente.",
            media_type="text/plain; charset=utf-8",
            status_code=200
        )
