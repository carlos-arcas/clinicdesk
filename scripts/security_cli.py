from __future__ import annotations

import argparse
import os
import secrets
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.application.auditoria.audit_service import AuditService
from clinicdesk.app.infrastructure.sqlite.db import bootstrap
from clinicdesk.app.infrastructure.sqlite.repos_auditoria_eventos import RepositorioAuditoriaEventosSqlite

from clinicdesk.app.common.crypto_field_protection import decrypt, encrypt, hash_lookup

CAMPOS_PII = ("documento", "telefono", "email", "direccion")
_ENV_KEY = "CLINICDESK_CRYPTO_KEY"
_ENV_KEY_PREVIOUS = "CLINICDESK_CRYPTO_KEY_PREVIOUS"


@dataclass(frozen=True)
class ResultadoRotacion:
    filas_leidas: int
    filas_actualizadas: int
    campos_recifrados: int


class ErrorSeguridadCLI(RuntimeError):
    pass


def generar_clave_segura() -> int:
    clave = secrets.token_urlsafe(48)
    sys.stderr.write("ADVERTENCIA: no pegues esta clave en repositorios ni logs.\n")
    sys.stdout.write(f"{clave}\n")
    return 0


def validar_clave_activa() -> int:
    clave = os.getenv(_ENV_KEY, "")
    if not _es_clave_valida(clave):
        sys.stderr.write("ERROR: CLINICDESK_CRYPTO_KEY ausente o con fortaleza insuficiente.\n")
        return 1
    sys.stdout.write("OK: CLINICDESK_CRYPTO_KEY válida.\n")
    return 0


def ejecutar_rotacion(args: argparse.Namespace) -> int:
    db_path = Path(args.db_path)
    schema_path = Path(args.schema_path)
    con = bootstrap(db_path, schema_path, apply=True)
    try:
        if args.dry_run:
            resultado = rotar_claves(con, dry_run=True, batch_size=args.batch_size, sample_size=args.sample_size)
            sys.stdout.write(
                f"DRY-RUN OK: filas_leidas={resultado.filas_leidas} "
                f"filas_actualizadas={resultado.filas_actualizadas} "
                f"campos_recifrados={resultado.campos_recifrados}\n"
            )
            return 0
        if args.apply:
            resultado = rotar_claves(con, dry_run=False, batch_size=args.batch_size, sample_size=args.sample_size)
            sys.stdout.write(
                f"APPLY OK: filas_leidas={resultado.filas_leidas} "
                f"filas_actualizadas={resultado.filas_actualizadas} "
                f"campos_recifrados={resultado.campos_recifrados}\n"
            )
            return 0
        raise ErrorSeguridadCLI("Debes indicar --dry-run o --apply")
    except ErrorSeguridadCLI as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    finally:
        con.close()


def rotar_claves(
    con: sqlite3.Connection,
    *,
    dry_run: bool,
    batch_size: int,
    sample_size: int,
) -> ResultadoRotacion:
    _validar_entorno_rotacion()
    _validar_columnas_pii(con)

    total_leidas = 0
    total_actualizadas = 0
    total_campos = 0

    if dry_run:
        filas = _leer_filas_pii(con, limite=max(sample_size, 1), offset=0)
        total_leidas = len(filas)
        for fila in filas:
            total_campos += _contar_campos_descifrables(fila)
        return ResultadoRotacion(filas_leidas=total_leidas, filas_actualizadas=0, campos_recifrados=total_campos)

    offset = 0
    while True:
        filas = _leer_filas_pii(con, limite=batch_size, offset=offset)
        if not filas:
            break
        total_leidas += len(filas)
        con.execute("BEGIN")
        try:
            for fila in filas:
                updates, campos_recifrados = _build_updates_recifrado(fila)
                total_campos += campos_recifrados
                if not updates:
                    continue
                total_actualizadas += 1
                asignaciones = ", ".join(f"{k} = ?" for k in updates)
                parametros = [updates[k] for k in updates]
                parametros.append(fila["id"])
                con.execute(f"UPDATE pacientes SET {asignaciones} WHERE id = ?", parametros)
            con.commit()
        except Exception:
            con.rollback()
            raise
        offset += len(filas)

    _auditar_rotacion(con, filas_leidas=total_leidas, filas_actualizadas=total_actualizadas, campos_recifrados=total_campos)
    return ResultadoRotacion(
        filas_leidas=total_leidas,
        filas_actualizadas=total_actualizadas,
        campos_recifrados=total_campos,
    )


