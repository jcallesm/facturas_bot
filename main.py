from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse

app = FastAPI()

tickets ={}
contador=1
usuarios_estados = {}
usuarios_datos = {}

@app.post("/whatsapp")
async def whatsapp_webhook(From: str = Form (...), Body: str = Form(...)):
    global contador
    
    mensaje =Body.strip().lower()

    #####MENSAJE INICIAL#####
    if From not in usuarios_estados:
        usuarios_estados[From]= 'concepto'
        usuarios_datos[From] = {}
        return PlainTextResponse(
                        "👋 Hola, soy el bot de tickets.\nVamos a crear un nuevo ticket.\nPor favor, dime el **concepto** del ticket: COMPRA, VENTA u OTRO)."
                        )
    
    ####### PASO 1: TICKET SEGÙN CONCEPTO #####
    if estado == 'concepto':
        if mensaje in ["compra", "venta"]:
            usuarios_datos[From][concepto] = mensaje.capitalize()
            usuarios_estados[From]= 'estatus_pago'
            return PlainTextResponse(
                "✅ Entendido. Ahora dime el **estatus de pago**:\n1️⃣ PAGADO\n2️⃣ NO PAGADO\n3️⃣ PAGO PARCIAL"
            ) 
        elif mensaje == "otro":
            usuarios_estado[From] = "concepto_otro"
            return PlainTextResponse("Por favor, escribe el concepto personalizado.")
        else:
            return PlainTextResponse("❌ No entendí. Escribe 'compra', 'venta' u 'otro'.")
        ######## PASO 2: CONCEPTO PERZONALIZADO #####
    elif estado == 'concepto_otro':
        usuarios_datos[From]["concepto"] = mensaje.capitalize()
        usuarios_estados[From]= 'estatus_pago'
        return PlainTextResponse(
                        "Perfecto. Ahora dime el **estatus de pago**:\n1️⃣ PAGADO\n2️⃣ NO PAGADO\n3️⃣ PAGO PARCIAL"
        )
        # Paso 3: estatus de pago
    elif estado == 'estatus_pago':
        opciones_estatus = {"1": "PAGADO", "2": "NO PAGADO", "3": "PAGO PARCIAL"}
        if mensaje in opciones_estatus:
            if mensaje in opciones_estatus:
                usuarios_datos[From]["estatus_pago"] = opciones_estatus[mensaje]
                if mensaje in ["PAGADO","1"]:
                    usuarios_estados[From]= 'importe_total'
                    return PlainTextResponse("💰 Ingresa el **importe total** (solo números).") 
                elif mensaje in ["NO PAGADO","2"]:
                    usuarios_estados[From]= "importe_por_cobrar"
                    return PlainTextResponse("💰 Ingresa el **importe por cobrar** (solo números).") 
                elif mensaje in ["PAGO PARCIAL","3"]:
                    usuarios_estados[From]= 'importe_parcial_pagado'
                    return PlainTextResponse("💰 Ingresa el **importe parcial pagado** (solo números).")
            else:
                return PlainTextResponse("❌ Opción inválida. Escribe alguna de las siguientes opciones: PAGADO, NO PAGADO, PAGO PARCIAL, 1, 2 ó 3.")
            ########PASO 4A: IMPORTE TOTAL PAGADO ########     
        elif estado == 'importe_total':
            if not mensaje.replace(".","",1).rpartitionisdigit():
                return PlainTextResponse("❌ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).")
            
            importe=float(mensaje)
            usuarios_datos[From]["importe_total"] = importe

            ###CREAR TICKET###
            fecha_creacion=current_time().string()
            hoy= today().string()
            ticket_id = f"hoy-{contador:03d}"
            contador+=1
            ticket = {
                "fecha_creacion": fecha_creacion,
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total": usuarios_datos[From]["importe_total"],
                "por_cobrar":0.0,
                "cliente": From
            }
            tickets[ticket_id] = ticket
            usuarios_estados.pop(From)
            usuarios_datos.pop(From)

        return PlainTextResponse(
            f"✅ Ticket creado con éxito.\n\n🧾 Concepto: {ticket['concepto']}\n💰 Importe total: ${ticket['importe_total']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}"
        )
        ########PASO 4B: IMPORTE POR COBRAR ########
    elif estado == 'importe_por_cobrar':
        if not mensaje.replace(".","",1).rpartitionisdigit():
            return PlainTextResponse("❌ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).")
            
            importe=float(mensaje)
            usuarios_datos[From]["importe_por_cobrar"] = importe

            ###CREAR TICKET###
            fecha_creacion=current_time().string()
            hoy= today().string()
            ticket_id = f"hoy-{contador:03d}"
            contador+=1
            ticket = {
                "fecha_creacion": fecha_creacion,
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total":0.0,
                "por_cobrar":usuarios_datos[From]["importe_por_cobrar"],
                "cliente": From
            }
            tickets[ticket_id] = ticket
            usuarios_estados.pop(From)
            usuarios_datos.pop(From)
        
        return PlainTextResponse(
            f"✅ Ticket creado con éxito.\n\n🧾 Concepto: {ticket['concepto']}\n💰 Importe total: ${ticket['importe_total']}\n💸 Por cobrar: ${ticket['por_cobrar']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}"
        )
    
        ########PASO 4C: IMPORTE PARCIAL PAGADO ########
    elif estado == 'importe_parcial_pagado':
        if not mensaje.replace(".","",1).rpartitionisdigit():
            return PlainTextResponse("❌ Ingresa solo números o decimales válidos (ejemplo: 120 o 89.50).")
            
            importe=float(mensaje)
            usuarios_datos[From]["importe_parcial_pagado"] = importe

            ###CREAR TICKET###
            fecha_creacion=current_time().string()
            hoy= today().string()
            ticket_id = f"hoy-{contador:03d}"
            contador+=1
            ticket = {
                "fecha_creacion": fecha_creacion,
                "concepto": usuarios_datos[From]["concepto"],
                "estatus_pago": usuarios_datos[From]["estatus_pago"],
                "importe_total":0.0,
                "por_cobrar":0.0,
                "parcial_pagado":usuarios_datos[From]["importe_parcial_pagado"],
                "cliente": From
            }
            tickets[ticket_id] = ticket
            usuarios_estados.pop(From)
            usuarios_datos.pop(From)
        
        return PlainTextResponse(
            f"✅ Ticket creado con éxito.\n\n🧾 Concepto: {ticket['concepto']}\n💰 Importe total: ${ticket['importe_total']}\n💸 Parcial pagado: ${ticket['parcial_pagado']}\n📊 Estatus: {ticket['estatus_pago']}\n🆔 Número: {ticket_id}"
        )
    else:
        usuarios_estados[From]= 'concepto'
        return PlainTextResponse("Vamos a crear un nuevo ticket. Escribe 'compra', 'venta' u 'otro'.")