FROM python:3.10-slim

# Set environment variables agar output log Python langsung muncul
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy & install requirements terlebih dahulu untuk caching layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh file proyek
COPY . .

# Expose port default (Railway akan otomatis override via $PORT)
EXPOSE 7860

# Jalankan aplikasi
CMD ["python", "app.py"]
