FROM python:3.11-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar código y base de datos
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando para iniciar FastAPI con uvicorn
CMD ["uvicorn", "FAST_API:app", "--host", "0.0.0.0", "--port", "8000"]
