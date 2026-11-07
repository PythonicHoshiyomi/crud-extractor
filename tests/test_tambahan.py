"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

from crud import ast_nodes as ast
from crud.parser import parse_sql
from crud.resolver import Resolver
from crud.analyzer import analyze_statement

def one(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    assert len(script.statements) == 1
    return script.statements[0]

# ============================================================
# Test regresi resolver
# ============================================================

def test_regresi_resolver_kolom_tanpa_qualifier_satu_tabel():
    # Sebelum perbaikan TODO(T2), kolom nama tidak di-resolve.
    script = parse_sql("SELECT nama FROM pelanggan;")
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)

    columns = [
        node
        for node in ast.iter_nodes(script)
        if isinstance(node, ast.ColumnRef)
    ]

    assert len(columns) == 1
    assert columns[0].resolved == "pelanggan"
    assert diagnostics == []


def test_regresi_resolver_lookup_scope_terdalam():
    # Alias p di subquery harus menutupi alias p dari scope luar.
    script = parse_sql(
        """
        SELECT p.id
        FROM pelanggan p
        WHERE p.id IN (
            SELECT p.id
            FROM pesanan p
        );
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)

    columns = [
        node
        for node in ast.iter_nodes(script)
        if isinstance(node, ast.ColumnRef)
    ]

    assert diagnostics == []
    assert len(columns) == 3

    # p.id pada SELECT luar dan WHERE luar mengarah ke pelanggan.
    assert columns[0].resolved == "pelanggan"
    assert columns[1].resolved == "pelanggan"

    # p.id pada SELECT dalam mengarah ke pesanan.
    assert columns[2].resolved == "pesanan"


def test_regresi_resolver_scope_delete_tidak_bocor():
    # Alias s dari DELETE tidak boleh terlihat pada statement berikutnya.
    script = parse_sql(
        """
        DELETE FROM sesi s;
        SELECT s.id FROM pengguna u;
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)

    assert len(diagnostics) == 1
    assert diagnostics[0].level == "error"
    assert diagnostics[0].line == 3
    assert "alias 's' tidak terdefinisi" in diagnostics[0].message


# ============================================================
# Test kasus tepi resolver
# ============================================================

