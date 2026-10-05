# Cara pasang Dashboard Event di Hostinger

Paket ini pakai PHP + MySQL (didukung di semua plan Hosting Web Hostinger).

## 1. Buat database MySQL
1. Login ke **hPanel** Hostinger.
2. Buka **Databases > MySQL Databases**.
3. Buat database baru + user + password. Catat 3 hal ini:
   - Nama database (contoh: `u123456789_eventdb`)
   - Nama user (contoh: `u123456789_admin`)
   - Password user
   - Host biasanya `localhost`

## 2. Import struktur tabel
1. Masih di hPanel, buka **phpMyAdmin** lalu pilih database yang baru dibuat.
2. Klik tab **Import**, pilih file `db.sql` dari paket ini, lalu jalankan.
3. Pastikan 4 tabel muncul: `events`, `materials`, `docs`, `event_history`.

## 3. Edit `config.php`
Buka file `config.php`, ganti bagian ini dengan data dari langkah 1:
```php
define('DB_NAME', 'u123456789_eventdb');
define('DB_USER', 'u123456789_admin');
define('DB_PASS', 'password-database-kamu');
```
Lalu ganti password login admin (WAJIB, jangan dibiarkan default):
```php
define('ADMIN_PASSWORD', 'password-rahasia-kamu');
```

## 4. Upload file ke Hostinger
1. Buka **File Manager** di hPanel (atau pakai FTP).
2. Masuk ke folder `public_html` (atau subfolder jika mau taruh di alamat khusus, misalnya `public_html/admin-event`).
3. Upload semua isi paket ini: `index.html`, `api.php`, `config.php`, dan folder `uploads/` (beserta isinya).

## 5. Buka dan login
1. Akses `https://namadomainkamu.com/` (atau `/admin-event/` kalau ditaruh di subfolder).
2. Masuk dengan password yang kamu set di `ADMIN_PASSWORD`.
3. Mulai tambah event, isi link presensi + upload barcode, dan cek riwayatnya.

## Catatan penting
- **Ganti `ADMIN_PASSWORD`** — ini satu-satunya proteksi login dashboard ini. Jangan pakai password bawaan.
- Sebaiknya taruh dashboard ini di alamat yang tidak sembarang orang tahu (atau di subfolder khusus admin), karena tidak ada sistem multi-user/role di sini — cuma satu password admin.
- File gambar barcode disimpan di folder `uploads/`. Folder ini sudah diberi `.htaccess` supaya tidak bisa dipakai menjalankan script, hanya untuk menyimpan gambar.
- Kalau nanti mau tambah HTTPS paksa, aktifkan **SSL** gratis dari hPanel (Hostinger sudah sediakan Let's Encrypt gratis) dan set redirect HTTP→HTTPS.
- "Salin data (untuk publish)" tetap ada untuk menyalin data event dalam format JSON, kalau kamu mau minta Claude bikinkan halaman publik terpisah dari data itu.
