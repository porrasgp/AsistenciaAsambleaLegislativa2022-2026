# Lista de PYMES Activas - MEIC Costa Rica

Proyecto para la consulta, extracción y análisis de la **Lista de PYMES Activas** publicada por el Ministerio de Economía, Industria y Comercio (MEIC) de Costa Rica.

## 📋 Descripción

Este proyecto obtiene y procesa la información pública de las Pequeñas y Medianas Empresas (PYMES) activas registradas en Costa Rica, disponible en el portal de transparencia del MEIC.

- **Fuente oficial:** [Lista de PYMES Activas - MEIC](https://www.meic.go.cr/transparencia/apoyo-a-la-pequena-y-mediana-empresa/lista-de-pymes-activas/)
- **Institución:** Ministerio de Economía, Industria y Comercio (MEIC)
- **País:** Costa Rica

## 🎯 Objetivos

- Descargar/consultar el listado oficial de PYMES activas.
- Normalizar y estructurar los datos en un formato utilizable (CSV, JSON, base de datos).
- Facilitar búsquedas, filtros y análisis por sector, región, tamaño, etc.
- Proveer una API o script reutilizable para consultas periódicas.

## 🚀 Características

- [ ] Extracción automatizada de datos desde el sitio del MEIC
- [ ] Limpieza y normalización de la información
- [ ] Exportación a CSV / JSON
- [ ] Búsqueda y filtrado por criterios (provincia, actividad económica, tamaño)
- [ ] API REST (opcional)
- [ ] Dashboard de visualización (opcional)

## 🛠️ Tecnologías

> Ajusta esta sección según tu stack real.

- **Lenguaje:** Python 3.11+ / Node.js / etc.
- **Scraping:** BeautifulSoup, Scrapy, Playwright, Puppeteer
- **Datos:** pandas, SQLite / PostgreSQL
- **API:** FastAPI / Express
- **Frontend (opcional):** React / Vue

## 📦 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/meic-pymes-activas.git
cd meic-pymes-activas

# Crear entorno virtual (Python)
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt
# Lista-PYMES-2020-2026
