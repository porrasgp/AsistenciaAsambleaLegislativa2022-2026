import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Optional

# Ruta absoluta a la base de datos - ajústala según tu estructura de carpetas
DB_PATH = os.path.join(os.path.dirname(__file__), "asistencia_legislativa.db")

app = FastAPI(
    title="API de Asistencia Legislativa",
    description="API para consultar datos de asistencia de diputados",
    version="1.2.0"
)

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
    if not os.path.exists(DB_PATH):
        raise HTTPException(
            status_code=500, 
            detail=f"Base de datos no encontrada en: {DB_PATH}. Ejecuta CSVDB.py primero."
        )
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta SQL: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "API de Asistencia Legislativa lista 🚀",
        "database_path": DB_PATH,
        "database_exists": os.path.exists(DB_PATH),
        "endpoints": [
            "/kpi",
            "/kpi/asistencia",
            "/kpi/asistencia-mensual", 
            "/kpi/ranking",
            "/kpi/sesiones-por-fraccion",
            "/kpi/asistencia-por-tipo-sesion",
            "/kpi/comparacion-fracciones",
            "/kpi/diputado/{nombre}",
            "/time/asistencia",
            "/time/asistencia-anual",
            "/stats/resumen",
            "/debug/columnas"
        ]
    }

@app.get("/health")
def health_check():
    """Endpoint para verificar el estado de la API y la base de datos"""
    try:
        # Verificar si existe la base de datos
        if not os.path.exists(DB_PATH):
            return {
                "status": "error",
                "message": "Base de datos no encontrada",
                "database_path": DB_PATH,
                "solution": "Ejecuta CSVDB.py para crear la base de datos"
            }
        
        # Verificar si la tabla existe
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asistencia_legislativa';")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            conn.close()
            return {
                "status": "error",
                "message": "Tabla 'asistencia_legislativa' no existe",
                "solution": "Ejecuta CSVDB.py para crear la tabla"
            }
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM asistencia_legislativa;")
        record_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "ok",
            "database_path": DB_PATH,
            "table_exists": True,
            "record_count": record_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar la base de datos: {str(e)}"
        }

# Endpoint índice de KPIs
@app.get("/kpi")
def kpi_index():
    kpi_tree = {
        "title": "Árbol de KPIs de Asistencia Legislativa",
        "description": "Métricas disponibles para analizar el desempeño de diputados",
        "database_status": {
            "path": DB_PATH,
            "exists": os.path.exists(DB_PATH)
        },
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
                "path": "/kpi/sesiones-por-fraccion",
                "method": "GET",
                "description": "Total de sesiones por fracción política",
                "parameters": "Ninguno",
                "output": [
                    {"Fraccion": "str", "total_sesiones": "int"}
                ]
            },
            {
                "path": "/kpi/asistencia-por-tipo-sesion",
                "method": "GET",
                "description": "Comparación de asistencia por tipo de sesión (Plenario, Comisiones, etc.)",
                "parameters": "Ninguno",
                "output": [
                    {"tipo_sesion": "str", "promedio_asistencia": "float", "total_sesiones": "int"}
                ]
            },
            {
                "path": "/kpi/comparacion-fracciones",
                "method": "GET",
                "description": "Comparación detallada de asistencia entre fracciones políticas",
                "parameters": "Ninguno",
                "output": [
                    {"Fraccion": "str", "pct_asistencia": "float", "total_diputados": "int"}
                ]
            },
            {
                "path": "/kpi/diputado/{nombre}",
                "method": "GET",
                "description": "Estadísticas detalladas de un diputado específico",
                "parameters": [{"name": "nombre", "type": "str", "description": "Nombre del diputado"}],
                "output": {"Diputado": "str", "Fraccion": "str", "pct_asistencia": "float", "desglose": "dict"}
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
            "version": "1.2",
            "last_updated": "2025-08-20",
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
            COALESCE(SUM(AsistenciaPlenario), 0) +
            COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
            COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
            COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
            COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
            COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
            COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0) AS total_asistencias,
            
            COALESCE(SUM(AusenciasPlenario), 0) +
            COALESCE(SUM(AusenciasComisionesPlenas), 0) +
            COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
            COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
            COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
            COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
            COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0) AS total_ausencias
        FROM asistencia_legislativa
    """)
    
    total_asistencias = df["total_asistencias"][0] or 0
    total_ausencias = df["total_ausencias"][0] or 0
    
    if total_asistencias + total_ausencias == 0:
        kpi = 0
    else:
        kpi = total_asistencias / (total_asistencias + total_ausencias)
    
    return JSONResponse(content={
        "pct_asistencia": round(kpi * 100, 2),
        "total_asistencias": int(total_asistencias),
        "total_ausencias": int(total_ausencias),
        "total_sesiones": int(total_asistencias + total_ausencias)
    })

# KPI: Asistencia promedio por mes
@app.get("/kpi/asistencia-mensual")
def asistencia_mensual():
    df = query("""
        SELECT 
            Anio,
            Mes,
            COALESCE(AsistenciaPlenario, 0) as AsistenciaPlenario,
            COALESCE(AsistenciaComisionesPlenas, 0) as AsistenciaComisionesPlenas,
            COALESCE(AsistenciaComisionesPermanentes, 0) as AsistenciaComisionesPermanentes,
            COALESCE(AsistenciaComisionesPermanentesEspeciales, 0) as AsistenciaComisionesPermanentesEspeciales,
            COALESCE(AsistenciaComisionesEspeciales, 0) as AsistenciaComisionesEspeciales,
            COALESCE(AsistenciaReunionesDeFraccion, 0) as AsistenciaReunionesDeFraccion,
            COALESCE(AsistenciaReunionesDeJefaturasDeFraccion, 0) as AsistenciaReunionesDeJefaturasDeFraccion,
            COALESCE(AusenciasPlenario, 0) as AusenciasPlenario,
            COALESCE(AusenciasComisionesPlenas, 0) as AusenciasComisionesPlenas,
            COALESCE(AusenciasComisionesPermanentes, 0) as AusenciasComisionesPermanentes,
            COALESCE(AusenciasComisionesPermanentesEspeciales, 0) as AusenciasComisionesPermanentesEspeciales,
            COALESCE(AusenciasComisionesEspeciales, 0) as AusenciasComisionesEspeciales,
            COALESCE(AusenciasReunionesDeFraccion, 0) as AusenciasReunionesDeFraccion,
            COALESCE(AusenciasReunionesDeJefaturasDeFraccion, 0) as AusenciasReunionesDeJefaturasDeFraccion
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

