from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EspecialidadSeed:
    nombre: str
    motivos: tuple[str, ...]


NOMBRES = (
    "Lucia",
    "Mateo",
    "Sofia",
    "Hugo",
    "Valeria",
    "Leo",
    "Daniela",
    "Pablo",
    "Martina",
    "Alvaro",
    "Elena",
    "Nicolas",
    "Irene",
    "Diego",
    "Carmen",
    "Javier",
    "Marta",
    "Adrian",
    "Noa",
    "Andres",
    "Paula",
    "Clara",
    "Raul",
    "Aitana",
    "Manuel",
    "Julia",
    "Rocio",
    "Sergio",
    "Teresa",
    "Marina",
    "Ismael",
    "Olga",
    "Ruben",
    "Natalia",
    "Carlos",
    "Alicia",
)

APELLIDOS = (
    "Garcia",
    "Rodriguez",
    "Fernandez",
    "Lopez",
    "Martinez",
    "Sanchez",
    "Perez",
    "Gomez",
    "Martin",
    "Ruiz",
    "Diaz",
    "Moreno",
    "Alonso",
    "Navarro",
    "Torres",
    "Vazquez",
    "Castro",
    "Serrano",
    "Ortega",
    "Gil",
    "Molina",
    "Suarez",
    "Romero",
    "Delgado",
    "Prieto",
    "Herrera",
    "Mendez",
    "Cabrera",
    "Arias",
    "Campos",
)

MUNICIPIOS = (
    "Madrid",
    "Mostoles",
    "Alcorcon",
    "Getafe",
    "Leganes",
    "Alcobendas",
    "Pozuelo",
    "Majadahonda",
    "Fuenlabrada",
    "Parla",
)

VIAS = (
    "Calle Mayor",
    "Avenida de Europa",
    "Calle Real",
    "Avenida del Mediterraneo",
    "Calle Doctor Fleming",
    "Calle Severo Ochoa",
    "Avenida de la Constitucion",
    "Calle de la Salud",
    "Paseo de la Estacion",
    "Calle de los Olmos",
)

DOMINIOS_CLINICA = (
    "clinicacentro.local",
    "saludnorte.local",
    "consultasierra.local",
)

DOMINIOS_CONTACTO = (
    "mailpaciente.net",
    "correo-familia.net",
    "buzonpersonal.net",
)

PUESTOS_PERSONAL = (
    "Recepcion",
    "Enfermeria",
    "Administracion",
    "Auxiliar clinico",
    "Tecnico de apoyo",
)

ALERGIAS_FRECUENTES = (
    "Penicilina",
    "AINEs",
    "Latex",
    "Yodo",
)

OBSERVACIONES_PACIENTE = (
    "Prefiere cita a primera hora.",
    "Acude con informe de especialista externo.",
    "Conviene confirmar telefono antes de procedimientos.",
    "Historial de seguimiento estable en los ultimos meses.",
    "Solicita revisiones agrupadas si es posible.",
)

NOTAS_CITA = (
    "Trae analitica pendiente para comentar en consulta.",
    "Pide revisar medicacion y tolerancia clinica.",
    "Refiere mejoria parcial desde la ultima visita.",
    "Se acuerda control telefonico si persisten sintomas.",
    "Conviene validar agenda de seguimiento al alta.",
    "Acude acompanado por familiar.",
)

ESPECIALIDADES = (
    EspecialidadSeed(
        "Medicina Familiar",
        (
            "Revision anual",
            "Control de tension arterial",
            "Seguimiento de tratamiento cronico",
            "Valoracion de sintomas respiratorios",
            "Consulta por dolor lumbar",
        ),
    ),
    EspecialidadSeed(
        "Pediatria",
        (
            "Revision infantil",
            "Control de crecimiento",
            "Consulta por fiebre",
            "Seguimiento de otitis",
            "Valoracion digestiva pediatrica",
        ),
    ),
    EspecialidadSeed(
        "Cardiologia",
        (
            "Revision cardiologica",
            "Seguimiento de hipertension",
            "Control tras Holter",
            "Valoracion de palpitaciones",
            "Reajuste de medicacion cardiovascular",
        ),
    ),
    EspecialidadSeed(
        "Traumatologia",
        (
            "Revision de rodilla",
            "Seguimiento post esguince",
            "Dolor de hombro",
            "Control de rehabilitacion",
            "Valoracion de sobrecarga muscular",
        ),
    ),
    EspecialidadSeed(
        "Dermatologia",
        (
            "Revision de lesion cutanea",
            "Seguimiento de tratamiento topico",
            "Consulta por dermatitis",
            "Control de acne inflamatorio",
            "Valoracion de nevus",
        ),
    ),
    EspecialidadSeed(
        "Neurologia",
        (
            "Seguimiento de cefaleas",
            "Revision neurologica",
            "Control de parestesias",
            "Consulta por mareo recurrente",
            "Ajuste de tratamiento neurologico",
        ),
    ),
)
