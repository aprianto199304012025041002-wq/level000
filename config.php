<?php
// ============================================================
// KONFIGURASI — WAJIB DIISI SEBELUM DIPAKAI
// ============================================================

session_start();

// --- Detail database MySQL kamu (lihat di hPanel > Databases > MySQL Databases) ---
define('DB_HOST', 'localhost');
define('DB_NAME', 'u781960094_event');
define('DB_USER', 'u781960094_event');
define('DB_PASS', 'Event26.');

// --- Password untuk login ke dashboard admin ini (WAJIB DIGANTI!) ---
define('ADMIN_PASSWORD', 'Balmon-Event!2026Xq');

// ============================================================
// Tidak perlu diubah di bawah ini
// ============================================================

function get_db(){
    static $pdo = null;
    if($pdo === null){
        try{
            $pdo = new PDO(
                'mysql:host='.DB_HOST.';dbname='.DB_NAME.';charset=utf8mb4',
                DB_USER, DB_PASS,
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                ]
            );
        } catch(PDOException $e){
            http_response_code(500);
            header('Content-Type: application/json');
            echo json_encode(['error' => 'Koneksi database gagal. Cek DB_HOST/DB_NAME/DB_USER/DB_PASS di config.php.']);
            exit;
        }
    }
    return $pdo;
}

function require_login(){
    if(empty($_SESSION['admin_logged_in'])){
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'unauthorized']);
        exit;
    }
}