# KPI: ranking diputados
@app.get("/kpi/ranking")
def ranking(top: int = Query(5, description="Número de resultados a mostrar"), 
           orden: str = Query("desc", description="Orden: 'asc' para peores, 'desc' para mejores")):
    df = query(f"""
        SELECT 
            Diputado,
            Fraccion,
            (COALESCE(SUM(AsistenciaPlenario), 0) +
             COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
             COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
             COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0)) AS total_asistencias,
             
            (COALESCE(SUM(AusenciasPlenario), 0) +
             COALESCE(SUM(AusenciasComisionesPlenas), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
             COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
             COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0)) AS total_ausencias
        FROM asistencia_legislativa
        GROUP BY Diputado, Fraccion
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
    return JSONResponse(content=df[['Diputado', 'Fraccion', 'pct_asistencia']].to_dict(orient="records"))

# KPI: total sesiones por fracción política
@app.get("/kpi/sesiones-por-fraccion")
def sesiones_organo():
    df = query("""
        SELECT 
            Fraccion, 
            COALESCE(SUM(Total), 0) AS total_sesiones
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
            (COALESCE(SUM(AsistenciaPlenario), 0) +
             COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
             COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
             COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0)) AS total_asistencias,
             
            (COALESCE(SUM(AusenciasPlenario), 0) +
             COALESCE(SUM(AusenciasComisionesPlenas), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
             COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
             COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0)) AS total_ausencias
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

