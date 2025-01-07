import random
from datetime import datetime
from typing import List
import MetaTrader5 as mt5
import logging




# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Códigos ANSI para colores
COLOR_VERDE = "\033[92m"  # Verde para ✓
COLOR_ROJO = "\033[91m"   # Rojo para ✗
COLOR_RESET = "\033[0m"   # Reset a color normal


def PARES_DIVISAS():
    return [
        # Sesión Americana
        "USDMXNm"
    ]

# Llamar a la función usando el nombre 'par_divisa'
par_divisa = PARES_DIVISAS()




def obtener_ganancias_perdidas():
    """
    Obtiene las ganancias y pérdidas de las posiciones abiertas en la cuenta de MetaTrader 5.

    Returns:
        List[Tuple[str, float]]: Lista de pares de divisas y sus ganancias/pérdidas.
    """
    posiciones = mt5.positions_get()
    if posiciones is None:
        logging.error(f"Error al obtener posiciones: {mt5.last_error()}")
        return []

    resultados = []
    for pos in posiciones:
        resultados.append((pos.symbol, pos.profit))
    return resultados

def calcular_ganancias_perdidas(pares: List[str], resultados: List[float], pares_por_hilera: int = 5):
    """
    Calcula y registra las ganancias o pérdidas de los pares de divisas en formato de columnas.

    Args:
        pares (List[str]): Lista de pares de divisas.
        resultados (List[float]): Lista de ganancias/pérdidas correspondientes a los pares.
        pares_por_hilera (int): Número de pares por hilera (columnas).

    Returns:
        None
    """
    # Fecha y hora actuales
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info("\n--- Resultados en Columnas ---")
    
    # Preparar las columnas
    columnas = []
    for i in range(0, len(pares), pares_por_hilera):
        columna = []
        for j in range(i, min(i + pares_por_hilera, len(pares))):
            numero = f"{j + 1:>2}."
            par = pares[j]
            ganancia = resultados[j]
            simbolo = f"{COLOR_VERDE}✓{COLOR_RESET}" if ganancia > 0 else f"{COLOR_ROJO}✗{COLOR_RESET}" if ganancia < 0 else "-"
            columna.append(f"{numero} {par}: {ganancia:7.2f} {simbolo}")
        columnas.append(columna)
    
    # Combinar y mostrar las columnas como una tabla
    filas_max = max(len(col) for col in columnas)
    for fila in range(filas_max):
        linea = "   ".join(col[fila] if fila < len(col) else "" for col in columnas)
        logging.info(f"{timestamp} | {linea}")