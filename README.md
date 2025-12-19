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

### 3.4 Ordering
Sistem tidak menjamin urutan global antar event.  
Pendekatan ini mengikuti karakteristik sistem terdistribusi, di mana konsistensi dan ketersediaan lebih diutamakan dibanding urutan absolut.

### 3.5 Retry dan Delivery Guarantee
Publisher mensimulasikan skema **at-least-once delivery**, sehingga event dapat dikirim lebih dari satu kali.  
Deduplication pada Aggregator memastikan bahwa event duplikat tidak memengaruhi hasil akhir.

---
## 3. Keputusan Desain

### 3.1 Idempotency
Setiap event diidentifikasi secara unik menggunakan kombinasi:
- `topic`
- `event_id`

Jika event dengan kombinasi tersebut sudah pernah diproses, maka event akan diabaikan.

---

### 3.2 Deduplication Store
Deduplication diimplementasikan menggunakan SQLite dengan primary key `(topic, event_id)`.  
Pendekatan ini menjamin tidak adanya duplikasi data walaupun event dikirim ulang oleh publisher.

---

### 3.3 Concurrency dan Transaksi
Aggregator menggunakan:
- `asyncio.Queue` untuk antrean event
- Worker background untuk pemrosesan paralel

Operasi penyimpanan event dilakukan secara atomik di level database untuk menjaga konsistensi data.

---

### 3.4 Ordering
Sistem tidak menjamin urutan global antar event.  
Pendekatan ini mengikuti karakteristik sistem terdistribusi, di mana konsistensi dan ketersediaan lebih diutamakan dibanding urutan absolut.

---

### 3.5 Retry dan Delivery Guarantee
Publisher mensimulasikan skema **at-least-once delivery**, sehingga event dapat dikirim lebih dari satu kali.  
Deduplication pada Aggregator memastikan bahwa event duplikat tidak memengaruhi hasil akhir.

---
## 4. Build dan Menjalankan Sistem
### 4.1 Build dan Run dengan Docker Compose

Untuk membangun image dan menjalankan seluruh service, gunakan perintah berikut:

```bash
docker compose up --build
```

Perintah ini akan:
- Membangun image untuk aggregator dan publisher
- Menjalankan kedua service dalam satu network Docker
- Mengaktifkan volume untuk penyimpanan database SQLite

