import pandas as pd
import sqlite3

# ===== 1. Cargar archivo Excel =====
import pandas as pd
import os

# ===== 1. Cargar archivo Excel =====
file_path = r"C:\Users\Admin\OneDrive\Desktop\AsistenciaAsambleaLegislativa2022-2026\data\combined_asistencia.xlsx"

# Verify the file exists before trying to read it
if os.path.exists(file_path):
    df = pd.read_excel(file_path, sheet_name="Sheet1")
    print(f"✅ Excel file loaded successfully with {df.shape[0]} rows and {df.shape[1]} columns")
else:
    print(f"❌ File not found at: {file_path}")
    print("Please check the file path and try again.")

# ===== 2. Normalización de columnas =====
# Ajusta según los nombres de tu archivo real
df = df.rename(columns={
    'MES': 'Mes',
    'AÑO': 'Anio', 
    ' Nombre': 'Diputado', 
    'Fracc': 'Fraccion', 
    'TOTAL': 'Total', 
    'Asis PL': 'AsistenciaPlenario',
    'Prog PL': 'ProgramadasNoRealizadasPlenario',
    'Aus PL': 'AusenciasPlenario',
    'Perm PL': 'PermisosPlenario',
    'Asis  Plen': 'AsistenciaComisionesPlenas',
    'Prog Plen': 'ProgramadasNoRealizadasComisionesPlenas',
    'Aus  Plen': 'AusenciasComisionesPlenas',
    'Perm Plen': 'PermisosComisionesPlenas',
    'Asis  CP': 'AsistenciaComisionesPermanentes',
    'Prog CP': 'ProgramadasNoRealizadasComisionesPermanentes',
    'Aus  CP': 'AusenciasComisionesPermanentes',
    'Perm  CP': 'PermisosComisionesPermanentes',
    'Asis  CPE': 'AsistenciaComisionesPermanentesEspeciales',
    'Aus  CPE': 'AusenciasComisionesPermanentesEspeciales',
    'Perm  CPE': 'PermisosComisionesPermanentesEspeciales',
    'Asis  CE': 'AsistenciaComisionesEspeciales',
    'Aus  CE': 'AusenciasComisionesEspeciales',
    'Perm  CE': 'PermisosComisionesEspeciales',
    'Asis  Frac': 'AsistenciaReunionesDeFraccion',
    'Prog  Frac': 'ProgramadasNoRealizadasReunionesDeFraccion',
    'Aus  Frac': 'AusenciasReunionesDeFraccion',
    'Perm  Frac': 'PermisosReunionesDeFraccion',
    'Asis  Jef.Frac': 'AsistenciaReunionesDeJefaturasDeFraccion',
    'Aus  Jef. Frac': 'AusenciasReunionesDeJefaturasDeFraccion',
    'Perm  Jef. Frac': 'PermisosReunionesDeJefaturasDeFraccion', 
    'source_file': 'SourceFile'
})

# ===== 3. Construir columna fecha =====
# Usamos el primer día del mes como referencia
df["fecha"] = pd.to_datetime(
    df["Anio"].astype(str) + "-" + df["Mes"].astype(str) + "-01",
    errors="coerce"
)

# ===== 4. Crear conexión a SQLite =====
conn = sqlite3.connect("./backend/asistencia_legislativa.db")

# Guardar en tabla SQL
df.to_sql("asistencia_legislativa", conn, if_exists="replace", index=False)

# ===== 5. Validar =====
cur = conn.cursor()
cur.execute("SELECT MIN(fecha), MAX(fecha), COUNT(*) FROM asistencia_legislativa;")
print("Rango de fechas y total registros:", cur.fetchone())

conn.close()
