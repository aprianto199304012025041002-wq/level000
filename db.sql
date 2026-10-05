-- Skema database Dashboard Event
-- Cara pakai: buka phpMyAdmin di hPanel Hostinger (Databases > phpMyAdmin),
-- pilih database yang sudah kamu buat, lalu buka tab "Import" dan upload file ini.
--
-- SUDAH PERNAH IMPORT SEBELUMNYA? Tabel `materials` di file ini menambahkan kolom
-- baru `original_name` (untuk fitur upload dokumen materi). Kolom ini tidak akan
-- otomatis dibuat lewat re-import karena tabelnya sudah ada. Cukup jalankan query
-- ALTER TABLE berikut sekali saja di tab "SQL" phpMyAdmin:
--
-- ALTER TABLE materials ADD COLUMN original_name VARCHAR(255) DEFAULT '';

CREATE TABLE IF NOT EXISTS events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL DEFAULT '',
  description TEXT,
  agency VARCHAR(255) DEFAULT '',
  ministry VARCHAR(255) DEFAULT '',
  event_date DATE NULL,
  event_time VARCHAR(100) DEFAULT '',
  location VARCHAR(255) DEFAULT '',
  public_url VARCHAR(500) DEFAULT '',
  presensi_link VARCHAR(500) DEFAULT '',
  presensi_barcode VARCHAR(255) DEFAULT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS materials (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  title VARCHAR(255) DEFAULT '',
  url VARCHAR(500) DEFAULT '',
  original_name VARCHAR(255) DEFAULT '',
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS docs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  caption VARCHAR(255) DEFAULT '',
  url VARCHAR(500) DEFAULT '',
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS event_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  action VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
