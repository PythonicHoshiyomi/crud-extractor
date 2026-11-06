# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Kolom tanpa qualifier tidak di-resolve

**Ditemukan oleh:** Arsel Fahri Khadafi · **Diperbaiki oleh:** Arsel Fahri Khadafi

**Gejala.**  
Kolom tanpa qualifier seperti `nama` pada query `SELECT nama FROM pelanggan`
tidak memiliki nilai `ColumnRef.resolved`. Akibatnya resolver tidak dapat menentukan
bahwa kolom tersebut berasal dari tabel `pelanggan`.

Menurut SPESIFIKASI.md bagian 4.3, jika hanya ada tepat satu tabel di scope terdalam,
kolom tanpa qualifier harus di-resolve ke tabel tersebut.

**Reproduksi minimal.**

```sql
SELECT nama FROM pelanggan;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Fungsi _column() belum memiliki implementasi untuk kolom tanpa qualifier.
Kode hanya menangani kolom yang memiliki qualifier, seperti p.nama, kemudian berhenti
pada pass. Akibatnya aturan resolusi untuk scope terdalam belum dijalankan.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pada fungsi _column() di crud/resolver.py, ditambahkan logika untuk:
- menghasilkan warning jika tidak ada tabel pada scope;
- mengisi col.resolved jika scope memiliki tepat satu tabel;
- menghasilkan warning jika terdapat lebih dari satu tabel karena kolom ambigu.

Alternatif yang ditolak adalah mencari kolom tanpa qualifier ke seluruh parent scope.
Dapat menyebabkan kolom pada scope dalam salah dikaitkan dengan tabel dari scope luar.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_regresi_resolver_kolom_tanpa_qualifier_satu_tabel

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu mengidentifikasi TODO(T2), menjelaskan aturan kolom tanpa qualifier,
dan menyarankan bentuk test regresi.

---


---

## Bug 2 — Lookup scope tidak memprioritaskan scope terdalam

```markdown
## Bug 2: Lookup alias mencari scope luar lebih dahulu

**Ditemukan oleh:** [Nama anggota] · **Diperbaiki oleh:** [Nama anggota]

**Gejala.**  
Ketika scope dalam dan scope luar memiliki alias yang sama, alias pada scope dalam
seharusnya menutupi alias pada scope luar. Namun implementasi `_lookup()` sebelumnya
mencari scope luar lebih dahulu.

**Reproduksi minimal.**

```sql
SELECT p.id
FROM pelanggan p
WHERE p.id IN (
    SELECT p.id
    FROM pesanan p
);
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Fungsi _lookup() membangun rantai scope dari scope sekarang ke parent, tetapi kemudian menggunakan urutan terbalik saat melakukan pencarian. Akibatnya environment luar diperiksa sebelum environment dalam.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Fungsi _lookup() diubah agar memeriksa self.scope terlebih dahulu, kemudian berpindah
ke scope.parent secara berurutan. Dengan demikian alias dalam melakukan shadowing terhadap alias luar, tetapi alias yang tidak ditemukan di scope dalam tetap dapat dicari pada scope luar untuk mendukung correlated subquery.

Alternatif yang ditolak adalah menghapus akses ke parent scope. Alternatif tersebut memang
dapat mencegah shadowing yang salah, tetapi juga akan merusak correlated subquery

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_regresi_resolver_lookup_scope_terdalam

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menemukan hubungan antara urutan pencarian scope, shadowing, dan correlated
subquery.

---


---

## Bug 3 — Scope `DELETE` bocor ke statement berikutnya

```markdown
## Bug 3: Scope DELETE tidak dibersihkan

**Ditemukan oleh:** [Nama anggota] · **Diperbaiki oleh:** [Nama anggota]

**Gejala.**  
Alias yang dideklarasikan pada statement `DELETE` masih dapat terlihat ketika resolver
memproses statement berikutnya. Hal ini melanggar aturan bahwa setiap statement harus
berdiri sendiri.

**Reproduksi minimal.**

```sql
DELETE FROM sesi s;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Fungsi _delete() memanggil _push() untuk membuat scope baru, tetapi tidak memanggil
_pop() setelah proses resolusi selesai. Akibatnya scope DELETE tetap tersimpan pada
resolver dan dapat memengaruhi statement berikutnya.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Ditambahkan pemanggilan _pop() pada akhir _delete() setelah tabel target dan kondisi
WHERE selesai di-resolve.
Alternatif yang ditolak adalah mengosongkan self.scope secara langsung dengan assignment
seperti self.scope = None. Cara tersebut tidak dipilih karena dapat merusak parent scope.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_regresi_resolver_scope_delete_tidak_bocor

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menemukan hubungan antara urutan pencarian scope, shadowing, dan correlated
subquery.

---

---

## Bug 4: Subquery dalam UPDATE salah dianggap sebagai operasi U

**Ditemukan oleh:** [Nama anggota] · **Diperbaiki oleh:** [Nama anggota]

**Gejala.**  
Tabel yang hanya dibaca melalui subquery pada statement `UPDATE` dilaporkan sebagai tabel
yang mengalami operasi `U`. Menurut SPESIFIKASI.md bagian 5, tabel target `UPDATE` mendapat
operasi `U`, sedangkan semua tabel yang digunakan oleh subquery mendapat operasi `R`.

**Reproduksi minimal.**

```sql
UPDATE pelanggan
SET level = (
    SELECT level_baru
    FROM level_pelanggan
)
WHERE id IN (
    SELECT pelanggan_id
    FROM pesanan
);
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Pada fungsi analyze_statement() di crud/analyzer.py, ekspresi assignment dan
WHERE pada UPDATE dikirim ke _collect() dengan operasi "U". Parameter tersebut
diteruskan ke subquery, sehingga tabel sumber subquery ikut dianggap di-update.

