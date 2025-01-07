import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Lista de pares de divisas
PARES_DIVISAS = [
    # Sesión Americana
    "USDMXNm"    
]



# archivo: obtener_datos_mt5.py

def obtener_datos_de_par(par, fecha_inicial, fecha_final, timeframe):
    """
    Obtiene datos históricos para un par específico.
    """
    rates = mt5.copy_rates_range(par, timeframe, fecha_inicial, fecha_final)
    if rates is None:
        print(f"Error al obtener datos para {par}")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def obtener_datos_historicos(pares_divisas, rango_minutos=5, timeframe=mt5.TIMEFRAME_M1):
    

    if not mt5.initialize():
        print("Error al iniciar MetaTrader5")
        return None

    # Rango de fechas: últimos 5 minutos
    fecha_final = datetime.now()
    fecha_inicial = fecha_final - timedelta(minutes=rango_minutos)

    # Diccionario para almacenar los datos
    datos_historicos = {}

    try:
        # Procesamiento paralelo para obtener datos de cada par
        with ThreadPoolExecutor() as executor:
            futuros = {
                executor.submit(obtener_datos_de_par, par, fecha_inicial, fecha_final, timeframe): par
                for par in pares_divisas
            }
            for futuro in futuros:
                par = futuros[futuro]
                resultado = futuro.result()
                if resultado is not None:
                    datos_historicos[par] = resultado

        return datos_historicos

    finally:
        # Asegurar el cierre de la conexión con MT5
        mt5.shutdown()