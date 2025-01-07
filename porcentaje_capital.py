import MetaTrader5 as mt5
import logging
from concurrent.futures import ThreadPoolExecutor 
from exness import*



# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



# Configuración de pares y estrategias
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



# -------------------- Funciones Requeridas -------------------- #
def obtener_saldo_cuenta():
    """Obtiene el saldo de la cuenta en MetaTrader 5."""
    cuenta = mt5.account_info()
    if cuenta is None:
        logging.error("No se pudo obtener información de la cuenta.")
        return None
    return cuenta.balance

def calcular_riesgo(saldo, riesgo_porcentaje):
    """Calcula el monto máximo a arriesgar basado en el saldo y el porcentaje de riesgo."""
    return saldo * riesgo_porcentaje 

def calcular_lote_riesgo(saldo, par_divisa, stop_loss_pips, riesgo_porcentaje):
    """Calcula el tamaño del lote basado en el saldo, el riesgo y el stop loss."""
    try:
        symbol_info = mt5.symbol_info(par_divisa)
        if not symbol_info:
            logging.error(f"No se pudo obtener información del símbolo: {par_divisa}")
            return 0.1

        point = symbol_info.point
        monto_riesgo = calcular_riesgo(saldo, riesgo_porcentaje)
        valor_pip = point * symbol_info.contract_size
        lote = monto_riesgo / (stop_loss_pips * valor_pip)
        lote = max(symbol_info.volume_min, min(lote, symbol_info.volume_max))
        return round(lote, 2)
    except Exception as e:
        logging.error(f"Error al calcular lotes para {par_divisa}: {e}")
        return 0.1

def distribuir_capital(monto_total, par_divisa, porcentaje):
    
    # Calcula el monto que se distribuirá según el porcentaje
    monto_a_distribuir = (monto_total * porcentaje) / 100

    # Calcula el capital asignado a cada par
    capital_por_par = monto_a_distribuir / len(par_divisa)

    # Retorna un diccionario con los pares y su capital asignado
    return {par: capital_por_par for par in par_divisa}