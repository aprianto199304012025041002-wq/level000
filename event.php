<?php
// ============================================================
// Halaman publik event — otomatis ambil data dari database.
// Akses lewat: event.php?id=3   atau   event.php?slug=nama-event
// (slug dihasilkan otomatis dari judul event, gak perlu diisi manual)
// ============================================================

require __DIR__ . '/config.php';

function slugify($text){
    $text = trim((string)$text);
    $text = mb_strtolower($text, 'UTF-8');
    $text = preg_replace('/[^a-z0-9]+/', '-', $text);
    return trim($text, '-');
}
function esc($s){ return htmlspecialchars((string)($s ?? ''), ENT_QUOTES, 'UTF-8'); }

$pdo = get_db();
$id = intval($_GET['id'] ?? 0);
$slugParam = trim($_GET['slug'] ?? '');

$ev = null;
if ($id) {
    $stmt = $pdo->prepare('SELECT * FROM events WHERE id = ?');
    $stmt->execute([$id]);
    $ev = $stmt->fetch();
} elseif ($slugParam !== '') {
    foreach ($pdo->query('SELECT * FROM events')->fetchAll() as $row) {
        if (slugify($row['title']) === $slugParam) { $ev = $row; break; }
    }
}

if (!$ev) {
    http_response_code(404);
    ?>
    <!DOCTYPE html><html lang="id"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event tidak ditemukan</title>
    <link rel="icon" type="image/png" href="logo-balmon.png">
    <style>
      body{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
        font-family:-apple-system,Segoe UI,Roboto,sans-serif; background:#eef4fc; color:#0f2a52; text-align:center; }
      .box{ padding:48px 32px; }
      h1{ margin:0 0 8px; font-size:26px; }
      p{ color:#5b6b83; margin:0; }
    </style>
    </head>
    <body>
      <div class="box">
        <h1>Event tidak ditemukan</h1>
        <p>Link ini mungkin salah, atau eventnya sudah dihapus dari dashboard.</p>
      </div>
    </body></html>
    <?php
    exit;
}

$m = $pdo->prepare('SELECT title, url FROM materials WHERE event_id = ? ORDER BY id ASC');
$m->execute([$ev['id']]);
$materials = $m->fetchAll();

$d = $pdo->prepare('SELECT caption, url FROM docs WHERE event_id = ? ORDER BY id ASC');
$d->execute([$ev['id']]);
$docs = $d->fetchAll();

$bulan = ['01'=>'Januari','02'=>'Februari','03'=>'Maret','04'=>'April','05'=>'Mei','06'=>'Juni',
          '07'=>'Juli','08'=>'Agustus','09'=>'September','10'=>'Oktober','11'=>'November','12'=>'Desember'];
$dateFormatted = $ev['event_date'] ?: '';
if ($dateFormatted) {
    $parts = explode('-', $dateFormatted);
    if (count($parts) === 3) $dateFormatted = intval($parts[2]) . ' ' . ($bulan[$parts[1]] ?? $parts[1]) . ' ' . $parts[0];
}

$hasBarcodeImg   = !empty($ev['presensi_barcode']);
$hasPresensiLink = !empty($ev['presensi_link']);

// Presensi otomatis ditutup kalau tanggal kegiatan sudah lewat
$isPastEvent = false;
if (!empty($ev['event_date'])) {
    $isPastEvent = date('Y-m-d') > $ev['event_date'];
}

// Nama instansi untuk header (dipecah jadi 2 baris kalau ada tanda " - " / " – ")
$orgFull = trim($ev['agency'] ?: 'Balai Monitor Spektrum Frekuensi Radio dan Infrastruktur Digital');
$orgLine1 = $orgFull; $orgLine2 = '';
foreach ([' – ', ' - '] as $sep) {
    if (strpos($orgFull, $sep) !== false) {
        [$orgLine1, $orgLine2] = array_map('trim', explode($sep, $orgFull, 2));
        break;
    }
}
?>
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><?= esc($ev['title']) ?> — Halaman Event</title>
<link rel="icon" type="image/png" href="logo-balmon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{
    --navy:#0d2f66; --navy-deep:#0a2452;
    --blue:#1f5fc4; --blue-soft:#e8f1fd; --blue-tint:#dce9fb;
    --ink:#0f2a52; --ink-soft:#5b6b83;
    --line:#e3eaf5;
    --card:#ffffff;
    --bg:#f4f8fd;
    font-family:'Plus Jakarta Sans', -apple-system, Segoe UI, Roboto, sans-serif;
  }
  *{ box-sizing:border-box; }
  body{ margin:0; background:var(--bg); color:var(--ink); line-height:1.6; }
  a{ font-family:inherit; }

  /* ---------- Header ---------- */
  .topbar{ background:var(--navy); padding:14px 24px; }
  .topbar-inner{ max-width:900px; margin:0 auto; display:flex; align-items:center; gap:14px; }
  .topbar .logo{ width:44px; height:44px; border-radius:50%; flex:none; }
  .topbar h1{ margin:0; font-size:16px; line-height:1.35; font-weight:700; color:#fff; }
  .topbar h1 span{ display:block; }

  /* ---------- Hero ---------- */
  .hero{ position:relative; overflow:hidden; background:linear-gradient(120deg,#eef4fc 0%,#dbe9fb 45%,#8db8ec 100%); padding:40px 24px 76px; }
  .hero-deco{ position:absolute; inset:0; pointer-events:none; }
  .hero-inner{ position:relative; max-width:900px; margin:0 auto; z-index:1; }
  .badge{ display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,.75); color:var(--blue); font-weight:700; font-size:13px; padding:8px 16px 8px 12px; border-radius:999px; margin-bottom:22px; }
  .badge svg{ width:16px; height:16px; }
  .hero h2{ margin:0; font-size:clamp(26px,4.2vw,38px); line-height:1.28; font-weight:800; color:var(--navy); max-width:640px; }

  /* ---------- Info bar (overlaps hero) ---------- */
  .infobar-wrap{ max-width:900px; margin:-46px auto 0; padding:0 24px; position:relative; z-index:2; }
  .infobar{ background:var(--card); border-radius:16px; box-shadow:0 12px 30px rgba(13,47,102,.12); display:flex; flex-wrap:wrap; }
  .info-item{ flex:1 1 220px; display:flex; align-items:center; gap:14px; padding:20px 24px; border-right:1px solid var(--line); }
  .info-item:last-child{ border-right:none; }
  .info-icon{ flex:none; width:42px; height:42px; border-radius:50%; background:var(--blue-tint); color:var(--blue); display:flex; align-items:center; justify-content:center; }
  .info-icon svg{ width:20px; height:20px; }
  .info-item .label{ margin:0 0 2px; font-size:12.5px; color:var(--ink-soft); }
  .info-item .value{ margin:0; font-size:15px; font-weight:700; color:var(--ink); }
  .info-item .value.small{ font-weight:500; font-size:13px; color:var(--ink-soft); margin-top:2px; }

  /* ---------- Main content ---------- */
  main{ max-width:900px; margin:0 auto; padding:36px 24px 20px; }
  .card{ background:var(--card); border-radius:16px; box-shadow:0 4px 16px rgba(13,47,102,.06); padding:26px 28px; margin-bottom:20px; }
  .card-head{ display:flex; align-items:flex-start; gap:16px; margin-bottom:18px; }
  .card-icon{ flex:none; width:44px; height:44px; border-radius:50%; background:var(--blue); color:#fff; display:flex; align-items:center; justify-content:center; }
  .card-icon svg{ width:21px; height:21px; }
  .card-head-text{ padding-top:6px; }
  .card-head-text h3{ margin:0 0 8px; font-size:19px; font-weight:700; color:var(--navy); }
  .card-head-text .rule{ width:30px; height:3px; background:var(--blue); border:none; border-radius:2px; margin:0; }
  .card-body{ padding-left:60px; }
  .desc{ font-size:15px; color:var(--ink); white-space:pre-line; margin:0; }
  .empty{ font-size:14px; color:var(--ink-soft); font-style:italic; padding:16px 18px; background:var(--blue-soft); border-radius:10px; margin:0; }

  /* Presensi */
  .presensi-box{ display:flex; gap:20px; align-items:center; background:var(--blue-soft); border-radius:14px; padding:18px; }
  .qr{ flex:0 0 auto; width:118px; height:118px; background:#fff; border-radius:10px; display:flex; align-items:center; justify-content:center; padding:8px; overflow:hidden; border:1px solid var(--line); }
  .qr img, .qr canvas, .qr table{ width:100% !important; height:100% !important; object-fit:contain; }
  .presensi-info{ min-width:0; }
  .presensi-link{ display:inline-flex; align-items:center; gap:6px; font-size:15px; font-weight:700; color:var(--blue); text-decoration:none; word-break:break-all; }
  .presensi-link svg{ width:15px; height:15px; flex:none; }
  .presensi-link:hover{ text-decoration:underline; }
  .presensi-info .hint{ margin:10px 0 0; font-size:13.5px; color:var(--ink-soft); }

  .presensi-closed{ display:flex; align-items:flex-start; gap:14px; background:#fdecea; border:1px solid #f6c9c2; border-radius:14px; padding:18px 20px; }
  .presensi-closed .closed-icon{ flex:none; width:34px; height:34px; border-radius:50%; background:#f4b6ad; color:#8f2c1f; display:flex; align-items:center; justify-content:center; }
  .presensi-closed .closed-icon svg{ width:18px; height:18px; }
  .presensi-closed p{ margin:6px 0 0; font-size:14.5px; color:#8f2c1f; line-height:1.55; }
  .presensi-closed p strong{ color:#7a2318; }

  /* Lists (Materi / Dokumentasi) */
  ul.list{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px; }
  ul.list li a{ display:flex; align-items:center; gap:12px; background:var(--blue-soft); border-radius:10px; padding:14px 16px; color:var(--navy); text-decoration:none; font-weight:600; font-size:14.5px; transition:background .15s; }
  ul.list li a:hover{ background:var(--blue-tint); }
  ul.list li a .file-ic{ flex:none; width:20px; height:20px; color:var(--blue); }
  ul.list li a .txt{ flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  ul.list li a .chev{ flex:none; width:18px; height:18px; color:var(--ink-soft); }

  footer.page-footer{ text-align:center; font-size:13px; color:var(--ink-soft); padding:26px 24px 46px; }
  footer.page-footer p{ margin:2px 0; }

  @media (max-width:640px){
    .card-body{ padding-left:0; margin-top:4px; }
    .info-item{ border-right:none; border-bottom:1px solid var(--line); }
    .info-item:last-child{ border-bottom:none; }
    .infobar{ flex-direction:column; }
    .presensi-box{ flex-direction:column; text-align:center; }
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <img src="logo-balmon.png" alt="Logo Balmon Jogja Istimewa" class="logo">
    <h1><span><?= esc($orgLine1) ?></span><?php if ($orgLine2): ?><span><?= esc($orgLine2) ?></span><?php endif; ?></h1>
  </div>
</div>

<div class="hero">
  <div class="hero-inner">
    <span class="badge">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5v12L3 14v-3z"></path><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"></path></svg>
      Sosialisasi
    </span>
    <h2><?= esc($ev['title']) ?></h2>
  </div>
</div>

<div class="infobar-wrap">
  <div class="infobar">
    <div class="info-item">
      <span class="info-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
      </span>
      <div>
        <p class="label">Tanggal</p>
        <p class="value"><?= $dateFormatted ? esc($dateFormatted) : '—' ?></p>
      </div>
    </div>
    <div class="info-item">
      <span class="info-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
      </span>
      <div>
        <p class="label">Waktu</p>
        <p class="value"><?= esc($ev['event_time'] ?: '—') ?></p>
      </div>
    </div>
    <div class="info-item">
      <span class="info-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
      </span>
      <div>
        <p class="label">Lokasi</p>
        <p class="value"><?= esc($ev['location'] ?: '—') ?></p>
      </div>
    </div>
  </div>
</div>

<main>

  <?php if (!empty($ev['description'])): ?>
  <section class="card">
    <div class="card-head">
      <span class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>
      </span>
      <div class="card-head-text">
        <h3>Tentang Kegiatan</h3>
        <hr class="rule">
      </div>
    </div>
    <div class="card-body">
      <p class="desc"><?= nl2br(esc($ev['description'])) ?></p>
    </div>
  </section>
  <?php endif; ?>

  <section class="card">
    <div class="card-head">
      <span class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="3" width="7" height="7" rx="1"></rect><rect x="14" y="14" width="7" height="7" rx="1"></rect><rect x="3" y="14" width="7" height="7" rx="1"></rect></svg>
      </span>
      <div class="card-head-text">
        <h3>Presensi</h3>
        <hr class="rule">
      </div>
    </div>
    <div class="card-body">
      <?php if ($isPastEvent): ?>
        <div class="presensi-closed">
          <span class="closed-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          </span>
          <p>Anda Sudah Tidak Bisa Melakukan Presensi Pada Kegiatan <strong><?= esc($ev['title']) ?></strong></p>
        </div>
      <?php elseif ($hasPresensiLink): ?>
        <div class="presensi-box">
          <div class="qr" id="qr">
            <?php if ($hasBarcodeImg): ?>
              <img src="uploads/<?= esc($ev['presensi_barcode']) ?>" alt="Barcode presensi">
            <?php endif; ?>
          </div>
          <div class="presensi-info">
            <a class="presensi-link" href="<?= esc($ev['presensi_link']) ?>" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
              <?= esc($ev['presensi_link']) ?>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
            <p class="hint">Scan barcode atau klik link untuk mengisi presensi kehadiran.</p>
          </div>
        </div>
      <?php else: ?>
        <p class="empty">Link presensi belum tersedia untuk event ini.</p>
      <?php endif; ?>
    </div>
  </section>

  <section class="card">
    <div class="card-head">
      <span class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>
      </span>
      <div class="card-head-text">
        <h3>Materi</h3>
        <hr class="rule">
      </div>
    </div>
    <div class="card-body">
      <?php if ($materials): ?>
        <ul class="list">
          <?php foreach ($materials as $mat): ?>
            <li><a href="<?= esc($mat['url']) ?>" target="_blank" rel="noopener">
              <svg class="file-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              <span class="txt"><?= esc($mat['title'] ?: $mat['url']) ?></span>
              <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </a></li>
          <?php endforeach; ?>
        </ul>
      <?php else: ?>
        <p class="empty">Materi untuk kegiatan ini belum tersedia. Silakan cek kembali menjelang hari pelaksanaan.</p>
      <?php endif; ?>
    </div>
  </section>

  <section class="card">
    <div class="card-head">
      <span class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
      </span>
      <div class="card-head-text">
        <h3>Dokumentasi</h3>
        <hr class="rule">
      </div>
    </div>
    <div class="card-body">
      <?php if ($docs): ?>
        <ul class="list">
          <?php foreach ($docs as $doc): ?>
            <li><a href="<?= esc($doc['url']) ?>" target="_blank" rel="noopener">
              <svg class="file-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              <span class="txt"><?= esc($doc['caption'] ?: $doc['url']) ?></span>
              <svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </a></li>
          <?php endforeach; ?>
        </ul>
      <?php else: ?>
        <p class="empty">Dokumentasi kegiatan akan ditampilkan di sini setelah acara berlangsung.</p>
      <?php endif; ?>
    </div>
  </section>

</main>

<footer class="page-footer">
  <p>Diselenggarakan oleh Balai Monitor Spektrum Frekuensi Radio dan Infrastruktur Digital –</p>
  <p><?= $ev['ministry'] ? ' &middot; ' . esc($ev['ministry']) : '' ?></p>
</footer>

<?php if (!$isPastEvent && $hasPresensiLink && !$hasBarcodeImg): ?>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
<script>
  try{
    new QRCode(document.getElementById("qr"), {
      text: <?= json_encode($ev['presensi_link']) ?>,
      width: 102, height: 102,
      colorDark: "#0d2f66", colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M
    });
  }catch(e){
    document.getElementById("qr").innerHTML = '<span style="font-size:11px;color:#999;">QR gagal dimuat</span>';
  }
</script>
<?php endif; ?>
</body>
</html>