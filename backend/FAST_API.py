import sqlite3
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Importa el middleware CORS
import uvicorn

DB_PATH = "asistencia_legislativa.db"

app = FastAPI()

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def query(sql: str, params: tuple = ()):
    """Ejecuta consultas SQL y devuelve DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

@app.get("/")
def root():
    return {"message": "API de Asistencia Legislativa lista 🚀"}

# Endpoint índice de KPIs
@app.get("/kpi")
def kpi_index():
    kpi_tree = {
        "title": "Árbol de KPIs de Asistencia Legislativa",
        "description": "Métricas disponibles para analizar el desempeño de diputados",
        "endpoints": [
            {
                "path": "/kpi/asistencia",
                "method": "GET",
                "description": "Porcentaje de asistencia global de todos los diputados",
                "parameters": "Ninguno",
                "output": {"pct_asistencia": "float"}
            },
            {
                "path": "/kpi/asistencia-mensual",
                "method": "GET",
                "description": "Evolución mensual del promedio de asistencia",
                "parameters": "Ninguno",
                "output": [
                    {"Anio": "int", "Mes": "int", "kpi_pct": "float"}
                ]
            },
            {
                "path": "/kpi/ranking",
                "method": "GET",
                "description": "Ranking de diputados por porcentaje de asistencia",
                "parameters": [
                    {"name": "top", "type": "int", "default": 5, "description": "Número de resultados"},
                    {"name": "orden", "type": "str", "default": "desc", "description": "'asc' para peores, 'desc' para mejores"}
                ],
                "output": [
                    {"Diputado": "str", "pct_asistencia": "float"}
                ]
            },
            {
                "path": "/kpi/sesiones-organo",
                "method": "GET",
                "description": "Total de sesiones por fracción política",
                "parameters": "Ninguno",
                "output": [
                    {"Fraccion": "str", "total_sesiones": "int"}
                ]
            },
            {
                "path": "/time/asistencia",
                "method": "GET",
                "description": "Serie temporal de asistencia por fracción política",
                "parameters": "Ninguno",
                "output": [
                    {"periodo": "str(YYYY-MM)", "Fraccion": "str", "pct_asistencia": "float"}
                ]
            }
        ],
        "metadata": {
            "version": "1.0",
            "last_updated": "2025-08-19",
            "kpi_formula": "Asistencia / (Asistencia + Ausencias)",
            "exclusiones": "Permisos y sesiones canceladas no se consideran"
        }
    }
    return JSONResponse(content=kpi_tree)


# KPI: % asistencia promedio (GLOBAL)
@app.get("/kpi/asistencia")
def asistencia_promedio():
    df = query("""
        SELECT 
            SUM(AsistenciaPlenario +
                AsistenciaComisionesPlenas +
                AsistenciaComisionesPermanentes +
                AsistenciaComisionesPermanentesEspeciales +
                AsistenciaComisionesEspeciales +
                AsistenciaReunionesDeFraccion +
                AsistenciaReunionesDeJefaturasDeFraccion) AS total_asistencias,
            SUM(AusenciasPlenario +
                AusenciasComisionesPlenas +
                AusenciasComisionesPermanentes +
                AusenciasComisionesPermanentesEspeciales +
                AusenciasComisionesEspeciales +
                AusenciasReunionesDeFraccion +
                AusenciasReunionesDeJefaturasDeFraccion) AS total_ausencias
        FROM asistencia_legislativa
    """)
    total_asistencias = df["total_asistencias"][0]
    total_ausencias = df["total_ausencias"][0]
    
    if total_asistencias + total_ausencias == 0:
        kpi = 0
    else:
        kpi = total_asistencias / (total_asistencias + total_ausencias)
    
    return JSONResponse(content={"pct_asistencia": round(kpi * 100, 2)})

# KPI: Asistencia promedio por mes
@app.get("/kpi/asistencia-mensual")
def asistencia_mensual():
    df = query("""
        SELECT 
            Anio,
            Mes,
            AsistenciaPlenario,
            AsistenciaComisionesPlenas,
            AsistenciaComisionesPermanentes,
            AsistenciaComisionesPermanentesEspeciales,
            AsistenciaComisionesEspeciales,
            AsistenciaReunionesDeFraccion,
            AsistenciaReunionesDeJefaturasDeFraccion,
            AusenciasPlenario,
            AusenciasComisionesPlenas,
            AusenciasComisionesPermanentes,
            AusenciasComisionesPermanentesEspeciales,
            AusenciasComisionesEspeciales,
            AusenciasReunionesDeFraccion,
            AusenciasReunionesDeJefaturasDeFraccion
        FROM asistencia_legislativa
    """)
    
    # Calcular totales por fila
    asistencias_cols = [
        'AsistenciaPlenario', 'AsistenciaComisionesPlenas', 'AsistenciaComisionesPermanentes',
        'AsistenciaComisionesPermanentesEspeciales', 'AsistenciaComisionesEspeciales',
        'AsistenciaReunionesDeFraccion', 'AsistenciaReunionesDeJefaturasDeFraccion'
    ]
    
    ausencias_cols = [
        'AusenciasPlenario', 'AusenciasComisionesPlenas', 'AusenciasComisionesPermanentes',
        'AusenciasComisionesPermanentesEspeciales', 'AusenciasComisionesEspeciales',
        'AusenciasReunionesDeFraccion', 'AusenciasReunionesDeJefaturasDeFraccion'
    ]
    
    df['total_asistencias'] = df[asistencias_cols].sum(axis=1)
    df['total_ausencias'] = df[ausencias_cols].sum(axis=1)
    
    # Calcular KPI individual
    df['kpi'] = df.apply(
        lambda x: x['total_asistencias'] / (x['total_asistencias'] + x['total_ausencias']) 
        if (x['total_asistencias'] + x['total_ausencias']) > 0 
        else 0, 
        axis=1
    )
    
    # Agrupar por mes y año
    kpi_mes = df.groupby(['Anio', 'Mes'])['kpi'].mean().reset_index()
    kpi_mes['kpi_pct'] = round(kpi_mes['kpi'] * 100, 2)
    kpi_mes = kpi_mes[['Anio', 'Mes', 'kpi_pct']]
    
    return JSONResponse(content=kpi_mes.to_dict(orient="records"))

# KPI: ranking diputados (actualizado)
@app.get("/kpi/ranking")
def ranking(top: int = 5, orden: str = "desc"):
    asc = "ASC" if orden == "asc" else "DESC"
    
    df = query(f"""
        SELECT 
            Diputado,
            (SUM(AsistenciaPlenario) +
             SUM(AsistenciaComisionesPlenas) +
             SUM(AsistenciaComisionesPermanentes) +
             SUM(AsistenciaComisionesPermanentesEspeciales) +
             SUM(AsistenciaComisionesEspeciales) +
             SUM(AsistenciaReunionesDeFraccion) +
             SUM(AsistenciaReunionesDeJefaturasDeFraccion)) AS total_asistencias,
             
            (SUM(AusenciasPlenario) +
             SUM(AusenciasComisionesPlenas) +
             SUM(AusenciasComisionesPermanentes) +
             SUM(AusenciasComisionesPermanentesEspeciales) +
             SUM(AusenciasComisionesEspeciales) +
             SUM(AusenciasReunionesDeFraccion) +
             SUM(AusenciasReunionesDeJefaturasDeFraccion)) AS total_ausencias
        FROM asistencia_legislativa
        GROUP BY Diputado
    """)
    
    # Calcular KPI
    df['pct_asistencia'] = df.apply(
        lambda x: round(100 * x['total_asistencias'] / (x['total_asistencias'] + x['total_ausencias']), 2)
        if (x['total_asistencias'] + x['total_ausencias']) > 0 
        else 0,
        axis=1
    )
    
    # Ordenar y seleccionar top
    df = df.sort_values('pct_asistencia', ascending=(orden=='asc')).head(top)
    return JSONResponse(content=df[['Diputado', 'pct_asistencia']].to_dict(orient="records"))

# ===== Endpoints actualizados =====
# KPI: total sesiones por fracción política
@app.get("/kpi/sesiones-por-fraccion")
def sesiones_organo():
    df = query("""
        SELECT Fraccion, SUM(Total) AS total_sesiones
        FROM asistencia_legislativa
        GROUP BY Fraccion
        ORDER BY total_sesiones DESC
    """)
    return JSONResponse(content=df.to_dict(orient="records"))

# Serie temporal de asistencia por fracción política
@app.get("/time/asistencia")
def serie_asistencia():
    # Obtener datos de asistencias y ausencias
    df = query("""
        SELECT 
            Anio,
            Mes,
            Fraccion,
            (SUM(AsistenciaPlenario) +
             SUM(AsistenciaComisionesPlenas) +
             SUM(AsistenciaComisionesPermanentes) +
             SUM(AsistenciaComisionesPermanentesEspeciales) +
             SUM(AsistenciaComisionesEspeciales) +
             SUM(AsistenciaReunionesDeFraccion) +
             SUM(AsistenciaReunionesDeJefaturasDeFraccion)) AS total_asistencias,
             
            (SUM(AusenciasPlenario) +
             SUM(AusenciasComisionesPlenas) +
             SUM(AusenciasComisionesPermanentes) +
             SUM(AusenciasComisionesPermanentesEspeciales) +
             SUM(AusenciasComisionesEspeciales) +
             SUM(AusenciasReunionesDeFraccion) +
             SUM(AusenciasReunionesDeJefaturasDeFraccion)) AS total_ausencias
        FROM asistencia_legislativa
        GROUP BY Anio, Mes, Fraccion
    """)
    
    # Calcular porcentaje de asistencia
    df['pct_asistencia'] = df.apply(
        lambda x: round(100 * x['total_asistencias'] / (x['total_asistencias'] + x['total_ausencias']), 2)
        if (x['total_asistencias'] + x['total_ausencias']) > 0 
        else 0,
        axis=1
    )
    
    # Crear columna de periodo (YYYY-MM)
    df['periodo'] = df['Anio'].astype(str) + '-' + df['Mes'].apply(lambda x: f"{x:02d}")
    
    # Ordenar resultados
    df = df.sort_values(['periodo', 'Fraccion'])
    
    return JSONResponse(content=df[['periodo', 'Fraccion', 'pct_asistencia']].to_dict(orient="records"))

# ===== Iniciar servidor =====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)