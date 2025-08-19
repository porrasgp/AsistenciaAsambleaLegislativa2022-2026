import pandas as pd
import requests
import sqlite3
import warnings
from datetime import datetime
from dateutil.relativedelta import relativedelta

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# ----------------------
# CONFIGURACIÓN
# ----------------------
BASE_URL = "https://alcr-sh05.asamblea.go.cr/pa/datosabiertos/Documentos%20compartidos/RegistroAsistencia/{periodo}-Control_asistencia.xlsx"
DB_PATH = "asistencia.db"

# ----------------------
# FUNCIONES
# ----------------------
def generar_meses(inicio):
    """
    Genera lista de meses en formato YYYY-MM desde 'inicio' hasta el mes actual.
    """
    fechas = []
    actual = datetime.strptime(inicio, "%Y-%m")
    fin_dt = datetime.today().replace(day=1)  # primer día del mes actual

    while actual <= fin_dt:
        fechas.append(actual.strftime("%Y-%m"))
        actual += relativedelta(months=1)

    return fechas


def mes_en_base(cursor, periodo):
    """
    Verifica si un periodo ya existe en la base de datos.
    """
    cursor.execute("SELECT COUNT(*) FROM asistencia WHERE periodo = ?", (periodo,))
    return cursor.fetchone()[0] > 0


def descargar_excel(periodo):
    """
    Descarga y lee el Excel de un periodo, devolviendo un DataFrame o None.
    """
    url = BASE_URL.format(periodo=periodo)
    try:
        resp = requests.get(url, verify=False, timeout=20)
        if resp.status_code == 200 and resp.content.strip():
            df = pd.read_excel(resp.content)
            df["periodo"] = periodo
            return df
        else:
            print(f"❌ No disponible: {periodo}")
    except Exception as e:
        print(f"⚠ Error descargando {periodo}: {e}")
    return None


def guardar_en_sqlite(df, conn):
    """
    Guarda un DataFrame en SQLite sin necesidad de definir columnas previamente.
    """
    df.to_sql("asistencia", conn, if_exists="append", index=False)


# ----------------------
# PROCESO PRINCIPAL
# ----------------------
def main():
    # Conexión a SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla si no existe (mínimo un campo para evitar error en la primera carga)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            periodo TEXT
        )
    """)

    # Generar meses desde Noviembre 2018 hasta el mes actual
    meses = generar_meses("2018-11")
    print(f"Procesando {len(meses)} meses hasta {meses[-1]}...")

    for periodo in meses:
        if mes_en_base(cursor, periodo):
            print(f"⏩ Ya existe en base: {periodo}")
            continue

        df = descargar_excel(periodo)
        if df is not None:
            guardar_en_sqlite(df, conn)
            conn.commit()
            print(f"✅ Guardado: {periodo}")

    conn.close()
    print("🎯 Proceso completado")


if __name__ == "__main__":
    main()
