from clinicdesk.app.application.usecases.exportar_auditoria_csv import mapear_error_exportacion


def test_mapear_error_exportacion_permission_error() -> None:
    assert mapear_error_exportacion(PermissionError("denegado")) == "sin_permisos"


def test_mapear_error_exportacion_file_not_found() -> None:
    assert mapear_error_exportacion(FileNotFoundError("ruta inválida")) == "ruta_invalida"


def test_mapear_error_exportacion_winerror_32() -> None:
    err = OSError("[WinError 32] The process cannot access the file because it is being used by another process")
    assert mapear_error_exportacion(err) == "archivo_en_uso"


def test_mapear_error_exportacion_oserror_generico() -> None:
    assert mapear_error_exportacion(OSError("fallo de E/S")) == "io_error"