# KPI: asistencia por tipo de sesión (ya funcionando)
@app.get("/kpi/asistencia-por-tipo-sesion")
def asistencia_por_tipo_sesion():
    try:
        df = query("""
            SELECT 
                COALESCE(SUM(AsistenciaPlenario), 0) as asis_plenario,
                COALESCE(SUM(AusenciasPlenario), 0) as aus_plenario,
                COALESCE(SUM(AsistenciaComisionesPlenas), 0) as asis_comisiones_plenas,
                COALESCE(SUM(AusenciasComisionesPlenas), 0) as aus_comisiones_plenas,
                COALESCE(SUM(AsistenciaComisionesPermanentes), 0) as asis_comisiones_permanentes,
                COALESCE(SUM(AusenciasComisionesPermanentes), 0) as aus_comisiones_permanentes,
                COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) as asis_comisiones_perm_esp,
                COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) as aus_comisiones_perm_esp,
                COALESCE(SUM(AsistenciaComisionesEspeciales), 0) as asis_comisiones_especiales,
                COALESCE(SUM(AusenciasComisionesEspeciales), 0) as aus_comisiones_especiales,
                COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) as asis_reuniones_fraccion,
                COALESCE(SUM(AusenciasReunionesDeFraccion), 0) as aus_reuniones_fraccion,
                COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0) as asis_jefaturas,
                COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0) as aus_jefaturas
            FROM asistencia_legislativa
        """)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No se encontraron datos")
        
        # Extraer valores de manera más segura
        row = df.iloc[0]
        
        # Calcular porcentajes para cada tipo de sesión
        tipos_sesion = [
            {
                "tipo_sesion": "Plenario",
                "total_asistencias": int(row["asis_plenario"]) if not pd.isna(row["asis_plenario"]) else 0,
                "total_ausencias": int(row["aus_plenario"]) if not pd.isna(row["aus_plenario"]) else 0
            },
            {
                "tipo_sesion": "Comisiones Plenas",
                "total_asistencias": int(row["asis_comisiones_plenas"]) if not pd.isna(row["asis_comisiones_plenas"]) else 0,
                "total_ausencias": int(row["aus_comisiones_plenas"]) if not pd.isna(row["aus_comisiones_plenas"]) else 0
            },
            {
                "tipo_sesion": "Comisiones Permanentes",
                "total_asistencias": int(row["asis_comisiones_permanentes"]) if not pd.isna(row["asis_comisiones_permanentes"]) else 0,
                "total_ausencias": int(row["aus_comisiones_permanentes"]) if not pd.isna(row["aus_comisiones_permanentes"]) else 0
            },
            {
                "tipo_sesion": "Com. Perm. Especiales",
                "total_asistencias": int(row["asis_comisiones_perm_esp"]) if not pd.isna(row["asis_comisiones_perm_esp"]) else 0,
                "total_ausencias": int(row["aus_comisiones_perm_esp"]) if not pd.isna(row["aus_comisiones_perm_esp"]) else 0
            },
            {
                "tipo_sesion": "Comisiones Especiales",
                "total_asistencias": int(row["asis_comisiones_especiales"]) if not pd.isna(row["asis_comisiones_especiales"]) else 0,
                "total_ausencias": int(row["aus_comisiones_especiales"]) if not pd.isna(row["aus_comisiones_especiales"]) else 0
            },
            {
                "tipo_sesion": "Reuniones de Fracción",
                "total_asistencias": int(row["asis_reuniones_fraccion"]) if not pd.isna(row["asis_reuniones_fraccion"]) else 0,
                "total_ausencias": int(row["aus_reuniones_fraccion"]) if not pd.isna(row["aus_reuniones_fraccion"]) else 0
            },
            {
                "tipo_sesion": "Jefaturas de Fracción",
                "total_asistencias": int(row["asis_jefaturas"]) if not pd.isna(row["asis_jefaturas"]) else 0,
                "total_ausencias": int(row["aus_jefaturas"]) if not pd.isna(row["aus_jefaturas"]) else 0
            }
        ]
        
        # Calcular porcentajes y total de sesiones
        resultado = []
        for tipo in tipos_sesion:
            total = tipo["total_asistencias"] + tipo["total_ausencias"]
            if total > 0:
                porcentaje = round(100 * tipo["total_asistencias"] / total, 2)
            else:
                porcentaje = 0.0
            
            resultado.append({
                "tipo_sesion": tipo["tipo_sesion"],
                "promedio_asistencia": porcentaje,
                "total_sesiones": total,
                "total_asistencias": tipo["total_asistencias"],
                "total_ausencias": tipo["total_ausencias"]
            })
        
        # Ordenar por promedio de asistencia descendente
        resultado.sort(key=lambda x: x["promedio_asistencia"], reverse=True)
        
        return JSONResponse(content=resultado)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al procesar asistencia por tipo de sesión: {str(e)}"
        )

# NUEVOS ENDPOINTS ADICIONALES

