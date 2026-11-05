# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Arsel | Meminta analisis aturan resolver dan pembagian scope berdasarkan SPESIFIKASI.md. | Diterima sebagai panduan analisis. | Saran AI membantu memetakan TODO(T2), `_lookup()`, dan `_delete()` terhadap aturan scope. | Membaca ulang `crud/resolver.py` dan mencocokkan setiap saran dengan SPESIFIKASI.md. |
| 2 | Arsel | Meminta rancangan test regresi untuk resolver. | Diterima dengan perubahan pada nama test dan detail assertion. | Test harus mengikuti struktur AST dan diagnostic yang benar-benar digunakan proyek. | Menjalankan test sebelum dan sesudah perbaikan menggunakan pytest. |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
