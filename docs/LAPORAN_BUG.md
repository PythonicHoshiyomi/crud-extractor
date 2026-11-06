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