# KPI: Comparación entre fracciones políticas
@app.get("/kpi/comparacion-fracciones")
def comparacion_fracciones():
    """Compara la asistencia promedio entre todas las fracciones políticas"""
    df = query("""
        SELECT 
            Fraccion,
            COUNT(DISTINCT Diputado) as total_diputados,
            (COALESCE(SUM(AsistenciaPlenario), 0) +
             COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
             COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
             COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0)) AS total_asistencias,
             
            (COALESCE(SUM(AusenciasPlenario), 0) +
             COALESCE(SUM(AusenciasComisionesPlenas), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
             COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
             COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0)) AS total_ausencias
        FROM asistencia_legislativa
        GROUP BY Fraccion
    """)
    
    # Calcular porcentaje de asistencia por fracción
    df['pct_asistencia'] = df.apply(
        lambda x: round(100 * x['total_asistencias'] / (x['total_asistencias'] + x['total_ausencias']), 2)
        if (x['total_asistencias'] + x['total_ausencias']) > 0 
        else 0,
        axis=1
    )
    
    # Ordenar por porcentaje de asistencia descendente
    df = df.sort_values('pct_asistencia', ascending=False)
    
    return JSONResponse(content=df[['Fraccion', 'pct_asistencia', 'total_diputados']].to_dict(orient="records"))

# KPI: Estadísticas de un diputado específico
@app.get("/kpi/diputado/{nombre}")
def estadisticas_diputado(nombre: str):
    """Obtiene estadísticas detalladas de un diputado específico"""
    df = query("""
        SELECT 
            Diputado,
            Fraccion,
            COALESCE(SUM(AsistenciaPlenario), 0) as asis_plenario,
            COALESCE(SUM(AusenciasPlenario), 0) as aus_plenario,
            COALESCE(SUM(AsistenciaComisionesPlenas), 0) as asis_comisiones_plenas,
            COALESCE(SUM(AusenciasComisionesPlenas), 0) as aus_comisiones_plenas,
            COALESCE(SUM(AsistenciaComisionesPermanentes), 0) as asis_comisiones_permanentes,
            COALESCE(SUM(AusenciasComisionesPermanentes), 0) as aus_comisiones_permanentes,
            COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) as asis_comisiones_perm_esp,
            COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) as aus_comisiones_perm_esp,
            COALESCE(SUM(AsistenciaComisionesEspeciales), 0) as asis_comisiones_especiales,
            COALESCE(SUM(AusenciasComisionesEspeciales), 0) as aus_comisiones_especiales,
            COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) as asis_reuniones_fraccion,
            COALESCE(SUM(AusenciasReunionesDeFraccion), 0) as aus_reuniones_fraccion,
            COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0) as asis_jefaturas,
            COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0) as aus_jefaturas
        FROM asistencia_legislativa
        WHERE UPPER(Diputado) LIKE UPPER(?)
        GROUP BY Diputado, Fraccion
    """, (f"%{nombre}%",))
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Diputado '{nombre}' no encontrado")
    
    # Tomar el primer resultado si hay múltiples coincidencias
    row = df.iloc[0]
    
    # Calcular totales
    total_asistencias = (
        row['asis_plenario'] + row['asis_comisiones_plenas'] + row['asis_comisiones_permanentes'] +
        row['asis_comisiones_perm_esp'] + row['asis_comisiones_especiales'] + 
        row['asis_reuniones_fraccion'] + row['asis_jefaturas']
    )
    
    total_ausencias = (
        row['aus_plenario'] + row['aus_comisiones_plenas'] + row['aus_comisiones_permanentes'] +
        row['aus_comisiones_perm_esp'] + row['aus_comisiones_especiales'] + 
        row['aus_reuniones_fraccion'] + row['aus_jefaturas']
    )
    
    total_sesiones = total_asistencias + total_ausencias
    pct_asistencia = round(100 * total_asistencias / total_sesiones, 2) if total_sesiones > 0 else 0
    
    # Desglose por tipo de sesión
    desglose = {
        "plenario": {
            "asistencias": int(row['asis_plenario']),
            "ausencias": int(row['aus_plenario']),
            "porcentaje": round(100 * row['asis_plenario'] / (row['asis_plenario'] + row['aus_plenario']), 2) 
                         if (row['asis_plenario'] + row['aus_plenario']) > 0 else 0
        },
        "comisiones_plenas": {
            "asistencias": int(row['asis_comisiones_plenas']),
            "ausencias": int(row['aus_comisiones_plenas']),
            "porcentaje": round(100 * row['asis_comisiones_plenas'] / (row['asis_comisiones_plenas'] + row['aus_comisiones_plenas']), 2) 
                         if (row['asis_comisiones_plenas'] + row['aus_comisiones_plenas']) > 0 else 0
        },
        "comisiones_permanentes": {
            "asistencias": int(row['asis_comisiones_permanentes']),
            "ausencias": int(row['aus_comisiones_permanentes']),
            "porcentaje": round(100 * row['asis_comisiones_permanentes'] / (row['asis_comisiones_permanentes'] + row['aus_comisiones_permanentes']), 2) 
                         if (row['asis_comisiones_permanentes'] + row['aus_comisiones_permanentes']) > 0 else 0
        }
    }
    
    return JSONResponse(content={
        "Diputado": row['Diputado'],
        "Fraccion": row['Fraccion'],
        "pct_asistencia_total": pct_asistencia,
        "total_asistencias": int(total_asistencias),
        "total_ausencias": int(total_ausencias),
        "total_sesiones": int(total_sesiones),
        "desglose_por_tipo": desglose
    })

