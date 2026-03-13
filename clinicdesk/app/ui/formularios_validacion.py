from __future__ import annotations

from collections.abc import Sequence

from clinicdesk.app.i18n import I18nManager


def validar_formulario_paciente(valores: dict[str, str], *, i18n: I18nManager) -> dict[str, str]:
    errores: dict[str, str] = {}
    if not valores.get("documento"):
        errores["documento"] = i18n.t("form.error.documento_requerido")
    if not valores.get("nombre"):
        errores["nombre"] = i18n.t("form.error.nombre_requerido")
    if not valores.get("apellidos"):
        errores["apellidos"] = i18n.t("form.error.apellidos_requeridos")

    email = valores.get("email", "")
    if email and "@" not in email:
        errores["email"] = i18n.t("form.error.email_invalido")
    return errores


def validar_formulario_cita(valores: dict[str, str], *, i18n: I18nManager) -> dict[str, str]:
    errores: dict[str, str] = {}
    if not valores.get("paciente_id") or not valores.get("medico_id") or not valores.get("sala_id"):
        errores["inicio"] = i18n.t("citas.form.error.selectores")
    if not valores.get("inicio"):
        errores["inicio"] = i18n.t("citas.form.error.inicio")
    if not valores.get("fin"):
        errores["fin"] = i18n.t("citas.form.error.fin")
    return errores


def primer_campo_con_error(errores: dict[str, str], orden_campos: Sequence[str]) -> str | None:
    for campo in orden_campos:
        if campo in errores:
            return campo
    return None
