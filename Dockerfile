# 1. Gunakan image dasar (base image)
FROM python:3.10-slim

# 2. Tentukan folder kerja di dalam container
WORKDIR /app

# 3. Copy semua file dari komputer ke dalam container
COPY . .

# 4. Install library yang dibutuhkan (jika ada)
RUN pip install flask

# 5. Jalankan aplikasi
CMD ["python", "app.py"]