# Serie temporal anual (resumen por año)
@app.get("/time/asistencia-anual")
def serie_asistencia_anual():
    """Evolución anual del promedio de asistencia"""
    df = query("""
        SELECT 
            Anio,
            (COALESCE(SUM(AsistenciaPlenario), 0) +
             COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
             COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
             COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
             COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0)) AS total_asistencias,
             
            (COALESCE(SUM(AusenciasPlenario), 0) +
             COALESCE(SUM(AusenciasComisionesPlenas), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
             COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
             COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
             COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
             COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0)) AS total_ausencias
        FROM asistencia_legislativa
        GROUP BY Anio
        ORDER BY Anio
    """)
    
    # Calcular porcentaje de asistencia por año
    df['pct_asistencia'] = df.apply(
        lambda x: round(100 * x['total_asistencias'] / (x['total_asistencias'] + x['total_ausencias']), 2)
        if (x['total_asistencias'] + x['total_ausencias']) > 0 
        else 0,
        axis=1
    )
    
    return JSONResponse(content=df[['Anio', 'pct_asistencia']].to_dict(orient="records"))

# Estadísticas generales (resumen)
@app.get("/stats/resumen")
def estadisticas_resumen():
    """Resumen general de estadísticas de la base de datos"""
    # Obtener datos generales
    df_general = query("""
        SELECT 
            COUNT(DISTINCT Diputado) as total_diputados,
            COUNT(DISTINCT Fraccion) as total_fracciones,
            MIN(Anio) as anio_inicio,
            MAX(Anio) as anio_fin,
            COUNT(*) as total_registros
        FROM asistencia_legislativa
    """)
    
    # Obtener totales de asistencia
    df_totales = query("""
        SELECT 
            COALESCE(SUM(AsistenciaPlenario), 0) +
            COALESCE(SUM(AsistenciaComisionesPlenas), 0) +
            COALESCE(SUM(AsistenciaComisionesPermanentes), 0) +
            COALESCE(SUM(AsistenciaComisionesPermanentesEspeciales), 0) +
            COALESCE(SUM(AsistenciaComisionesEspeciales), 0) +
            COALESCE(SUM(AsistenciaReunionesDeFraccion), 0) +
            COALESCE(SUM(AsistenciaReunionesDeJefaturasDeFraccion), 0) AS total_asistencias,
            
            COALESCE(SUM(AusenciasPlenario), 0) +
            COALESCE(SUM(AusenciasComisionesPlenas), 0) +
            COALESCE(SUM(AusenciasComisionesPermanentes), 0) +
            COALESCE(SUM(AusenciasComisionesPermanentesEspeciales), 0) +
            COALESCE(SUM(AusenciasComisionesEspeciales), 0) +
            COALESCE(SUM(AusenciasReunionesDeFraccion), 0) +
            COALESCE(SUM(AusenciasReunionesDeJefaturasDeFraccion), 0) AS total_ausencias
        FROM asistencia_legislativa
    """)
    
    # Obtener lista de fracciones
    df_fracciones = query("SELECT DISTINCT Fraccion FROM asistencia_legislativa ORDER BY Fraccion")
    
    general = df_general.iloc[0]
    totales = df_totales.iloc[0]
    
    total_asistencias = totales['total_asistencias']
    total_ausencias = totales['total_ausencias']
    total_sesiones = total_asistencias + total_ausencias
    pct_asistencia_global = round(100 * total_asistencias / total_sesiones, 2) if total_sesiones > 0 else 0
    
    return JSONResponse(content={
        "periodo": {
            "anio_inicio": int(general['anio_inicio']),
            "anio_fin": int(general['anio_fin']),
            "total_anios": int(general['anio_fin'] - general['anio_inicio'] + 1)
        },
        "participantes": {
            "total_diputados": int(general['total_diputados']),
            "total_fracciones": int(general['total_fracciones']),
            "fracciones": df_fracciones['Fraccion'].tolist()
        },
        "sesiones": {
            "total_asistencias": int(total_asistencias),
            "total_ausencias": int(total_ausencias),
            "total_sesiones": int(total_sesiones),
            "pct_asistencia_global": pct_asistencia_global
        },
        "base_datos": {
            "total_registros": int(general['total_registros']),
            "promedio_registros_por_diputado": round(general['total_registros'] / general['total_diputados'], 1)
        }
    })

