from tipo_de_operacion import*
import logging
from concurrent.futures import ThreadPoolExecutor
from getpass import getpass
import MetaTrader5 as mt5
from porcentaje_capital import*


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def PARES_DIVISAS():
    return [
        # Sesión Americana
        "USDMXNm"
    ]

# Llamar a la función usando el nombre 'par_divisa'
par_divisa = PARES_DIVISAS()




def crear_estrategia_exness(
    stop_loss_pips=20, 
    take_profit_pips=40, 
    trailing_distance_pips=15, 
    nombre="Estrategia Tiempo Real"
):
    
    return {
        "stop_loss_pips": stop_loss_pips,
        "take_profit_pips": take_profit_pips,
        "trailing_distance_pips": trailing_distance_pips,
        "nombre": nombre
    }

# Ejemplo de uso
estrategia_exness = crear_estrategia_exness()
print(estrategia_exness)



def conectar_cuenta(servidor, cuenta, contrasena):
    """
    Conecta a la cuenta de MetaTrader 5 utilizando las credenciales proporcionadas.
    """
    if not mt5.initialize(timeout=1000):  # 60 segundos de tiempo de espera
        logging.error(f"No se pudo inicializar MetaTrader 5. Error: {mt5.last_error()}")
        exit()

    # Conectar con las credenciales proporcionadas
    login_status = mt5.login(login=cuenta, password=contrasena, server=servidor)
    if not login_status:
        logging.error(f"Fallo al iniciar sesión con la cuenta {cuenta}. Verifica las credenciales.")
        return False

    logging.info(f"Conexión exitosa a la cuenta {cuenta} en el servidor {servidor}.")
    return True


# Abrir operación
def abrir_operacion_mt5(par, tipo, stop_loss_pips, take_profit_pips, volumen):
    """
    Abre una operación directamente en MetaTrader 5.
    """
    precio = mt5.symbol_info_tick(par)
    if not precio:
        logging.error(f"No se pudo obtener el precio para {par}.")
        return None

    orden = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": par,
        "volume": volumen,
        "type": mt5.ORDER_BUY if tipo == "compra" else mt5.ORDER_SELL,
        "price": precio.ask if tipo == "compra" else precio.bid,
        "sl": precio.ask - stop_loss_pips * 0.0001 if tipo == "compra" else precio.bid + stop_loss_pips * 0.0001,
        "tp": precio.ask + take_profit_pips * 0.0001 if tipo == "compra" else precio.bid - take_profit_pips * 0.0001,
        "deviation": 10,
    }

    resultado = mt5.order_send(orden)
    if resultado and resultado.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"Operación abierta exitosamente. Ticket: {resultado.order}")
        return {
            "ticket": resultado.order,
            "par": par,
            "tipo": tipo,
            "tp": orden["tp"],
            "sl": orden["sl"],
        }
    else:
        logging.error(f"Error al abrir operación: {resultado.retcode}")
        return None

# Cerrar operación
def cerrar_operacion_mt5(ticket):
    """
    Cierra una operación abierta en MetaTrader 5.
    """
    posicion = mt5.positions_get(ticket=ticket)
    if not posicion:
        logging.error(f"No se encontró la posición con el ticket {ticket}.")
        return False

    orden = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": posicion[0].symbol,
        "volume": posicion[0].volume,
        "type": mt5.ORDER_SELL if posicion[0].type == mt5.ORDER_BUY else mt5.ORDER_BUY,
        "price": mt5.symbol_info_tick(posicion[0].symbol).bid if posicion[0].type == mt5.ORDER_BUY else mt5.symbol_info_tick(posicion[0].symbol).ask,
        "deviation": 10,
    }

    resultado = mt5.order_send(orden)
    if resultado and resultado.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"Operación cerrada exitosamente. Ticket: {ticket}")
        return True
    else:
        logging.error(f"Error al cerrar operación: {resultado.retcode}")
        return False










# ---------------- Operaciones en MT5 ---------------- #

def ajustar_tp_dinamico(operacion, take_profit_pips):
    """
    Ajusta dinámicamente el nivel de Take Profit con base en el precio actual.
    Retorna True si el TP fue ajustado exitosamente.
    """
    ticket = operacion.get("ticket")
    precio_actual = obtener_precio_actual(operacion["par"])
    tp_actual = operacion.get("tp")

    if not precio_actual or not tp_actual:
        logging.error(f"No se pudo ajustar el TP dinámico para el ticket {ticket}.")
        return False

    nuevo_tp = max(precio_actual["ask"] + take_profit_pips * 0.0001, tp_actual) if operacion["tipo"] == "compra" else \
               min(precio_actual["bid"] - take_profit_pips * 0.0001, tp_actual)

    if nuevo_tp != tp_actual:
        if mt5.order_modify(ticket, price_sl=None, price_tp=nuevo_tp):
            logging.info(f"TP dinámico ajustado para el ticket {ticket}: Nuevo TP: {nuevo_tp}")
            operacion["tp"] = nuevo_tp  # Actualizar el TP en los datos locales de la operación
            return True
        else:
            logging.error(f"No se pudo modificar el TP para el ticket {ticket}.")
            return False
    return False

def verificar_tp_dinamico(operacion):
    """
    Verifica si el precio alcanzó el nivel de Take Profit dinámico.
    Retorna True si el precio alcanzó el TP.
    """
    precio_actual = obtener_precio_actual(operacion["par"])
    if not precio_actual:
        logging.error(f"No se pudo verificar el TP dinámico para {operacion['par']}.")
        return False

    tipo = operacion["tipo"]
    tp = operacion["tp"]

    if (tipo == "compra" and precio_actual["bid"] >= tp) or (tipo == "venta" and precio_actual["ask"] <= tp):
        logging.info(f"El TP dinámico fue alcanzado para el ticket {operacion['ticket']}.")
        return True
    return False

