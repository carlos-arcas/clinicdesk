# Decisión técnica: privacidad de atributos en listados de pacientes

## Contexto
El listado de pacientes es un punto de exposición masiva de datos. Para reducir riesgo de divulgación accidental, los atributos personales/sensibles deben mostrarse enmascarados por defecto en vistas de listado.

## Inventario `atributos_paciente` (orden estable)

| atributo | tipo | fuente |
|---|---|---|
| id | int | dominio / tabla sqlite / DTO |
| tipo_documento | str | dominio / tabla sqlite |
| documento | str | dominio / tabla sqlite / DTO |
| nombre | str | dominio / tabla sqlite |
| apellidos | str | dominio / tabla sqlite |
| nombre_completo | str | DTO |
| telefono | optional | dominio / tabla sqlite / DTO |
| email | optional | dominio / tabla sqlite |
| fecha_nacimiento | optional | dominio / tabla sqlite |
| direccion | optional | dominio / tabla sqlite |
| activo | bool | dominio / tabla sqlite / DTO |
| num_historia | optional | dominio / tabla sqlite |
| alergias | optional | dominio / tabla sqlite |
| observaciones | optional | dominio / tabla sqlite |

## Clasificación de sensibilidad
- **PUBLICO**: se muestra sin máscara en listado.
- **PERSONAL**: se muestra enmascarado en listado.
- **SENSIBLE**: se muestra enmascarado en listado con regla conservadora.

### Mapa aplicado
- PUBLICO: `id`, `tipo_documento`, `nombre`, `apellidos`, `nombre_completo`, `activo`.
- PERSONAL: `documento`, `telefono`, `email`, `fecha_nacimiento`, `direccion`.
- SENSIBLE: `num_historia`, `alergias`, `observaciones`.

## Reglas de máscara (dominio)
- Deterministas y sin dependencias de UI/Qt.
- `None` o vacío -> `""`.
- No revelan más de 2-3 caracteres finales cuando aplica.
- Ejemplos:
  - documento `40000014` -> `******14`
  - teléfono `610000314` -> `*** *** 314`
  - email `a@b.com` -> `a***@b.com`
  - texto `Calle Mayor 3` -> `C********** 3`

## Consecuencia arquitectónica
Se define un contrato de aplicación para que presentadores/UI consuman:
1. Atributos disponibles y ordenados.
2. Clave i18n por atributo (`pacientes.<atributo>`).
3. Formateo en modo listado aplicando máscara según sensibilidad.

La vista de detalle/historial podrá solicitar el valor completo, pero ese caso no forma parte de esta decisión atómica.
