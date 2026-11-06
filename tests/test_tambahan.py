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

def test_escape_character_in_string_literal():
    # Pastikan karakter escape di dalam string literal tidak memengaruhi parsing.
    script = parse_sql(
        r"""
        SELECT 'It\'s a test', "Column \"Name\""
        FROM test_table;
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []

def test_precedency_of_operators():
    # Pastikan operator AND memiliki precedensi lebih tinggi daripada OR.
    script = parse_sql(
        """
        SELECT id
        FROM t
        WHERE a = 1 OR b = 2 AND c = 3;
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []

    where_clause = script.statements[0].where
    assert isinstance(where_clause, ast.BinaryOp) and where_clause.op == "OR"
    assert isinstance(where_clause.right, ast.BinaryOp) and where_clause.right.op == "AND"

def test_left_join_outer_reference():
    # Pastikan kolom dari tabel luar dapat diakses di ON clause dari LEFT JOIN.
    script = parse_sql(
        """
        SELECT a.id
        FROM a
        LEFT JOIN b ON b.a_id = a.id;
        """
    )
    assert script.errors == []

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []

    join_condition = script.statements[0].joins[0].condition
    assert isinstance(join_condition, ast.BinaryOp) and join_condition.op == "="

def test_error_recovery_after_invalid_token():
    # Pastikan parser dapat melanjutkan parsing setelah menemukan token yang tidak valid.
    script = parse_sql(
        """
        SELECT id, nama FROM pelanggan;
        INSERT INTO log (id, pesan) VALUES (1, 'ok');
        INVALID TOKEN HERE
        UPDATE produk SET stok = stok - 1 WHERE id = 3;
        """
    )
    assert len(script.errors) == 1  # Hanya satu error untuk token yang tidak valid.

    diagnostics = Resolver().resolve_script(script)
    assert diagnostics == []  # Resolver harus tetap bekerja pada statement yang valid.