Berdasarkan aturan CRUD lokal pada SPESIFIKASI.md bagian 5, operasi U hanya
berlaku untuk tabel target UPDATE. Subquery tetap merupakan operasi pembacaan dan harus
menghasilkan R.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Operasi yang diteruskan untuk assignment.value dan stmt.where diubah dari "U" menjadi
"R"

Alternatif yang ditolak adalah mengubah _collect() agar selalu mengubah operasi menjadi
"R" ketika menemukan subquery. Alternatif tersebut tidak dipilih karena _collect() juga
digunakan untuk SELECT, INSERT, dan DELETE

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
test_regresi_analyzer_subquery_update_selalu_read

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
Konfirmasi kesalahannya pada kesesuain spesifikasi.md

---

## Bug 5: Quote ter-escape mengakhiri literal terlalu awal

**Ditemukan oleh:** Giza Jirndhara· **Diperbaiki oleh:** Giza Jirndhara  

**Gejala.**  
Parser gagal membaca string yang berisi quote ter-escape, seperti `'It\'s a test'`.
Identifier yang dibungkus quote ganda dan berisi quote ter-escape, seperti
`"Column \"Name\""`, juga tidak dapat diproses.

**Reproduksi minimal.**

```sql
SELECT 'It\'s a test', "Column \"Name\"" FROM test_table;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Scanner pada `crud/lexer.py` menganggap setiap `'` sebagai akhir string tanpa
memeriksa apakah karakter tersebut di-escape. Scanner juga belum memiliki aturan
untuk identifier berpetik ganda. Dalam konsep scanner pada Crafting Interpreters
Bab 4, lexer perlu mengenali konteks karakter saat memindai token agar delimiter
yang merupakan bagian dari isi token tidak dianggap sebagai penutup.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Fungsi `_string()` di `crud/lexer.py` sekarang melewati karakter yang di-escape
dan mendukung quote tunggal ganda (`''`). Ditambahkan `_quoted_identifier()` untuk
membaca identifier dengan quote ganda, termasuk quote yang di-escape atau digandakan.
Penanganan dilakukan di lexer karena lexer yang menentukan batas token; memperbaikinya
di parser berarti parser sudah menerima token yang terpotong atau salah jenis.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
`test_escape_character_in_string_literal`

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menemukan bahwa quote dianggap sebagai delimiter tanpa penanganan escape,
kemudian membantu memperbaiki scanner. Perbaikan diverifikasi dengan menjalankan suite
pytest.

---

## Bug 6: Operator `<>` tidak dikenali lexer

**Ditemukan oleh:** Giza Jirndhara · **Diperbaiki oleh:** Giz Jirndharaa

**Gejala.**  
Kondisi SQL yang menggunakan `<>` sebagai operator tidak sama gagal diparse.

**Reproduksi minimal.**

```sql
SELECT id FROM test_table WHERE status <> 'rahasia';
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Lexer hanya mengenali `<` dan `<=`, sehingga `<>` dipotong menjadi token `<`
dan `>`. Ini merupakan kekurangan pada pemindaian operator multi-karakter (Crafting
Interpreters Bab 4): lexer perlu memeriksa karakter berikutnya untuk mengenali
operator terpanjang yang valid.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Pemindaian `<` di `crud/lexer.py` diperbarui agar mengenali `<=`, `<>`, dan `<`
sebagai token yang berbeda. `<>` dipertahankan sebagai operator tersendiri, bukan
diubah menjadi `!=`, supaya ejaan operator dari input SQL tetap tercermin pada token.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
`test_matrix_laporan_penjualan` di `tests/test_analyzer.py` menjalankan query contoh
yang memakai `<>`.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI menemukan kekurangan ini saat menjalankan suite setelah perbaikan lexer, lalu
memperbaikinya. Suite diverifikasi kembali menggunakan pytest.

---

## Bug 7: `AND` dan `OR` memiliki presedensi yang sama

**Ditemukan oleh:** Giza Jirndhara · **Diperbaiki oleh:** Giz Jirndharaa

**Gejala.**  
Ekspresi `a = 1 OR b = 2 AND c = 3` sebelumnya diparse dari kiri ke kanan,
sehingga struktur AST-nya tidak mengikuti aturan bahwa `AND` memiliki presedensi
lebih tinggi daripada `OR`.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Fungsi `_logical()` memproses `AND` dan `OR` dalam satu loop dan pada tingkat
grammar yang sama. Ini mengabaikan aturan presedensi operator pada recursive-descent
parser (Crafting Interpreters Bab 6) dan grammar proyek di `SPESIFIKASI.md`, yang
menempatkan `AND` lebih tinggi daripada `OR`.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
Parsing logika di `crud/parser.py` dipisah menjadi `_or()` dan `_and()`.
`_or()` mengurai operand melalui `_and()`, sehingga semua rangkaian `AND` membentuk
subekspresi sebelum `OR` digabungkan. Tetap memakai satu loop untuk kedua operator
tidak dipilih karena tidak dapat menyatakan tingkatan presedensi yang berbeda.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
`test_precedensi_and_di_atas_or` di `tests/test_parser.py` memeriksa bentuk AST,
dan `test_precedency_of_operators` di `tests/test_tambahan.py` juga memeriksa
pengelompokan operator.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu mencocokkan implementasi parser dengan presedensi yang tertulis di
spesifikasi, menerapkan pemisahan aturan grammar, dan menambahkan test AST.
Suite diverifikasi menggunakan pytest; 37 test lulus.

---