def calcular_lote_riesgo(saldo, par_divisa, stop_loss_pips, riesgo_porcentaje):
    """
    Calcula el tamaño del lote basado en el saldo, SL y el porcentaje de riesgo.
    """
    valor_pip = 10.0  # Ajustar según el par de divisas y cuenta
    riesgo_dolares = saldo * riesgo_porcentaje
    tamaño_lote = riesgo_dolares / (stop_loss_pips * valor_pip)

    logging.info(f"Tamaño del lote calculado: {tamaño_lote:.2f} para {par_divisa}.")
    return max(tamaño_lote, 0.01)  # Asegurar un mínimo de lote



def verificar_trailing_stop(operacion, trailing_distance_pips):
    """
    Verifica si el precio alcanzó el nivel del Trailing Stop.
    """
    precio_actual = obtener_precio_actual(operacion["par"])
    if not precio_actual:
        logging.error(f"No se pudo verificar el Trailing Stop para {operacion['par']}.")
        return False

    if operacion["tipo"] == "compra":
        nuevo_sl = precio_actual["bid"] - trailing_distance_pips * 0.0001
        if nuevo_sl > operacion["sl"]:
            return mt5.order_modify(operacion["ticket"], price_sl=nuevo_sl, price_tp=operacion["tp"])
    else:
        nuevo_sl = precio_actual["ask"] + trailing_distance_pips * 0.0001
        if nuevo_sl < operacion["sl"]:
            return mt5.order_modify(operacion["ticket"], price_sl=nuevo_sl, price_tp=operacion["tp"])

    return False

def obtener_precio_actual(par):
    """
    Obtiene el precio actual para el par de divisas dado.
    """
    precio = mt5.symbol_info_tick(par)
    if not precio:
        logging.error(f"No se pudo obtener el precio actual para {par}.")
        return None
    return {"ask": precio.ask, "bid": precio.bid}


datos =obtener_datos_historicos(par_divisa, rango_minutos=5, timeframe=mt5.TIMEFRAME_M1)

def ejecutar_estrategia_mt5(par_divisa, capital_par, estrategia_exness):
    """
    Ejecuta la estrategia de trading conectando directamente con la cuenta MT5.
    """
    

    try:
        while True:
            # Calcular el lote basado en el capital asignado y riesgo
            lote = calcular_lote_riesgo(
                saldo=capital_par,
                par_divisa=par_divisa,
                stop_loss_pips=estrategia_exness["stop_loss_pips"],
                riesgo_porcentaje=0.01  # Riesgo fijo por operación
            )

            if lote <= 0:
                logging.warning(f"No se pudo calcular un lote válido para {par_divisa}. Estrategia: {estrategia_exness['nombre']}.")
                return

            # Obtener datos históricos para calcular indicadores
            datos =obtener_datos_historicos(par_divisa, rango_minutos=5, timeframe=mt5.TIMEFRAME_M1) 
            if datos is None or datos.empty:
                logging.error(f"No se pudieron obtener precios para {par_divisa}.")
                return

            precios_close = datos['close'].tolist()

            # Determinar el tipo de operación usando la estrategia
            tipo_operacion =determinar_tipo_operacion(estrategia_exness, precios_close)
            if tipo_operacion is None or tipo_operacion == "mantener":
                logging.info(f"Estrategia para {par_divisa} indica mantener. No se abre operación.")
                continue

            # Abrir operación inicial
            logging.info(f"Abrir operación {tipo_operacion.upper()} para {par_divisa}, Lote: {lote}, Estrategia: {estrategia_exness['nombre']}.")
            operacion = abrir_operacion_mt5(
                par=par_divisa,
                tipo=tipo_operacion,
                stop_loss_pips=estrategia_exness["stop_loss_pips"],
                take_profit_pips=estrategia_exness["take_profit_pips"],
                volumen=lote
            )

            if not operacion:
                logging.warning(f"No se pudo abrir la operación para {par_divisa}. Estrategia: {estrategia_exness['nombre']}.")
                return

            # Monitorear y gestionar la operación
            while True:
                logging.info(f"Monitoreando operación en {par_divisa}. Ticket: {operacion.get('ticket')}.")

                # Ajustar Take Profit dinámico
                if ajustar_tp_dinamico(operacion, estrategia_exness["take_profit_pips"]):
                    logging.info(f"Take Profit dinámico ajustado para {par_divisa}. Ticket: {operacion.get('ticket')}.")

                # Verificar condiciones para cerrar operación
                if verificar_tp_dinamico(operacion):  # Condición para cerrar en TP dinámico
                    logging.info(f"Condición de cierre alcanzada para {par_divisa}. Ticket: {operacion.get('ticket')}.")
                    cerrar_operacion_mt5(operacion.get("ticket"))
                    break

                # Verificar Trailing Stop
                if verificar_trailing_stop(operacion, estrategia_exness.get("trailing_distance_pips", 10)):
                    logging.info(f"Trailing Stop alcanzado para {par_divisa}. Ticket: {operacion.get('ticket')}.")
                    cerrar_operacion_mt5(operacion.get("ticket"))
                    break

    except Exception as e:
        logging.error(f"Error al ejecutar estrategia '{estrategia_exness['nombre']}' para {par_divisa}: {e}")
    finally:
        mt5.shutdown()
        logging.info("Conexión a MT5 cerrada.")