def _build_updates_recifrado(fila: sqlite3.Row) -> tuple[dict[str, str], int]:
    updates: dict[str, str] = {}
    campos_recifrados = 0
    for campo in CAMPOS_PII:
        enc = fila[f"{campo}_enc"]
        if not enc:
            continue
        claro = decrypt(enc)
        nuevo_enc = encrypt(claro)
        nuevo_hash = hash_lookup(claro)
        updates[f"{campo}_enc"] = nuevo_enc
        updates[f"{campo}_hash"] = nuevo_hash
        campos_recifrados += 1
    return updates, campos_recifrados


def _contar_campos_descifrables(fila: sqlite3.Row) -> int:
    contados = 0
    for campo in CAMPOS_PII:
        enc = fila[f"{campo}_enc"]
        if not enc:
            continue
        decrypt(enc)
        contados += 1
    return contados


def _leer_filas_pii(con: sqlite3.Connection, *, limite: int, offset: int) -> list[sqlite3.Row]:
    where = " OR ".join(f"{campo}_enc IS NOT NULL" for campo in CAMPOS_PII)
    return con.execute(
        f"""
        SELECT id, documento_enc, telefono_enc, email_enc, direccion_enc
        FROM pacientes
        WHERE {where}
        ORDER BY id ASC
        LIMIT ? OFFSET ?
        """,
        (limite, offset),
    ).fetchall()


def _validar_columnas_pii(con: sqlite3.Connection) -> None:
    columnas = {row["name"] for row in con.execute("PRAGMA table_info(pacientes)").fetchall()}
    faltantes = [f"{campo}_enc" for campo in CAMPOS_PII if f"{campo}_enc" not in columnas]
    faltantes.extend(f"{campo}_hash" for campo in CAMPOS_PII if f"{campo}_hash" not in columnas)
    if faltantes:
        raise ErrorSeguridadCLI("Faltan columnas de cifrado en pacientes.")


def _validar_entorno_rotacion() -> None:
    activa = os.getenv(_ENV_KEY, "")
    previa = os.getenv(_ENV_KEY_PREVIOUS, "")
    if not _es_clave_valida(activa):
        raise ErrorSeguridadCLI("CLINICDESK_CRYPTO_KEY inválida.")
    if previa and not _es_clave_valida(previa):
        raise ErrorSeguridadCLI("CLINICDESK_CRYPTO_KEY_PREVIOUS inválida.")


def _es_clave_valida(clave: str) -> bool:
    limpia = clave.strip()
    if len(limpia) < 32:
        return False
    if len(set(limpia)) < 10:
        return False
    return True


def _auditar_rotacion(
    con: sqlite3.Connection,
    *,
    filas_leidas: int,
    filas_actualizadas: int,
    campos_recifrados: int,
) -> None:
    servicio = AuditService(RepositorioAuditoriaEventosSqlite(con))
    servicio.registrar(
        action="CRYPTO_ROTATE",
        outcome="ok",
        actor_username="security_cli",
        actor_role="SYSTEM",
        correlation_id=None,
        metadata={
            "n_patients": filas_leidas,
            "warnings_count": max(filas_leidas - filas_actualizadas, 0),
            "movimientos": campos_recifrados,
            "reason_code": "rotate_apply",
        },
    )


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Herramientas de administración de claves de cifrado.")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("generate-key", help="Genera una clave aleatoria segura")
    sub.add_parser("check-key", help="Valida que CLINICDESK_CRYPTO_KEY sea usable")

    rotate = sub.add_parser("rotate-key", help="Verifica o aplica rotación de clave")
    rotate_group = rotate.add_mutually_exclusive_group(required=True)
    rotate_group.add_argument("--dry-run", action="store_true", help="No modifica datos")
    rotate_group.add_argument("--apply", action="store_true", help="Re-cifra y persiste datos")
    rotate.add_argument("--db-path", default="data/clinicdesk.sqlite", help="Ruta de base SQLite")
    rotate.add_argument(
        "--schema-path",
        default="clinicdesk/app/infrastructure/sqlite/schema.sql",
        help="Ruta de schema.sql",
    )
    rotate.add_argument("--batch-size", type=int, default=200, help="Tamaño de lote para --apply")
    rotate.add_argument("--sample-size", type=int, default=25, help="Muestra para --dry-run")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    if args.comando == "generate-key":
        return generar_clave_segura()
    if args.comando == "check-key":
        return validar_clave_activa()
    if args.comando == "rotate-key":
        return ejecutar_rotacion(args)
    parser.error("Comando no soportado")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
