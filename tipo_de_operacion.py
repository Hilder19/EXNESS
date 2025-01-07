import pandas as pd
import MetaTrader5 as mt5
import logging 
from exness import*

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
    indicador="media_movil",  # Agregado para definir el tipo de indicador
    periodo_corto=5,  # Para media móvil
    periodo_largo=10,  # Para media móvil
    periodo_rsi=14,  # Para RSI
    nombre="Estrategia Tiempo Real"
):
    """
    Crea una configuración de estrategia para operaciones en MetaTrader 5.
    """
    return {
        "stop_loss_pips": stop_loss_pips,
        "take_profit_pips": take_profit_pips,
        "trailing_distance_pips": trailing_distance_pips,
        "indicador": indicador,
        "periodo_corto": periodo_corto,
        "periodo_largo": periodo_largo,
        "periodo_rsi": periodo_rsi,
        "nombre": nombre
    }

# Crear estrategia
estrategia_exness = crear_estrategia_exness()
print("Configuración de la estrategia:")
print(estrategia_exness)

# Obtener datos históricos por par
def obtener_datos_historicos(par_divisa, rango_minutos=5, timeframe=mt5.TIMEFRAME_M1):
    datos_por_par = {}
    for par in par_divisa:
        rates = mt5.copy_rates_from_pos(par, timeframe, 0, rango_minutos)
        if rates is not None:
            datos = pd.DataFrame(rates)
            datos['time'] = pd.to_datetime(datos['time'], unit='s')
            datos_por_par[par] = datos
        else:
            print(f"No se pudieron obtener datos para {par}")
    return datos_por_par

datos = obtener_datos_historicos(par_divisa, rango_minutos=5, timeframe=mt5.TIMEFRAME_M1)

print("Datos por par:")
for par, df in datos.items():
    print(f"Datos para {par}:")
    print(df.head())

# Cálculo de indicadores
def calcular_media_movil(datos, periodo, tipo="sma"):
    """
    Calcula la media móvil de los datos de cierre.
    """
    if len(datos) < periodo:
        raise ValueError("El tamaño de los datos debe ser mayor o igual al período.")

    if tipo == "sma":
        return pd.Series(datos).rolling(window=periodo).mean().iloc[-1]
    elif tipo == "ema":
        return pd.Series(datos).ewm(span=periodo, adjust=False).mean().iloc[-1]
    else:
        raise ValueError("Tipo de media móvil no soportado. Usa 'sma' o 'ema'.")

def calcular_rsi(datos, periodo=14):
    """
    Calcula el Índice de Fuerza Relativa (RSI) usando acumulación para optimización.
    """
    if len(datos) < periodo:
        raise ValueError("El tamaño de los datos debe ser mayor o igual al período.")

    cambios = pd.Series(datos).diff()
    ganancias = cambios.where(cambios > 0, 0)
    perdidas = -cambios.where(cambios < 0, 0)

    media_ganancias = ganancias.rolling(window=periodo).mean()
    media_perdidas = perdidas.rolling(window=periodo).mean()

    rs = media_ganancias / media_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# Determinación del tipo de operación
def determinar_tipo_operacion(estrategia_exness, datos):
    """
    Determina el tipo de operación a realizar basado en la estrategia configurada.
    """
    try:
        if estrategia_exness.get("indicador") == "media_movil":
            media_movil_corta = calcular_media_movil(datos, estrategia_exness["periodo_corto"])
            media_movil_larga = calcular_media_movil(datos, estrategia_exness["periodo_largo"])
            return "compra" if media_movil_corta > media_movil_larga else "venta"
        
        elif estrategia_exness.get("indicador") == "rsi":
            rsi = calcular_rsi(datos, estrategia_exness.get("periodo_rsi", 14))
            if rsi < 30:
                return "compra"
            elif rsi > 70:
                return "venta"
            else:
                return "mantener"
        
        else:
            logging.warning("Indicador no soportado en la estrategia.")
            return None

    except ValueError as e:
        logging.error(f"Error en la estrategia: {e}")
        return None