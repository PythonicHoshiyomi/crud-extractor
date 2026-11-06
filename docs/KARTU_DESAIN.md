# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | Kolom tanpa qualifier hanya diperiksa pada scope terdalam. Jika hanya ada satu tabel, kolom di-resolve; jika lebih dari satu tabel, dibuat warning ambigu. | Mencari kolom tanpa qualifier ke seluruh parent scope atau memilih tabel pertama secara otomatis. | Aturan ini sesuai SPESIFIKASI.md bagian 4.3 dan mencegah resolver membuat asumsi yang tidak dapat dibuktikan dari SQL. |
| 2 | Keyword dikenali tanpa membedakan huruf besar dan kecil, lalu nilai token keyword dinormalisasi menjadi huruf besar. | Membuat keyword hanya valid dalam satu bentuk kapitalisasi atau mempertahankan kapitalisasi input untuk diproses parser. | SQL menerima variasi kapitalisasi keyword; normalisasi membuat pengecekan keyword di parser konsisten tanpa mengubah kapitalisasi identifier. |
| 3 | Komentar blok `/* ... */` dipindai sebagai komentar oleh lexer sampai delimiter penutup ditemukan; komentar yang tidak ditutup menghasilkan `LexError`. | Menghapus komentar lewat penggantian teks sebelum tokenisasi atau mengabaikan komentar yang tidak ditutup. | Penanganan di lexer memakai state dan posisi sumber yang sama dengan pemindaian token lainnya, serta melaporkan komentar tidak valid secara eksplisit. |
| 4 | `INSERT ... SELECT` memakai parser `_select()` yang sudah ada dan menyimpan query pada field `ast.Insert.query`. | Membuat parser query terpisah atau mengubah query SELECT menjadi daftar `VALUES`. | Memakai ulang grammar dan node SELECT menjaga struktur query, menghindari duplikasi parser, dan memisahkan sumber nilai SELECT dari daftar VALUES. |
| 5 | Analyzer hanya memberikan operasi mutasi kepada tabel target statement. Tabel yang muncul sebagai sumber atau di dalam subquery selalu diberi operasi `R`, termasuk subquery pada `SET` dan `WHERE` dalam `UPDATE`. | Meneruskan operasi statement luar ke seluruh ekspresi dan subquery, sehingga tabel sumber pada subquery `UPDATE` ikut dianggap mengalami operasi `U`. | Aturan CRUD membedakan tabel target dan tabel yang hanya dibaca. Pendekatan ini mencegah tabel sumber salah dikategorikan sebagai tabel yang diubah dan menjaga hasil CRUD tetap sesuai struktur AST serta spesifikasi. |