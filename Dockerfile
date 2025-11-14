FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar torch CPU primero
RUN pip install --no-cache-dir \
    torch==2.9.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Instalar TODAS las dependencias (torch se saltará porque ya está)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]