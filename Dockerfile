FROM python:3.11-slim
WORKDIR /app

# Tambahkan baris ini untuk memberitahu Python bahwa /app adalah root
ENV PYTHONPATH=/app

RUN useradd -m appuser && chown -R appuser:appuser /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
RUN mkdir -p data && chown -R appuser:appuser data
USER appuser
COPY test ./test
EXPOSE 8080

# Pastikan CMD memanggil module dengan titik, bukan path file
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
