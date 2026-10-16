MANAJEMEN PERANGKAT SMFR - PANDUAN PASANG DI HOSTINGER
================================================================

Isi paket
  index.html     Aplikasi (tampilan)
  api.php        Server: login, simpan data, unggah foto
  setup.php      Pembuat tabel dan akun admin (dipakai SEKALI lalu dihapus)
  config.php     Pengaturan database (WAJIB diisi)
  private/       Data awal dari Excel (terlindungi, hanya terbaca setelah login)
  uploads/       Folder foto perangkat yang diunggah dari aplikasi

Langkah pemasangan
  1. hPanel Hostinger > Websites > Databases > MySQL Databases.
     Buat database baru, user, dan kata sandi. Catat ketiganya.
  2. Buka config.php, isi DB_NAME, DB_USER, DB_PASS sesuai langkah 1.
     DB_HOST biasanya tetap 'localhost'.
  3. hPanel > File Manager > public_html (atau folder subdomain).
     Unggah file zip ini lalu Extract, sehingga index.html, api.php, dan
     lainnya berada langsung di public_html. Pastikan file .htaccess ikut
     (aktifkan "Show hidden files" di File Manager).
  4. Buka https://domainanda.com/setup.php di browser.
     Buat akun administrator pertama (username, nama, kata sandi min. 8 karakter).
  5. HAPUS file setup.php dari File Manager.
  6. Buka https://domainanda.com/ lalu login.
  7. Menu "Pengguna" (khusus administrator): tambah akun untuk tiap petugas
     Balmon Yogyakarta, atau hapus akun yang tidak dipakai.
  8. Aktifkan SSL gratis: hPanel > Security > SSL, agar login terenkripsi (https).

Foto perangkat
  - Foto baru: buka detail aset > "Unggah / ganti foto", atau lewat form
    Tambah/Edit aset. Di HP, tombol ini bisa langsung membuka kamera.
    Foto otomatis dikecilkan (maks. 1280 px) sebelum diunggah.
  - Foto lama dari Excel (kolom Foto Perangkat, contoh Asset_Images/....jpg):
    unggah folder Asset_Images (dan Tag_Images) ke public_html dengan nama
    folder yang sama. Foto akan tampil otomatis.

Catatan
  - Data awal (Excel) tersimpan di private/base.php dan tidak diubah.
    Perubahan (tambah, edit, hapus) tersimpan di database MySQL.
  - Semua petugas yang login melihat data yang sama; layar menyegarkan diri
    tiap 30 detik. Jika dua orang mengubah data yang sama bersamaan,
    perubahan terakhir yang berlaku.
  - Cadangkan database secara berkala: hPanel > Databases > phpMyAdmin > Export.
  - Lupa kata sandi admin: hapus baris akun di tabel users lewat phpMyAdmin,
    lalu unggah lagi setup.php untuk membuat admin baru.
  - Butuh PHP 7.4 atau lebih baru (Hostinger memakai PHP 8.x secara bawaan).
