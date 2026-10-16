<?php
// Jalankan SEKALI di browser: https://domainanda.com/setup.php, lalu HAPUS file ini.
require __DIR__ . '/config.php';
function h($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
try {
  $pdo = new PDO('mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4', DB_USER, DB_PASS, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (Exception $e) { die('Koneksi database gagal. Periksa nama database, user, dan password di config.php.'); }
$pdo->exec("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(40) NOT NULL UNIQUE, nama VARCHAR(100) NOT NULL, pass_hash VARCHAR(255) NOT NULL, role ENUM('admin','petugas') NOT NULL DEFAULT 'petugas', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
$pdo->exec("CREATE TABLE IF NOT EXISTS docs (id VARCHAR(120) PRIMARY KEY, data MEDIUMTEXT NOT NULL, updated_by VARCHAR(40), updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
$has = (int)$pdo->query('SELECT COUNT(*) FROM users')->fetchColumn() > 0;
$err = ''; $ok = false;
if (!$has && $_SERVER['REQUEST_METHOD'] === 'POST') {
  $un = trim($_POST['username'] ?? ''); $nm = trim($_POST['nama'] ?? ''); $pw = (string)($_POST['password'] ?? '');
  if (!preg_match('/^[A-Za-z0-9_.-]{3,40}$/', $un) || $nm === '' || strlen($pw) < 8) {
    $err = 'Isi username (3-40 huruf/angka), nama lengkap, dan kata sandi minimal 8 karakter.';
  } else {
    $pdo->prepare("INSERT INTO users (username, nama, pass_hash, role) VALUES (?, ?, ?, 'admin')")->execute([$un, $nm, password_hash($pw, PASSWORD_DEFAULT)]);
    $ok = true; $has = true;
  }
}
?><!DOCTYPE html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Setup Manajemen Perangkat SMFR</title>
<style>body{font:15px/1.5 system-ui,sans-serif;background:#eef3fb;color:#12264a;display:grid;place-items:center;min-height:100vh;margin:0;padding:16px}.b{background:#fff;border-radius:14px;padding:26px;width:min(420px,100%);box-shadow:0 8px 30px #1d6fe022}input,button{font:inherit;padding:9px 11px;width:100%;box-sizing:border-box;margin:4px 0 12px;border:1px solid #cdd8ea;border-radius:8px}button{background:#1d6fe0;color:#fff;border:0;cursor:pointer}.e{color:#c2410c}</style></head><body><div class="b">
<h2>Setup Manajemen Perangkat SMFR</h2>
<?php if ($ok): ?><p><b>Berhasil.</b> Tabel database dan akun administrator sudah dibuat.</p><p class="e"><b>Penting:</b> hapus file <code>setup.php</code> dari hosting sekarang, lalu buka <a href="index.html">halaman utama</a> dan login.</p>
<?php elseif ($has): ?><p>Setup sudah pernah dijalankan. Hapus file <code>setup.php</code> dari hosting, lalu buka <a href="index.html">halaman utama</a>.</p>
<?php else: ?><p>Buat akun administrator pertama. Akun petugas lain bisa ditambahkan dari menu <b>Pengguna</b> setelah login.</p>
<?php if ($err): ?><p class="e"><?= h($err) ?></p><?php endif; ?>
<form method="post"><label>Username</label><input name="username" required autocomplete="username"><label>Nama lengkap</label><input name="nama" required><label>Kata sandi (min. 8 karakter)</label><input name="password" type="password" required autocomplete="new-password"><button>Buat administrator</button></form>
<?php endif; ?></div></body></html>
