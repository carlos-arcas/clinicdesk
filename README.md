# ClinicDesk
Portfolio de aplicación de escritorio para gestión clínica.

## Cómo ejecutar
1. Desde la raíz del repositorio, ejecuta:
   - `python -m clinicdesk`
   - (alternativo) `python -m clinicdesk.app`
2. **No ejecutes módulos individuales** como `clinicdesk/app/pages/pacientes/page.py`, ya que no cargan el menú ni las acciones globales.

## Importación/Exportación CSV
1. Abre la aplicación y ve al menú **Archivo → Importar/Exportar CSV…**.
2. Selecciona la entidad (Pacientes, Médicos, Personal, etc.).
3. Usa **Importar…** para cargar un CSV o **Exportar…** para generar uno.

### CSVs de ejemplo
En `clinicdesk/data/examples/` hay datos realistas para empezar:
- `pacientes.csv`
- `medicos.csv`
- `personal.csv`

## Tests
Consulta las instrucciones en [docs/TESTING.md](docs/TESTING.md).