# Lista de diputados disponibles
@app.get("/diputados")
def lista_diputados():
    """Lista todos los diputados disponibles en la base de datos"""
    df = query("""
        SELECT DISTINCT 
            Diputado, 
            Fraccion,
            COUNT(*) as total_registros
        FROM asistencia_legislativa 
        GROUP BY Diputado, Fraccion
        ORDER BY Diputado
    """)
    return JSONResponse(content=df.to_dict(orient="records"))

# Lista de fracciones disponibles
@app.get("/fracciones")
def lista_fracciones():
    """Lista todas las fracciones políticas disponibles"""
    df = query("""
        SELECT 
            Fraccion,
            COUNT(DISTINCT Diputado) as total_diputados,
            COUNT(*) as total_registros
        FROM asistencia_legislativa 
        GROUP BY Fraccion
        ORDER BY total_diputados DESC
    """)
    return JSONResponse(content=df.to_dict(orient="records"))

# ENDPOINTS DE DEBUGGING (mantener los existentes)
@app.get("/debug/columnas")
def debug_columnas():
    """Endpoint para verificar las columnas de la tabla"""
    try:
        df = query("SELECT * FROM asistencia_legislativa LIMIT 5")
        return {
            "columnas": list(df.columns),
            "total_filas": len(df),
            "muestra_datos": df.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/kpi/asistencia-por-tipo-sesion-simple")
def asistencia_por_tipo_sesion_simple():
    """Versión simplificada para debugging"""
    try:
        # Consulta más simple
        df = query("""
            SELECT 
                SUM(AsistenciaPlenario) as total_asis_plenario,
                SUM(AusenciasPlenario) as total_aus_plenario
            FROM asistencia_legislativa
        """)
        
        if df.empty:
            return {"error": "No data found"}
        
        asis = df.iloc[0]['total_asis_plenario'] or 0
        aus = df.iloc[0]['total_aus_plenario'] or 0
        total = asis + aus
        pct = round(100 * asis / total, 2) if total > 0 else 0
        
        return {
            "tipo_sesion": "Plenario",
            "asistencias": int(asis),
            "ausencias": int(aus),
            "total": int(total),
            "porcentaje": pct
        }
        
    except Exception as e:
        return {"error": str(e)}

# ===== Iniciar servidor =====
if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print(f"📂 Ruta de base de datos: {DB_PATH}")
    print(f"✅ Base de datos existe: {os.path.exists(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("⚠️  ATENCIÓN: Base de datos no encontrada!")
        print("💡 Ejecuta 'python CSVDB.py' primero para crear la base de datos")
    
    print("\n📋 Endpoints disponibles:")
    print("   GET / - Información general de la API")
    print("   GET /health - Estado de la API y base de datos")
    print("   GET /kpi - Índice de todos los KPIs")
    print("   GET /kpi/asistencia - Porcentaje global de asistencia")
    print("   GET /kpi/asistencia-mensual - Evolución mensual")
    print("   GET /kpi/ranking?top=5&orden=desc - Ranking de diputados")
    print("   GET /kpi/sesiones-por-fraccion - Total sesiones por fracción")
    print("   GET /kpi/asistencia-por-tipo-sesion - Asistencia por tipo")
    print("   GET /kpi/comparacion-fracciones - Comparación entre fracciones")
    print("   GET /kpi/diputado/{nombre} - Estadísticas de un diputado")
    print("   GET /time/asistencia - Serie temporal por fracción")
    print("   GET /time/asistencia-anual - Serie temporal anual")
    print("   GET /stats/resumen - Resumen general")
    print("   GET /diputados - Lista de diputados")
    print("   GET /fracciones - Lista de fracciones")
    print("   GET /debug/columnas - Debug de columnas")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")