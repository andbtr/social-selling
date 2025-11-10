FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

# Instalar torch CPU PRIMERO
RUN pip install --no-cache-dir torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu

# Instalar el resto de dependencias (quitando torch de la lista)
RUN grep -v "^torch" requirements.txt > requirements-final.txt && \
    pip install --no-cache-dir -r requirements-final.txt

# Copy application
COPY . .

EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]