def test_tepi_resolver_correlated_subquery():
    # Subquery memiliki scope sendiri, tetapi boleh membaca alias
    # yang berasal dari scope SELECT di luarnya.
    script = parse_sql(
        """
        SELECT p.nama
        FROM pelanggan p
        WHERE EXISTS (
            SELECT 1
            FROM pesanan o
            WHERE o.pelanggan_id = p.id
        );
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)

    columns = [
        node
        for node in ast.iter_nodes(script)
        if isinstance(node, ast.ColumnRef)
    ]

    resolved = {
        (column.qualifier, column.name): column.resolved
        for column in columns
    }

    assert diagnostics == []
    assert resolved[("p", "nama")] == "pelanggan"
    assert resolved[("o", "pelanggan_id")] == "pesanan"
    assert resolved[("p", "id")] == "pelanggan"
    
# ============================================================
# Test regresi analyzer
# ============================================================
    
def test_regresi_analyzer_subquery_update_selalu_read():
    script = parse_sql(
        """
        UPDATE pelanggan
        SET level = (
            SELECT level_baru
            FROM level_pelanggan
        )
        WHERE id IN (
            SELECT pelanggan_id
            FROM pesanan
        );
        """
    )
    assert script.errors == []

    result = analyze_statement(script.statements[0])

    assert result == {
        "pelanggan": {"U"},
        "level_pelanggan": {"R"},
        "pesanan": {"R"},
    }

# ============================================================
# Test regresi lexer dan parser
# ============================================================

def test_regresi_lexer_escape_character_dalam_literal():
    # Pastikan karakter escape di dalam string literal tidak memengaruhi parsing.
    script = parse_sql(
        r"""
        SELECT 'It\'s a test', "Column \"Name\""
        FROM test_table;
        """
    )
    assert script.errors == []
    select = script.statements[0]
    assert select.columns[0].expr.value == "It's a test"
    assert isinstance(select.columns[1].expr, ast.ColumnRef)
    assert select.columns[1].expr.name == 'column "name"'

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []


def test_regresi_lexer_operator_tidak_sama_dengan():
    # Operator <> harus menjadi satu operator perbandingan, bukan token < dan >.
    s = one("SELECT id FROM t WHERE status <> 'rahasia'")
    assert isinstance(s.where, ast.BinaryOp)
    assert s.where.op == "<>"


def test_regresi_parser_error_recovery_sampai_semicolon():
    # Pastikan parser dapat melanjutkan parsing setelah menemukan token yang tidak valid.
    script = parse_sql(
        """
        SELECT id, nama FROM pelanggan;
        INSERT INTO log (id, pesan) VALUES (1, 'ok');
        INVALID TOKEN HERE;
        UPDATE produk SET stok = stok - 1 WHERE id = 3;
        """
    )
    assert len(script.errors) == 1  # Hanya satu error untuk token yang tidak valid.
    assert len(script.statements) == 3
    assert isinstance(script.statements[-1], ast.Update)

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []  # Resolver harus tetap bekerja pada statement yang valid.


def test_regresi_parser_and_memiliki_presedensi_lebih_tinggi_dari_or():
    s = one("SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3")
    where = s.where

    assert isinstance(where, ast.BinaryOp) and where.op == "OR"
    assert isinstance(where.left, ast.BinaryOp) and where.left.op == "="
    assert isinstance(where.right, ast.BinaryOp) and where.right.op == "AND"
    assert isinstance(where.right.left, ast.BinaryOp) and where.right.left.op == "="
    assert isinstance(where.right.right, ast.BinaryOp) and where.right.right.op == "="


def test_regresi_parser_left_outer_join():
    s = one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert s.joins[0].kind == "LEFT"
    assert s.joins[0].source.name == "b"
    assert isinstance(s.joins[0].condition, ast.BinaryOp)
    assert s.joins[0].condition.op == "="


# ============================================================
# Test kasus tepi
# ============================================================

def test_tepi_resolver_kolom_tanpa_qualifier_ambigu():
    # Dua tabel membuat kolom tanpa qualifier ambigu; resolver tidak boleh memilih sembarang tabel.
    script = parse_sql("SELECT id FROM pelanggan, pesanan;")
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    column = script.statements[0].columns[0].expr

    assert isinstance(column, ast.ColumnRef)
    assert column.resolved is None
    assert len(diagnostics) == 1
    assert diagnostics[0].level == "warning"
    assert "ambigu tanpa skema" in diagnostics[0].message


def test_tepi_lexer_string_dengan_quote_ganda():
    # Quote tunggal ganda di dalam string SQL harus menjadi satu quote pada nilainya.
    s = one("SELECT 'O''Brien' FROM pelanggan")
    assert s.columns[0].expr.value == "O'Brien"


def test_tepi_lexer_semicolon_di_dalam_string():
    # Titik koma di dalam string tidak boleh mengakhiri statement lebih awal.
    script = parse_sql("SELECT 'nilai;lanjut' FROM a; SELECT id FROM b;")
    assert script.errors == []
    assert len(script.statements) == 2
    assert script.statements[0].columns[0].expr.value == "nilai;lanjut"
    assert script.statements[1].sources[0].name == "b"


def test_tepi_resolver_referensi_tabel_kiri_di_on_left_join():
    # Kondisi ON dapat memakai kolom dari sumber utama maupun sumber LEFT JOIN.
    script = parse_sql(
        "SELECT a.id FROM a LEFT JOIN b ON b.a_id = a.id;"
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    condition = script.statements[0].joins[0].condition

    assert diagnostics == []
    assert isinstance(condition, ast.BinaryOp)
    assert isinstance(condition.left, ast.ColumnRef)
    assert isinstance(condition.right, ast.ColumnRef)
    assert condition.left.resolved == "b"
    assert condition.right.resolved == "a"