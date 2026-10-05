<?php
require __DIR__ . '/config.php';
header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? ($_POST['action'] ?? '');

try {
    switch ($action) {
        case 'login':          handle_login(); break;
        case 'logout':         handle_logout(); break;
        case 'check':          echo json_encode(['authenticated' => !empty($_SESSION['admin_logged_in'])]); break;
        case 'events':         require_login(); list_events(); break;
        case 'event':          require_login(); get_event(); break;
        case 'save_event':     require_login(); save_event(); break;
        case 'delete_event':   require_login(); delete_event(); break;
        case 'save_presensi_link': require_login(); save_presensi_link(); break;
        case 'upload_barcode': require_login(); upload_barcode(); break;
        case 'upload_material': require_login(); upload_material(); break;
        case 'history':        require_login(); get_history(); break;
        default:
            http_response_code(404);
            echo json_encode(['error' => 'Aksi tidak dikenal']);
    }
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}

function body_json(){
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

function handle_login(){
    $body = body_json();
    $password = $body['password'] ?? '';
    if ($password !== '' && hash_equals(ADMIN_PASSWORD, $password)) {
        $_SESSION['admin_logged_in'] = true;
        echo json_encode(['ok' => true]);
    } else {
        http_response_code(401);
        echo json_encode(['ok' => false, 'error' => 'Password salah']);
    }
}

function handle_logout(){
    $_SESSION = [];
    session_destroy();
    echo json_encode(['ok' => true]);
}

function attach_children($pdo, &$ev){
    $m = $pdo->prepare('SELECT title, url, original_name FROM materials WHERE event_id = ? ORDER BY id ASC');
    $m->execute([$ev['id']]);
    $materials = $m->fetchAll();
    foreach ($materials as &$mat) { $mat['originalName'] = $mat['original_name']; unset($mat['original_name']); }
    unset($mat);
    $ev['materials'] = $materials;

    $d = $pdo->prepare('SELECT caption, url FROM docs WHERE event_id = ? ORDER BY id ASC');
    $d->execute([$ev['id']]);
    $ev['docs'] = $d->fetchAll();

    $ev['date'] = $ev['event_date'];
    $ev['time'] = $ev['event_time'];
    $ev['publicUrl'] = $ev['public_url'];
    $ev['presensiLink'] = $ev['presensi_link'];
    $ev['presensiBarcodeUrl'] = $ev['presensi_barcode'] ? ('uploads/' . $ev['presensi_barcode']) : null;
}

function list_events(){
    $pdo = get_db();
    $events = $pdo->query('SELECT * FROM events ORDER BY created_at DESC')->fetchAll();
    foreach ($events as &$ev) { attach_children($pdo, $ev); }
    echo json_encode($events);
}

function get_event(){
    $pdo = get_db();
    $id = intval($_GET['id'] ?? 0);
    $stmt = $pdo->prepare('SELECT * FROM events WHERE id = ?');
    $stmt->execute([$id]);
    $ev = $stmt->fetch();
    if (!$ev) { http_response_code(404); echo json_encode(['error' => 'not found']); return; }
    attach_children($pdo, $ev);
    echo json_encode($ev);
}

function add_history($pdo, $event_id, $action){
    $pdo->prepare('INSERT INTO event_history (event_id, action, created_at) VALUES (?, ?, ?)')
        ->execute([$event_id, $action, date('Y-m-d H:i:s')]);
}

function save_event(){
    $pdo = get_db();
    $body = body_json();
    $id = intval($body['id'] ?? 0);
    $now = date('Y-m-d H:i:s');

    $title       = trim($body['title'] ?? '');
    $description = trim($body['description'] ?? '');
    $agency      = trim($body['agency'] ?? '');
    $ministry    = trim($body['ministry'] ?? '');
    $event_date  = !empty($body['date']) ? $body['date'] : null;
    $event_time  = trim($body['time'] ?? '');
    $location    = trim($body['location'] ?? '');
    $public_url  = trim($body['publicUrl'] ?? '');

    if ($id) {
        $stmt = $pdo->prepare('UPDATE events SET title=?, description=?, agency=?, ministry=?, event_date=?, event_time=?, location=?, public_url=?, updated_at=? WHERE id=?');
        $stmt->execute([$title, $description, $agency, $ministry, $event_date, $event_time, $location, $public_url, $now, $id]);
        add_history($pdo, $id, 'Detail event diperbarui');
    } else {
        $stmt = $pdo->prepare('INSERT INTO events (title, description, agency, ministry, event_date, event_time, location, public_url, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)');
        $stmt->execute([$title, $description, $agency, $ministry, $event_date, $event_time, $location, $public_url, $now, $now]);
        $id = (int)$pdo->lastInsertId();
        add_history($pdo, $id, 'Event dibuat');
    }

    // kumpulkan file materi lama, lalu hapus file fisik yang sudah tidak dipakai lagi
    // (misalnya materi dihapus dari form, atau file-nya diganti dengan yang baru)
    $oldFiles = $pdo->prepare('SELECT url FROM materials WHERE event_id = ?');
    $oldFiles->execute([$id]);
    $oldUrls = array_column($oldFiles->fetchAll(), 'url');
    $newUrls = array_map(function($m){ return trim($m['url'] ?? ''); }, $body['materials'] ?? []);
    foreach ($oldUrls as $oldUrl) {
        if ($oldUrl !== '' && !in_array($oldUrl, $newUrls, true)) {
            delete_material_file($oldUrl);
        }
    }

    $pdo->prepare('DELETE FROM materials WHERE event_id = ?')->execute([$id]);
    foreach (($body['materials'] ?? []) as $m) {
        $mt = trim($m['title'] ?? ''); $mu = trim($m['url'] ?? ''); $mo = trim($m['originalName'] ?? '');
        if ($mt === '' && $mu === '') continue;
        $pdo->prepare('INSERT INTO materials (event_id, title, url, original_name) VALUES (?,?,?,?)')->execute([$id, $mt, $mu, $mo]);
    }

    $pdo->prepare('DELETE FROM docs WHERE event_id = ?')->execute([$id]);
    foreach (($body['docs'] ?? []) as $d) {
        $du = trim($d['url'] ?? '');
        if ($du === '') continue;
        $pdo->prepare('INSERT INTO docs (event_id, caption, url) VALUES (?,?,?)')->execute([$id, trim($d['caption'] ?? ''), $du]);
    }

    echo json_encode(['ok' => true, 'id' => $id]);
}

function delete_event(){
    $pdo = get_db();
    $body = body_json();
    $id = intval($body['id'] ?? 0);

    $stmt = $pdo->prepare('SELECT presensi_barcode FROM events WHERE id = ?');
    $stmt->execute([$id]);
    $row = $stmt->fetch();
    if ($row && $row['presensi_barcode']) {
        $path = __DIR__ . '/uploads/' . $row['presensi_barcode'];
        if (is_file($path)) @unlink($path);
    }

    $m = $pdo->prepare('SELECT url FROM materials WHERE event_id = ?');
    $m->execute([$id]);
    foreach ($m->fetchAll() as $mat) { delete_material_file($mat['url']); }

    $pdo->prepare('DELETE FROM events WHERE id = ?')->execute([$id]);
    echo json_encode(['ok' => true]);
}

// Hapus file fisik materi di server. Hanya menghapus file yang benar-benar
// berada di dalam folder uploads/materials (mencegah path traversal / salah hapus
// file lain, dan mengabaikan begitu saja jika url-nya adalah link eksternal lama).
function delete_material_file($url){
    if (!$url) return;
    if (strpos($url, 'uploads/materials/') !== 0) return;
    $filename = basename($url);
    $path = __DIR__ . '/uploads/materials/' . $filename;
    if (is_file($path)) @unlink($path);
}

function upload_material(){
    if (empty($_FILES['file'])) {
        http_response_code(400); echo json_encode(['error' => 'File tidak ada']); return;
    }
    $file = $_FILES['file'];
    if ($file['error'] !== UPLOAD_ERR_OK) {
        http_response_code(400); echo json_encode(['error' => 'Upload gagal (kode ' . $file['error'] . ')']); return;
    }
    if ($file['size'] > 20 * 1024 * 1024) {
        http_response_code(400); echo json_encode(['error' => 'Ukuran file maksimal 20MB']); return;
    }

    $allowedExt = ['pdf' => true, 'doc' => true, 'docx' => true, 'ppt' => true, 'pptx' => true,
                   'xls' => true, 'xlsx' => true, 'jpg' => true, 'jpeg' => true, 'png' => true, 'zip' => true];
    $origName = $file['name'];
    $ext = strtolower(pathinfo($origName, PATHINFO_EXTENSION));
    if (!isset($allowedExt[$ext])) {
        http_response_code(400);
        echo json_encode(['error' => 'Jenis file tidak didukung. Gunakan PDF, Word, PowerPoint, Excel, gambar, atau ZIP.']);
        return;
    }

    $uploadsDir = __DIR__ . '/uploads/materials';
    if (!is_dir($uploadsDir)) mkdir($uploadsDir, 0755, true);

    $filename = 'materi_' . time() . '_' . bin2hex(random_bytes(4)) . '.' . $ext;
    if (!move_uploaded_file($file['tmp_name'], $uploadsDir . '/' . $filename)) {
        http_response_code(500); echo json_encode(['error' => 'Gagal menyimpan file di server']); return;
    }

    echo json_encode(['ok' => true, 'url' => 'uploads/materials/' . $filename, 'originalName' => $origName]);
}

function save_presensi_link(){
    $pdo = get_db();
    $body = body_json();
    $id = intval($body['id'] ?? 0);
    $link = trim($body['link'] ?? '');
    if (!$id) { http_response_code(400); echo json_encode(['error' => 'id wajib diisi']); return; }

    $pdo->prepare('UPDATE events SET presensi_link = ? WHERE id = ?')->execute([$link, $id]);
    add_history($pdo, $id, $link ? 'Link presensi diperbarui' : 'Link presensi dikosongkan');
    echo json_encode(['ok' => true]);
}

function upload_barcode(){
    $pdo = get_db();
    $id = intval($_POST['id'] ?? 0);

    if (!$id || empty($_FILES['file'])) {
        http_response_code(400); echo json_encode(['error' => 'id atau file tidak ada']); return;
    }
    $file = $_FILES['file'];
    if ($file['error'] !== UPLOAD_ERR_OK) {
        http_response_code(400); echo json_encode(['error' => 'Upload gagal (kode ' . $file['error'] . ')']); return;
    }
    if ($file['size'] > 5 * 1024 * 1024) {
        http_response_code(400); echo json_encode(['error' => 'Ukuran file maksimal 5MB']); return;
    }

    $allowed = ['image/png' => 'png', 'image/jpeg' => 'jpg', 'image/webp' => 'webp', 'image/gif' => 'gif'];
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);
    if (!isset($allowed[$mime])) {
        http_response_code(400); echo json_encode(['error' => 'File harus berupa gambar PNG/JPG/WEBP/GIF']); return;
    }

    $uploadsDir = __DIR__ . '/uploads';
    if (!is_dir($uploadsDir)) mkdir($uploadsDir, 0755, true);

    $filename = 'barcode_' . $id . '_' . time() . '_' . bin2hex(random_bytes(3)) . '.' . $allowed[$mime];
    if (!move_uploaded_file($file['tmp_name'], $uploadsDir . '/' . $filename)) {
        http_response_code(500); echo json_encode(['error' => 'Gagal menyimpan file di server']); return;
    }

    $stmt = $pdo->prepare('SELECT presensi_barcode FROM events WHERE id = ?');
    $stmt->execute([$id]);
    $old = $stmt->fetchColumn();
    if ($old && is_file($uploadsDir . '/' . $old)) @unlink($uploadsDir . '/' . $old);

    $pdo->prepare('UPDATE events SET presensi_barcode = ? WHERE id = ?')->execute([$filename, $id]);
    add_history($pdo, $id, 'Barcode presensi diperbarui');

    echo json_encode(['ok' => true, 'url' => 'uploads/' . $filename]);
}

function get_history(){
    $pdo = get_db();
    $id = intval($_GET['event_id'] ?? 0);
    $stmt = $pdo->prepare('SELECT action, created_at FROM event_history WHERE event_id = ? ORDER BY created_at DESC LIMIT 50');
    $stmt->execute([$id]);
    echo json_encode($stmt->fetchAll());
}
