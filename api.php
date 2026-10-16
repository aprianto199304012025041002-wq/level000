<?php
require __DIR__ . '/config.php';
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
ini_set('session.gc_maxlifetime', '43200');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'httponly' => true, 'samesite' => 'Lax', 'secure' => !empty($_SERVER['HTTPS'])]);
session_name('balmon_sid');
session_start();

function out($d, $c = 200) { http_response_code($c); echo json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); exit; }
function db() {
  static $p;
  if (!$p) {
    try {
      $p = new PDO('mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4', DB_USER, DB_PASS,
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
    } catch (Exception $e) { out(['error' => 'Koneksi database gagal. Periksa config.php'], 500); }
  }
  return $p;
}
function wa_target($t) {
  $o = [];
  foreach (preg_split('/[,;\n]+/', (string)$t, -1, PREG_SPLIT_NO_EMPTY) as $x) {
    $x = trim($x);
    if (strpos($x, '@') === false) {
      $x = preg_replace('/\D+/', '', $x);
      if ($x === '') continue;
      if ($x[0] === '0') $x = '62' . substr($x, 1);
      elseif ($x[0] === '8') $x = '62' . $x;
    }
    $o[] = $x;
  }
  return implode(',', $o);
}
function wa_send($msg) {
  if (!defined('WA_ENABLED') || !WA_ENABLED || !WA_TOKEN || !WA_TARGET || !function_exists('curl_init')) return null;
  $url = defined('WA_URL') && WA_URL ? WA_URL : 'https://wag.qosjogja.site/api/send-test';
  $ch = curl_init($url);
  curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_CONNECTTIMEOUT => 4, CURLOPT_TIMEOUT => 8,
    CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . WA_TOKEN, 'Content-Type: application/json'],
    CURLOPT_POSTFIELDS => json_encode(['to' => wa_target(WA_TARGET), 'message' => $msg], JSON_UNESCAPED_UNICODE)]);
  $r = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
  return ['http' => $code, 'error' => $err ?: null, 'body' => json_decode((string)$r, true) ?? $r];
}
function wa_lapor($d, $u) {
  $jn = ($d['jenis'] ?? '') === 'stasiun' ? 'Stasiun & Mobil Mon DF' : (($d['jenis'] ?? '') === 'lainnya' ? 'Lainnya' : 'Perangkat SMFR');
  $obj = ($d['jenis'] ?? '') === 'stasiun' ? ($d['stasiun'] ?? '-') : (($d['jenis'] ?? '') === 'lainnya' ? '-' : trim(($d['nama'] ?? '-') . (empty($d['aid']) ? '' : ' [' . $d['aid'] . ']')));
  $m = "*LAPORAN BARU*\n";
  $m .= "Jenis: $jn\n";
  if ($obj !== '-') $m .= (($d['jenis'] ?? '') === 'stasiun' ? 'Stasiun: ' : 'Perangkat: ') . "$obj\n";
  if (!empty($d['kon'])) $m .= 'Kondisi: ' . $d['kon'] . "\n";
  if (!empty($d['dasar'])) $m .= 'Dasar: ' . $d['dasar'] . "\n";
  $m .= 'Tanggal: ' . ($d['tgl'] ?? '-') . "\n";
  $m .= 'Pelapor: ' . (($d['petugas'] ?? '') ?: $u['nama']) . "\n";
  $m .= 'Keterangan: ' . (($d['ket'] ?? '') ?: '-');
  $host = $_SERVER['HTTP_HOST'] ?? '';
  if ($host) $m .= "\n\nBuka aplikasi: http" . (!empty($_SERVER['HTTPS']) ? 's' : '') . "://$host/";
  return $m;
}
function user() { return $_SESSION['u'] ?? null; }
function need($admin = false) {
  $u = user();
  if (!$u) out(['error' => 'Silakan login terlebih dahulu'], 401);
  if ($admin && $u['role'] !== 'admin') out(['error' => 'Hanya untuk administrator'], 403);
  return $u;
}

