# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Arsel | Meminta analisis aturan resolver dan pembagian scope berdasarkan SPESIFIKASI.md. | Diterima sebagai panduan analisis. | Saran AI membantu memetakan TODO(T2), `_lookup()`, dan `_delete()` terhadap aturan scope. | Membaca ulang `crud/resolver.py` dan mencocokkan setiap saran dengan SPESIFIKASI.md. |
| 2 | Arsel | Meminta rancangan test regresi untuk resolver. | Diterima dengan perubahan pada nama test dan detail assertion. | Test harus mengikuti struktur AST dan diagnostic yang benar-benar digunakan proyek. | Menjalankan test sebelum dan sesudah perbaikan menggunakan pytest. |
| 3 | Giza | Meminta analisis aturan parser & lexer | Diterima | Saran AI membantu memetakan TODO(T2&T3) | Membaca ulang `lexer.py` dan `parser.py` |
| 4 | Giza | Meminta perbaikan test `test_escape_character_in_string_literal`. | Diterima | Lexer sebelumnya menganggap quote yang di-escape sebagai penutup literal; pengecekan juga menemukan operator `<>` belum didukung. | Menjalankan `python -m pytest -q`; 36 test lulus. |
| 5 | Giza | Meminta penambahan presedensi pada operator `AND`/`OR`. | Diterima | `AND` harus memiliki presedensi lebih tinggi daripada `OR`, sesuai grammar di SPESIFIKASI.md. | Menjalankan `python -m pytest -q`; 37 test lulus. |
| 6 | Giza | Meminta membuatkan pesan commit | Diterima | Pembuatan pesan lebih efisien dan jelas | Membaca ulang pesan commit | 


**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
