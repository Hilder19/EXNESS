import logging
import MetaTrader5 as mt5  





def solicitar_credenciales():
    """
    Solicita las credenciales del usuario para conectarse a MetaTrader 5.
    """
    servidor = input("Introduce el servidor (Ejemplo: Exness-MT5): ").strip()
    cuenta = int(input("Introduce tu número de cuenta MT5: ").strip())
    contrasena = input("Introduce tu contraseña MT5: ").strip()
    return servidor, cuenta, contrasena

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






def desconectar_mt5():
    """
    Desconecta MetaTrader 5.
    """
    mt5.shutdown()
    logging.info("Desconectado de MetaTrader 5.")