$a = $_GET['a'] ?? '';
$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) $in = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') !== 'fetch') out(['error' => 'Permintaan tidak valid'], 400);

try {
switch ($a) {
  case 'me':
    out(['user' => user()]);

  case 'login':
    $un = trim($in['username'] ?? ''); $pw = (string)($in['password'] ?? '');
    $s = db()->prepare('SELECT * FROM users WHERE username = ?'); $s->execute([$un]); $r = $s->fetch();
    if (!$r || !password_verify($pw, $r['pass_hash'])) { usleep(700000); out(['error' => 'Username atau kata sandi salah'], 401); }
    session_regenerate_id(true);
    $_SESSION['u'] = ['id' => (int)$r['id'], 'username' => $r['username'], 'nama' => $r['nama'], 'role' => $r['role']];
    out(['user' => $_SESSION['u']]);

  case 'logout':
    $_SESSION = []; session_destroy(); out(['ok' => 1]);

  case 'base':
    need();
    echo require __DIR__ . '/private/base.php';
    exit;

  case 'docs':
    need();
    $rows = db()->query('SELECT id, data FROM docs')->fetchAll();
    out(['docs' => array_map(function ($r) { return ['id' => $r['id'], 'data' => json_decode($r['data'], true)]; }, $rows)]);

  case 'save':
    $u = need();
    $id = $in['id'] ?? ''; $d = $in['data'] ?? null;
    if (!preg_match('/^[A-Za-z0-9_.-]{1,120}$/', $id) || !is_array($d)) out(['error' => 'Data tidak valid'], 400);
    if ($u['role'] !== 'admin' && ($d['kind'] ?? '') === 'del') out(['error' => 'Hanya administrator yang dapat menghapus data'], 403);
    $so = db()->prepare('SELECT data FROM docs WHERE id = ?'); $so->execute([$id]); $ov = $so->fetchColumn(); $ov = $ov ? json_decode($ov, true) : [];
    $tlj = ['stasiun', 'lainnya'];
    if ($u['role'] !== 'admin' && (($d['kind'] ?? '') === 'lapor' || ($ov['kind'] ?? '') === 'lapor' || in_array($d['jenis'] ?? '', $tlj, true) || in_array($ov['jenis'] ?? '', $tlj, true))) {
      foreach (['st', 'tl', 'tltgl', 'tlby'] as $k) {
        $nv = (string)($d[$k] ?? ''); $o = (string)($ov[$k] ?? '');
        if ($k === 'st') { if ($nv === '') $nv = 'Baru'; if ($o === '') $o = 'Baru'; }
        if ($nv !== $o) out(['error' => 'Hanya administrator yang dapat mengisi tindak lanjut'], 403);
      }
    }
    $j = json_encode($d, JSON_UNESCAPED_UNICODE);
    if (strlen($j) > 400000) out(['error' => 'Data terlalu besar'], 400);
    db()->prepare('INSERT INTO docs (id, data, updated_by) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE data = VALUES(data), updated_by = VALUES(updated_by)')
      ->execute([$id, $j, $u['username']]);
    if (!$ov && ($d['kind'] ?? '') === 'lapor') {
      $wm = wa_lapor($d, $u);
      register_shutdown_function(function () use ($wm) {
        if (function_exists('fastcgi_finish_request')) fastcgi_finish_request();
        try { wa_send($wm); } catch (Throwable $e) {}
      });
    }
    out(['ok' => 1]);

  case 'del':
    need(true);
    $id = $in['id'] ?? '';
    if (!preg_match('/^[A-Za-z0-9_.-]{1,120}$/', $id)) out(['error' => 'ID tidak valid'], 400);
    db()->prepare('DELETE FROM docs WHERE id = ?')->execute([$id]);
    out(['ok' => 1]);

  case 'upload':
    need();
    if (empty($_FILES['file']) || $_FILES['file']['error'] !== UPLOAD_ERR_OK) out(['error' => 'Berkas gagal diunggah'], 400);
    $f = $_FILES['file'];
    if ($f['size'] > 6 * 1024 * 1024) out(['error' => 'Ukuran foto maksimal 6 MB'], 400);
    $info = @getimagesize($f['tmp_name']);
    $map = [IMAGETYPE_JPEG => 'jpg', IMAGETYPE_PNG => 'png', IMAGETYPE_WEBP => 'webp'];
    $ext = $map[$info[2] ?? 0] ?? null;
    if (!$ext) out(['error' => 'Format foto harus JPG, PNG, atau WEBP'], 400);
    $id = substr(preg_replace('/[^A-Za-z0-9_-]/', '_', $_POST['id'] ?? 'asset'), 0, 60);
    $dir = __DIR__ . '/uploads';
    if (!is_dir($dir)) mkdir($dir, 0755, true);
    $name = 'asset_' . $id . '_' . time() . '.' . $ext;
    if (!move_uploaded_file($f['tmp_name'], $dir . '/' . $name)) out(['error' => 'Gagal menyimpan foto di server'], 500);
    out(['path' => 'uploads/' . $name]);

  case 'wa_test':
    $u = need(true);
    if (!defined('WA_ENABLED') || !WA_ENABLED || !WA_TOKEN || !WA_TARGET) out(['error' => 'WA belum aktif. Isi WA_ENABLED, WA_TOKEN, WA_TARGET di config.php'], 400);
    out(['respon_gateway' => wa_send("*TES NOTIFIKASI*\nNotifikasi laporan Manajemen Perangkat SMFR berhasil terhubung. Dikirim oleh " . $u['nama'] . '.')]);

  case 'users':
    need(true);
    out(['users' => db()->query('SELECT username, nama, role FROM users ORDER BY username')->fetchAll()]);

  case 'user_save':
    need(true);
    $un = trim($in['username'] ?? ''); $nm = trim($in['nama'] ?? ''); $pw = (string)($in['password'] ?? '');
    $rl = ($in['role'] ?? '') === 'admin' ? 'admin' : 'petugas';
    if (!preg_match('/^[A-Za-z0-9_.-]{3,40}$/', $un) || $nm === '' || strlen($pw) < 8) out(['error' => 'Isi username (3-40 huruf/angka), nama, dan kata sandi minimal 8 karakter'], 400);
    db()->prepare('INSERT INTO users (username, nama, pass_hash, role) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE nama = VALUES(nama), pass_hash = VALUES(pass_hash), role = VALUES(role)')
      ->execute([$un, $nm, password_hash($pw, PASSWORD_DEFAULT), $rl]);
    out(['ok' => 1]);

  case 'user_del':
    $u = need(true);
    $un = (string)($in['username'] ?? '');
    if ($un === $u['username']) out(['error' => 'Akun yang sedang dipakai tidak bisa dihapus'], 400);
    db()->prepare('DELETE FROM users WHERE username = ?')->execute([$un]);
    out(['ok' => 1]);

  case 'pw':
    $u = need();
    $old = (string)($in['old'] ?? ''); $new = (string)($in['new'] ?? '');
    if (strlen($new) < 8) out(['error' => 'Kata sandi baru minimal 8 karakter'], 400);
    $s = db()->prepare('SELECT pass_hash FROM users WHERE id = ?'); $s->execute([$u['id']]); $r = $s->fetch();
    if (!$r || !password_verify($old, $r['pass_hash'])) out(['error' => 'Kata sandi lama salah'], 400);
    db()->prepare('UPDATE users SET pass_hash = ? WHERE id = ?')->execute([password_hash($new, PASSWORD_DEFAULT), $u['id']]);
    out(['ok' => 1]);

  default:
    out(['error' => 'Aksi tidak dikenal'], 404);
}
} catch (PDOException $e) {
  out(['error' => 'Kesalahan database. Pastikan setup.php sudah dijalankan.'], 500);
}