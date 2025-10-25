from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from datetime import datetime

app = FastAPI()

estados = {}
tickets_temp = {}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    numero = data.get("From", "").replace("whatsapp:", "")
    mensaje = data.get("Body", "").strip().lower()

    estado_actual = estados.get(numero)
    respuesta = ""

    # Paso 1: Inicio
    if estado_actual is None:
        respuesta = "👋 Hola, bienvenido al sistema de tickets.\nPor favor escribe el concepto del ticket."
        estados[numero] = "concepto"
        tickets_temp[numero] = {}
        return PlainTextResponse(respuesta)

    # Paso 2: Concepto
    if estado_actual == "concepto":
        tickets_temp[numero]["concepto"] = mensaje
        respuesta = "💰 Ingresa el monto del ticket:"
        estados[numero] = "monto"
        return PlainTextResponse(respuesta)

    # Paso 3: Monto
    if estado_actual == "monto":
        if mensaje.replace('.', '', 1).isdigit():
            tickets_temp[numero]["monto"] = float(mensaje)
            # 🔸 CAMBIO: nueva pregunta sobre estado de pago
            respuesta = "💳 Indica el estado de pago:\n1. Pagado\n2. No pagado\n3. Pago parcial"
            estados[numero] = "estado_pago"  # 🔸 CAMBIO: nuevo estado
        else:
            respuesta = "⚠️ Por favor ingresa un número válido para el monto."
        return PlainTextResponse(respuesta)

    # Paso 4: Estado de pago  🔸 CAMBIO NUEVO BLOQUE
    if estado_actual == "estado_pago":
        opciones_pago = {"1": "pagado", "2": "no pagado", "3": "pago parcial"}
        if mensaje in opciones_pago:
            tickets_temp[numero]["estado_pago"] = opciones_pago[mensaje]

            # 🔸 CAMBIO: Si es no pagado o pago parcial → preguntar cliente
            if mensaje in ["2", "3"]:
                respuesta = "👤 ¿Quieres agregar información del cliente?\n1. No\n2. Sí"
                estados[numero] = "cliente_opcion"  # 🔸 CAMBIO
            else:
                # Si es pagado → saltar a comentarios
                respuesta = "📝 ¿Quieres agregar algún comentario (cliente, lugar, orden, etc)?\n1. No\n2. Sí"
                estados[numero] = "comentario_opcion"
        else:
            respuesta = "⚠️ Opción inválida. Escribe 1, 2 o 3."
        return PlainTextResponse(respuesta)

    # Paso 5: Datos cliente (opcional)  🔸 CAMBIO NUEVO BLOQUE
    if estado_actual == "cliente_opcion":
        if mensaje in ["1", "no", "n"]:
            tickets_temp[numero]["cliente"] = ""  # 🔸 CAMBIO
            respuesta = "📝 ¿Quieres agregar algún comentario (cliente, lugar, orden, etc)?\n1. No\n2. Sí"
            estados[numero] = "comentario_opcion"
        elif mensaje in ["2", "sí", "si", "s"]:
            respuesta = "✍️ Escribe la información del cliente:"
            estados[numero] = "cliente_texto"  # 🔸 CAMBIO
        else:
            respuesta = "⚠️ Opción no válida. Escribe 1 para 'No' o 2 para 'Sí'."
        return PlainTextResponse(respuesta)

    # Paso 6: Texto cliente  🔸 CAMBIO NUEVO BLOQUE
    if estado_actual == "cliente_texto":
        tickets_temp[numero]["cliente"] = mensaje  # 🔸 CAMBIO
        respuesta = "📝 ¿Quieres agregar algún comentario adicional?\n1. No\n2. Sí"
        estados[numero] = "comentario_opcion"
        return PlainTextResponse(respuesta)

    # Paso 7: Comentario (sí/no) (ya existía)
    if estado_actual == "comentario_opcion":
        if mensaje in ["1", "no", "n"]:
            tickets_temp[numero]["comentario"] = ""
            estados[numero] = "confirmar"
            respuesta = generar_ticket(numero)
        elif mensaje in ["2", "sí", "si", "s"]:
            respuesta = "✍️ Escribe el comentario:"
            estados[numero] = "comentario_texto"
        else:
            respuesta = "⚠️ Opción no válida. Escribe 1 para 'No' o 2 para 'Sí'."
        return PlainTextResponse(respuesta)

    # Paso 8: Comentario (texto) (ya existía)
    if estado_actual == "comentario_texto":
        tickets_temp[numero]["comentario"] = mensaje
        estados[numero] = "confirmar"
        respuesta = generar_ticket(numero)
        return PlainTextResponse(respuesta)

# 📌 Esta función ya la tenías. Asegúrate de agregar el campo cliente si quieres mostrarlo.
def generar_ticket(numero):
    t = tickets_temp[numero]
    id_ticket = f"{t['concepto'][0].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    t["id"] = id_ticket

    ticket_texto = (
        f"📌 *Ticket generado*\n\n"
        f"🆔 ID: {id_ticket}\n"
        f"🧾 Concepto: {t['concepto']}\n"
        f"💰 Monto: {t['monto']}\n"
        f"💳 Estado de pago: {t['estado_pago']}\n"
        f"👤 Cliente: {t.get('cliente','')}\n"  # 🔸 CAMBIO NUEVO
        f"📝 Comentario: {t['comentario']}\n"
        f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    # Limpiar estado
    estados.pop(numero, None)
    tickets_temp.pop(numero, None)
    return ticket_texto
