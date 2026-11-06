# Laporan Akhir

## 1. Hasil evaluasi

Evaluasi dilakukan dengan menjalankan `py evaluate.py` setelah
`ground_truth.csv` dilengkapi secara manual. Evaluator membandingkan
triple `(file, baris, tabel, operasi)`.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72
```

Parser memiliki precision, recall, dan F1 sebesar 1.00. Artinya seluruh
label pada ground truth ditemukan dengan benar dan tidak ada hasil parser yang
keliru. Regex memiliki hasil lebih rendah karena baseline regex tidak memahami
struktur AST, komentar, subquery, alias, dan aturan scope. FP/FN pada bagian
`[regex]` merupakan bukti keterbatasan baseline pembanding.

## 2. Tiga kasus di mana regex salah

### Kasus 1 — Regex membaca perintah di dalam komentar

SQL:

```sql
-- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
SELECT p.nama, SUM(o.total) AS omzet
FROM pelanggan p
JOIN pesanan o ON o.pelanggan_id = p.id;
```

Regex menghasilkan false positive untuk `pelanggan` dengan operasi `D` pada
baris komentar. Parser tidak menghasilkan label tersebut karena lexer
menghapus komentar satu baris sebelum parsing. Ini menunjukkan pentingnya
lexing: teks yang tampak seperti keyword SQL tidak boleh dianggap statement
jika berada di dalam komentar.

### Kasus 2 — Regex salah membaca kata di dalam string

SQL:

```sql
WHERE o.catatan <> 'FROM rahasia'
```

Regex dapat menganggap `FROM` dan kata `rahasia` sebagai bagian dari struktur
SQL sehingga menghasilkan tabel atau operasi yang tidak ada. Parser benar
karena lexer membaca `'FROM rahasia'` sebagai satu token `STRING`, sehingga
isinya tidak dipakai sebagai nama tabel. Ini adalah perbedaan antara
tokenisasi berdasarkan konteks dan pencarian pola teks biasa.

### Kasus 3 — Regex tidak memahami subquery dan tabel sumber

SQL:

```sql
INSERT INTO arsip_pesanan (id, total)
SELECT id, total FROM pesanan WHERE tanggal < :batas;
```

Parser menghasilkan `arsip_pesanan -> C` dan `pesanan -> R`. Regex dapat
melewatkan tabel sumber `pesanan` atau salah mengaitkan operasi karena hanya
mencari keyword dan nama tabel secara lokal. Parser membedakan statement
`INSERT`, membangun AST untuk `SELECT`, lalu analyzer menerapkan aturan CRUD
bahwa target INSERT mendapat `C` dan tabel sumber SELECT mendapat `R`.

## 3. Batas pendekatan kami

### 1. Tidak mendukung CTE dan UNION

Contoh:

```sql
WITH aktif AS (SELECT id FROM pelanggan)
SELECT id FROM aktif
UNION
SELECT id FROM arsip_pelanggan;
```

Grammar saat ini tidak mencakup `WITH` dan `UNION`. Statement dapat gagal
diparse atau tabel sumber tidak tercatat lengkap pada CRUD matrix. Dukungan
yang benar membutuhkan perluasan grammar, AST, resolver scope CTE, dan aturan
CRUD untuk setiap bagian query.

### 2. Tidak memiliki informasi schema database

Contoh:

```sql
SELECT id FROM pelanggan;
```

Tool dapat menyimpulkan bahwa tabel `pelanggan` dibaca, tetapi tidak dapat
memastikan apakah kolom `id` benar-benar ada, apakah tipe datanya cocok, atau
apakah nama tersebut adalah synonym/view. Untuk validasi tersebut dibutuhkan
metadata database seperti daftar tabel, kolom, tipe data, schema, view, dan
relasi.


### 3. Fitur SQL di luar lingkup belum didukung

Quoted identifier, `MERGE`, DDL, window function, `t.*`, dan alias kolom di
`ORDER BY` berada di luar lingkup spesifikasi. Jika digunakan, query dapat
ditolak parser atau hasil CRUD tidak lengkap. Penanganannya memerlukan
perluasan lexer, grammar, AST, resolver, dan test untuk setiap fitur.

## 4. Pembagian kerja

### Arsel Fahri Khadafi (251524002)

Mengerjakan TODO resolver untuk kolom tanpa qualifier serta memperbaiki pencarian scope terdalam dan kebocoran scope `DELETE`. Memperbaiki aturan analyzer agar
subquery pada `UPDATE` dianggap sebagai operasi `R`, menambahkan test regresi,
dan melengkapi laporan bug. Menambahkan test regresi dan edge case
lainnya pada `tests/test_tambahan.py`, serta melengkapi label manual untuk
`audit.sql` dan `pemeliharaan.sql` pada `data/ground_truth.csv`.

### Giza Jirndhara (251524010)

Mengerjakan dukungan komentar blok, keyword huruf kecil, dan `INSERT ... SELECT`.
Memperbaiki escaped quote pada lexer dan presedensi operator logika
`AND`/`OR`, sekaligus menambahkan test dan dokumentasi bug. Memperbaiki error recovery parser agar berhenti di `;` dan menambahkan test untuk `LEFT OUTER JOIN` dan test tambahan lainnya pada `tests/test_tambahan.py`.