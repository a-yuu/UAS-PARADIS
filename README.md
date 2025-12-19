# UAS PARADIS – Distributed Log Aggregator System

Repository ini berisi implementasi **sistem terdistribusi berbasis Docker** untuk memenuhi **Ujian Akhir Semester (UAS)** mata kuliah **Sistem Paralel dan Terdistribusi**.  
Sistem dirancang untuk mendemonstrasikan konsep **multi-service architecture, idempotency, deduplication, concurrency, persistence, dan observability**.

---

## 1. Ringkasan Sistem

Sistem ini merupakan **log/event aggregator** yang menerima event dari service lain (publisher), memprosesnya secara paralel, dan memastikan bahwa **event duplikat tidak diproses lebih dari satu kali**.

Sistem terdiri dari dua service utama:
- **Aggregator**: menerima, memproses, dan menyimpan event
- **Publisher**: mensimulasikan pengiriman event (termasuk duplikat)

Seluruh sistem berjalan di **jaringan lokal Docker** tanpa dependensi eksternal.

---

## 2. Arsitektur Sistem
Sistem terdiri dari dua service utama, yaitu Publisher sebagai pengirim event dan Aggregator sebagai penerima dan pemroses event. Keduanya berkomunikasi melalui protokol HTTP di dalam Docker network lokal. Aggregator menyimpan data event ke dalam database SQLite yang dipersistensikan menggunakan Docker volume sehingga data tetap tersedia walaupun container dihentikan atau dijalankan ulang.

## 3. Keputusan Desain
### 3.1 Idempotency
Setiap event diidentifikasi secara unik menggunakan kombinasi:
- `topic`
- `event_id`
Jika event dengan kombinasi tersebut sudah pernah diproses, maka event akan diabaikan.

### 3.2 Deduplication Store
Deduplication diimplementasikan menggunakan SQLite dengan primary key `(topic, event_id)`.  
Pendekatan ini menjamin tidak adanya duplikasi data walaupun event dikirim ulang oleh publisher.

### 3.3 Concurrency dan Transaksi
Aggregator menggunakan:
- `asyncio.Queue` untuk antrean event
- Worker background untuk pemrosesan paralel
Operasi penyimpanan event dilakukan secara atomik di level database untuk menjaga konsistensi data.

### 3.4 Fault Tolerance & Persistence
Data disimpan di /app/data/dedup.db yang terhubung ke Docker Volume aggregator_data. Jika sistem crash atau container di-restart, sistem akan memulihkan state deduplikasi dari database tersebut.

## 4. Build dan Menjalankan Sistem
### 4.1 Persiapan
Pastikan Anda telah menginstal Docker dan Docker Compose di perangkat Anda.
### 4.2 Build dan Run
Gunakan perintah berikut untuk membangun image dan menjalankan seluruh layanan:
```bash
docker compose up --build
```
Perintah ini akan:
- Membangun image untuk aggregator dan publisher
- Menjalankan kedua service dalam satu network Docker
- Mengaktifkan volume untuk penyimpanan database SQLite

### 4.3 Mengecek Status Service
Pastikan seluruh service berjalan dengan benar menggunakan perintah:
```bash
docker compose ps
```
- uas_aggregator: Harus berstatus Up (healthy).
- uas_publisher: Akan berjalan melakukan simulasi, lalu berstatus Exited (0) setelah selesai mengirim event.

## 5. API Endpoints (Aggregator)
### 5.1 POST /publish
Menerima batch event log. Payload: List[Event]
### 5.2 GET /stats
Melihat metrik sistem secara real-time.
- URL: http://localhost:8080/stats
- Output: received, unique_processed, duplicate_dropped, uptime.
### 5.3 GET /events
Mengambil daftar log unik yang telah berhasil diproses.
- URL: http://localhost:8080/events

## 6. Asumsi Sistem
1. Identitas Unik: Diasumsikan setiap produser log bertanggung jawab menghasilkan event_id yang unik (misal: UUID).
2. Jaringan Lokal: Sistem diasumsikan berjalan dalam lingkungan terisolasi sesuai regulasi UAS, sehingga tidak ada pengecekan ke clock server eksternal.
3. Format Waktu: Menggunakan standar ISO8601 untuk timestamp.

## 7. Testing
### 7.1 Menjalankan Unit Test
Pengujian dilakukan menggunakan pytest di dalam lingkungan container untuk menjamin konsistensi:
```
docker compose exec aggregator pytest test/test_aggregator.py
```
### 7.2 Cakupan Test (12 Test Cases)
- Deduplication: Verifikasi ID ganda diabaikan.
- Persistence: Data tetap ada setelah container di-recreate.
- Concurrency: Uji coba multi-worker tanpa duplikasi data.
- Schema Validation: Memastikan format JSON dan timestamp benar.
- Statistik: Akurasi perhitungan data masuk vs data drop.
  
## 8. Video Demo
Tonton demo teknis operasional sistem melalui tautan berikut:
👉 https://youtu.be/-ahaAWS_-as

