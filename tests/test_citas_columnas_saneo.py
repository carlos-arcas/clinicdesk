from clinicdesk.app.application.citas.atributos import obtener_columnas_default_citas, sanear_columnas_citas


def test_sanear_columnas_corrige_duplicados_desconocidas_y_vacio() -> None:
    columnas, restauradas = sanear_columnas_citas(("fecha", "foo", "fecha", "estado"))
    assert columnas == ("fecha", "estado", "cita_id")
    assert restauradas is True

    columnas_vacias, restauradas_vacias = sanear_columnas_citas(())
    assert columnas_vacias == (*obtener_columnas_default_citas(), "cita_id")
    assert restauradas_vacias is True
