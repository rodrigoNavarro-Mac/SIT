from io import BytesIO
from openpyxl import load_workbook, Workbook
import os
from AppSIT.models import TutoringSession, TutoringAttendance, Group, User

def generar_listas_asistencia_tutorias(tutor, parcial_numero):
    """
    Genera el formato de asistencia individual y grupal en un único archivo Excel.

    Parámetros:
    - tutor: El objeto User del tutor.
    - parcial_numero: Número del parcial (1, 2, 3 o 4).

    Retorna:
    - Un archivo Excel con el formato rellenado.
    """
    # Verificar si el tutor tiene un grupo asignado
    try:
        grupo = Group.objects.get(teacher=tutor)
    except Group.DoesNotExist:
        raise ValueError("No tienes un grupo asignado.")

    # Construir la ruta al archivo base
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path_input_excel = os.path.join(base_dir, "exports", "R18-PC18 Lista de asistencia a tutoría Individual-Grupal-S6.xlsx")

    # Verificar que el archivo exista
    if not os.path.exists(path_input_excel):
        raise FileNotFoundError(f"No se encontró el archivo: {path_input_excel}")

    # Cargar el archivo base
    wb = load_workbook(path_input_excel)

    # Mapear códigos de academias a nombres completos
    academias = {
        "ISC": "Ingeniería en Sistemas Computacionales",
        "IM": "Ingeniería Mecatrónica",
        "IB": "Ingeniería Bioquímica",
        "II": "Ingeniería Industrial",
        "LG": "Licenciatura en Gastronomía",
        "N/A": "No aplica",
    }

    # --- Rellenar Hoja Individual ---
    hoja_individual = wb["Individual"]

    hoja_individual["B2"] = tutor.nombrecompleto()  # Persona Tutora
    hoja_individual["B3"] = academias.get(tutor.academia, "Desconocida")  # Academia
    hoja_individual["B4"] = f"{grupo.semester} {grupo.group_name}"  # Semestre y Grupo
    hoja_individual["D2"] = parcial_numero  # Parcial

    sesiones_individuales = TutoringSession.objects.filter(
        tutor=tutor, is_group=False
    ).prefetch_related("attendances")

    fila_individual = 8
    for sesion in sesiones_individuales:
        for asistencia in sesion.attendances.filter(is_present=True):
            estudiante = asistencia.student
            hoja_individual[f"B{fila_individual}"] = estudiante.nombrecompleto()
            hoja_individual[f"C{fila_individual}"] = sesion.date.strftime("%d/%m/%Y")
            if estudiante.genero == "Masculino":
                hoja_individual[f"D{fila_individual}"] = "X"
            elif estudiante.genero == "Femenino":
                hoja_individual[f"E{fila_individual}"] = "X"
            fila_individual += 1

    # --- Rellenar y Replicar Hoja Grupal ---
    hoja_grupal_base = wb["Grupal"]
    sesiones_grupales = TutoringSession.objects.filter(
        tutor=tutor, is_group=True
    ).prefetch_related("attendances")

    for num_sesion, sesion in enumerate(sesiones_grupales, start=1):
        # Crear una copia de la hoja grupal
        hoja_grupal = wb.copy_worksheet(hoja_grupal_base)
        hoja_grupal.title = f"Sesión grupal No. {num_sesion}"

        # Rellenar datos generales
        hoja_grupal["B2"] = tutor.nombrecompleto()  # Persona Tutora
        hoja_grupal["B3"] = academias.get(tutor.academia, "Desconocida")  # Academia
        hoja_grupal["B4"] = f"{grupo.semester} {grupo.group_name}"  # Semestre y Grupo
        hoja_grupal["B5"] = sesion.date.strftime("%d/%m/%Y")  # Fecha de la sesión
        hoja_grupal["E3"] = num_sesion  # Número de sesión grupal
        hoja_grupal["E2"] = parcial_numero  # Parcial

        # Rellenar lista de alumnos presentes
        fila_grupal = 9
        for asistencia in sesion.attendances.filter(is_present=True):
            estudiante = asistencia.student
            hoja_grupal[f"B{fila_grupal}"] = estudiante.nombrecompleto()
            if estudiante.genero == "Masculino":
                hoja_grupal[f"C{fila_grupal}"] = "X"
            elif estudiante.genero == "Femenino":
                hoja_grupal[f"D{fila_grupal}"] = "X"
            fila_grupal += 1

    # Eliminar la hoja base "Grupal"
    del wb["Grupal"]

    # Guardar en un buffer
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
