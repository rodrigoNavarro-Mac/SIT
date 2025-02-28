from venv import logger
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Subject, TeacherSubject, Grade, Group, StudentSubject, StudentGroup, User, TutoringSession, TutoringAttendance
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render, redirect
from .models import ClassSession, Attendance, StudentSubject
from datetime import date
from django.db.utils import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from rest_framework import viewsets
from .models import User, Subject, TeacherSubject, Group, StudentGroup, StudentSubject, Grade, ClassSession, Attendance, TutoringSession, TutoringAttendance
from .serializers import UserSerializer, SubjectSerializer, TeacherSubjectSerializer, GroupSerializer, StudentGroupSerializer, StudentSubjectSerializer, GradeSerializer, ClassSessionSerializer, AttendanceSerializer, TutoringSessionSerializer, TutoringAttendanceSerializer
from django.http import HttpResponse
from .exports.Seguimiento_académico import generar_reporte_seguimiento
from .exports.listas_asistencia_tutorias import generar_listas_asistencia_tutorias
from .exports.reporte_asistencia import generar_reporte_asistencia
from rest_framework.decorators import api_view
from rest_framework.response import Response




     
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class TeacherSubjectViewSet(viewsets.ModelViewSet):
    queryset = TeacherSubject.objects.all()
    serializer_class = TeacherSubjectSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class StudentGroupViewSet(viewsets.ModelViewSet):
    queryset = StudentGroup.objects.all()
    serializer_class = StudentGroupSerializer

class StudentSubjectViewSet(viewsets.ModelViewSet):
    queryset = StudentSubject.objects.all()
    serializer_class = StudentSubjectSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class ClassSessionViewSet(viewsets.ModelViewSet):
    queryset = ClassSession.objects.all()
    serializer_class = ClassSessionSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer

class TutoringSessionViewSet(viewsets.ModelViewSet):
    queryset = TutoringSession.objects.all()
    serializer_class = TutoringSessionSerializer

class TutoringAttendanceViewSet(viewsets.ModelViewSet):
    queryset = TutoringAttendance.objects.all()
    serializer_class = TutoringAttendanceSerializer


def login_view(request):
    """
    Maneja el proceso de inicio de sesión.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if user.user_type == 'Estudiante':
                return JsonResponse({'redirect_url': reverse('inicio_estudiante')})
            elif user.user_type == 'Docente':
                return JsonResponse({'redirect_url': reverse('inicio_docente')})
            elif user.user_type == 'Coordinador':
                return JsonResponse({'redirect_url': reverse('inicio_coordinador')})
            else:
                return JsonResponse({'redirect_url': reverse('login')})
        else:
            return JsonResponse({'message': 'Credenciales inválidas', 'message_type': 'warning'}, status=400)

    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def index_estudiante(request):
    return render(request, 'index_estudiante.html')

@login_required
def index_docente(request):
    return render(request, 'docente/index_docente.html')       

@login_required
def index_tutor(request):
    return render(request, 'tutor/index_tutor.html')

@login_required
def index_coordinador(request):
    return render(request, 'coordinador/index_coordinador.html')

@login_required
@csrf_exempt
def asignacion_materia_coordinador(request):
    if request.method == 'POST':
        teacher_ids = request.POST.getlist('docente_checkbox')
        subject_ids = request.POST.getlist('materia_checkbox')

        success_count = 0
        error_count = 0
        success_messages = []
        error_messages = []

        for teacher_id in teacher_ids:
            teacher = User.objects.get(pk=teacher_id)
            for subject_id in subject_ids:
                subject = Subject.objects.get(pk=subject_id)

                schedule_monday = request.POST.get(f'horario_lunes_{subject_id}', None)
                schedule_tuesday = request.POST.get(f'horario_martes_{subject_id}', None)
                schedule_wednesday = request.POST.get(f'horario_miercoles_{subject_id}', None)
                schedule_thursday = request.POST.get(f'horario_jueves_{subject_id}', None)
                schedule_friday = request.POST.get(f'horario_viernes_{subject_id}', None)

                obj, created = TeacherSubject.objects.update_or_create(
                    teacher=teacher,
                    subject=subject,
                    defaults={
                        'schedule_monday': schedule_monday,
                        'schedule_tuesday': schedule_tuesday,
                        'schedule_wednesday': schedule_wednesday,
                        'schedule_thursday': schedule_thursday,
                        'schedule_friday': schedule_friday
                    }
                )

                if created:
                    success_messages.append(f"Asignación creada correctamente para el docente {teacher.nombrecompleto()} y materia {subject.subject_name}.")
                    success_count += 1
                else:
                    error_messages.append(f"Asignación actualizada para el docente {teacher.nombrecompleto()} y materia {subject.subject_name}.")
                    error_count += 1

        response_data = {
            'success_count': success_count,
            'error_count': error_count,
            'success_messages': success_messages,
            'error_messages': error_messages,
        }

        return JsonResponse(response_data)

    else:
        teachers = User.objects.filter(user_type='Docente')
        subjects = Subject.objects.all()
        context = {
            'teachers': teachers,
            'subjects': subjects,
        }
        return render(request, 'coordinador/asignacion_materia_coordinador.html', context)

@login_required
@csrf_exempt
def seleccion_tutorados(request):
    academia_seleccionada = request.user.academia
    tutor_students = User.objects.filter(academia=academia_seleccionada, user_type='Estudiante')

    if request.method == 'POST':
        if 'assign_tutorados' in request.POST:
            estudiantes_seleccionados = request.POST.getlist('alumno_checkbox')
            tutor_group = Group.objects.filter(teacher=request.user).first()

            if tutor_group:
                successful_assignments = []
                failed_assignments = []

                for estudiante_id in estudiantes_seleccionados:
                    student = User.objects.get(pk=estudiante_id)
                    if StudentGroup.objects.filter(student=student).exists():
                        failed_assignments.append(student.username)
                    else:
                        try:
                            StudentGroup.objects.create(student=student, group=tutor_group)
                            successful_assignments.append(student.username)
                        except IntegrityError:
                            failed_assignments.append(student.username)

                if successful_assignments:
                    message = f'Los siguientes estudiantes fueron asignados correctamente: {", ".join(successful_assignments)}.'
                    message_type = 'success'
                else:
                    message = 'No se realizó ninguna asignación.'
                    message_type = 'error'

                if failed_assignments:
                    message_failed = f'Los siguientes estudiantes ya están asignados a otro grupo: {", ".join(failed_assignments)}'
                else:
                    message_failed = ''

                response_data = {
                    'message': f'{message}\n{message_failed}',
                    'message_type': 'error' if failed_assignments else 'success'
                }
                return JsonResponse(response_data, status=400 if failed_assignments else 200)
            else:
                return JsonResponse({'message': 'El tutor no tiene asignado ningún grupo.', 'message_type': 'error'}, status=400)

    context = {'tutor_students': tutor_students, 'academia': academia_seleccionada}
    return render(request, 'tutor/seleccion_tutorados.html', context)

@login_required
def seleccion_materias_docente(request):
    user = request.user
    if user.user_type != 'Docente':
        return redirect('home')

    group = Group.objects.filter(teacher=user).first()
    if not group:
        messages.error(request, "No tienes un grupo asignado.")
        return redirect('home')

    alumnos = StudentGroup.objects.filter(group=group).select_related('student')

    academias = [
        ('ISC', 'Ingeniería en Sistemas Computacionales'),
        ('IM', 'Ingeniería Mecatrónica'),
        ('IB', 'Ingeniería Bioquímica'),
        ('II', 'Ingeniería Industrial'),
        ('LG', 'Licenciatura en Gastronomía'),
        ('N/A', 'No aplica')
    ]

    selected_academia = request.GET.get('academia', user.academia)

    materias = TeacherSubject.objects.filter(teacher__academia=selected_academia).select_related('subject')

    if request.method == 'POST':
        materias_seleccionadas = request.POST.getlist('materia[]')
        alumnos_seleccionados = request.POST.getlist('seleccion[]')

        if not materias_seleccionadas or not alumnos_seleccionados:
            return JsonResponse({'message': 'Debes seleccionar al menos una materia y un alumno.', 'message_type': 'error'}, status=400)

        registros_creados = 0
        registros_existentes = 0
        for alumno_id in alumnos_seleccionados:
            alumno = User.objects.get(id=alumno_id)
            for materia_id in materias_seleccionadas:
                materia = Subject.objects.get(id=materia_id)
                if not StudentSubject.objects.filter(student=alumno, subject=materia).exists():
                    StudentSubject.objects.create(student=alumno, subject=materia)
                    registros_creados += 1
                else:
                    registros_existentes += 1

        message = f'Se han asignado {registros_creados} nuevas asignaciones. {registros_existentes} asignaciones ya existían.'
        message_type = 'success'
        return JsonResponse({'message': message, 'message_type': message_type}, status=200)

    context = {
        'alumnos': alumnos,
        'materias': materias,
        'academias': academias,
        'selected_academia': selected_academia,
    }
    return render(request, 'tutor/seleccion_materias_docente.html', context)

from django.http import JsonResponse

@login_required
def asistencia_tutoria(request):
    tutor = request.user
    students = User.objects.filter(user_type='Estudiante')
    session_date = timezone.now().date()  # Fecha actual

    if request.method == 'POST':
        session_type = request.POST.get('session_type', 'group')  # Por defecto grupal

        try:
            if session_type == 'group':
                # Validar que no exista otra sesión grupal en el mismo día
                existing_sessions = TutoringSession.objects.filter(tutor=tutor, date=session_date, is_group=True)
                if existing_sessions.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Ya existe una sesión grupal para este día.'
                    })

                # Crear la sesión grupal
                session, _ = TutoringSession.objects.get_or_create(tutor=tutor, date=session_date, is_group=True)

                # Registrar asistencia
                for student in students:
                    status = request.POST.get(f'is_present_{student.id}')
                    is_present = True if status == 'on' else False
                    TutoringAttendance.objects.create(session=session, student=student, is_present=is_present)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Asistencia grupal registrada correctamente.'
                })

            elif session_type == 'individual':
                # Registrar sesión individual
                individual_student_id = request.POST.get('individual_student_id')
                individual_student = User.objects.get(id=individual_student_id)

                # Validar que no exista otra sesión individual para el mismo estudiante en el mismo día
                existing_sessions = TutoringSession.objects.filter(
                    tutor=tutor, date=session_date, is_group=False, attendances__student=individual_student
                )
                if existing_sessions.exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Ya existe una sesión individual para el estudiante {individual_student.nombrecompleto()} en este día.'
                    })

                session, _ = TutoringSession.objects.get_or_create(tutor=tutor, date=session_date, is_group=False)
                status = request.POST.get('is_present_individual')
                is_present = True if status == 'on' else False
                TutoringAttendance.objects.create(session=session, student=individual_student, is_present=is_present)

                return JsonResponse({
                    'status': 'success',
                    'message': f'Asistencia individual registrada correctamente para {individual_student.nombrecompleto()}.'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Ocurrió un error al registrar la asistencia: {str(e)}'
            })

    context = {
        'students': students,
        'session_date': session_date,  # Enviar la fecha actual
    }
    return render(request, 'tutor/asistencia_tutoria.html', context)


@login_required
def materia_alumno(request):
    if request.user.user_type != 'Estudiante':
        return redirect('login')

    semesters = Subject.objects.values_list('semester', flat=True).distinct().order_by('semester')
    selected_semester = request.GET.get('semester')
    subject_details = []

    if selected_semester:
        subjects = Subject.objects.filter(semester=selected_semester)
        student = User.objects.get(user=request.user)

        for subject in subjects:
            teacher_subject = TeacherSubject.objects.filter(subject=subject).first()
            teacher = teacher_subject.teacher if teacher_subject else None

            student_subject = StudentSubject.objects.filter(student=student, subject=subject).first()
            if student_subject:
                grade = Grade.objects.filter(student_subject=student_subject).first()
            else:
                grade = None

            subject_details.append({
                'subject': subject,
                'teacher': teacher,
                'grade': grade
            })

    return render(request, 'materia_alumno.html', {
        'semesters': semesters,
        'subject_details': subject_details,
        'selected_semester': selected_semester
    })

@login_required
def panel_docente(request):
    if request.user.user_type != 'Docente':
        return redirect('inicio_docente')

    materias_por_semestre = {}
    teacher_subjects = TeacherSubject.objects.filter(teacher=request.user).select_related('subject').order_by('subject__semester')
    for ts in teacher_subjects:
        semestre = ts.subject.semester
        if semestre not in materias_por_semestre:
            materias_por_semestre[semestre] = []
        materias_por_semestre[semestre].append(ts.subject)

    materias_ordenadas_por_semestre = dict(sorted(materias_por_semestre.items()))

    return render(request, 'docente/panel_docente.html', {'materias_por_semestre': materias_ordenadas_por_semestre})

@login_required
def materia_impartida(request, id):
    
    materia = get_object_or_404(Subject, id=id)

    logger.info(f"Materia ID: {id}")
    materia = get_object_or_404(Subject, id=id)
    logger.info(f"Materia obtenida: {materia}")

    try:
            asignacion_docente = TeacherSubject.objects.get(subject=materia, teacher=request.user)
            logger.info(f"Asignación docente encontrada: {asignacion_docente}")
    except TeacherSubject.DoesNotExist:
            logger.error(f"No se encontró asignación docente para materia {materia}")
            return render(request, 'error.html', {'mensaje': 'No imparte esta materia'})


    try:
        asignacion_docente = TeacherSubject.objects.get(subject=materia, teacher=request.user)
    except TeacherSubject.DoesNotExist:
        return render(request, 'error.html', {'mensaje': 'No imparte esta materia'})

    semester_taken = materia.semester

    if request.method == 'POST':
        error = False
        for key, value in request.POST.items():
            if key.startswith('grades_'):
                _, student_id, parcial_number = key.split('_')
                student_subject = StudentSubject.objects.get(student_id=student_id, subject=materia)
                grade, created = Grade.objects.get_or_create(
                    teacher=request.user,
                    student_subject=student_subject,
                    semester_taken=semester_taken,
                    defaults={'parcial_1': 0, 'parcial_2': 0, 'parcial_3': 0, 'parcial_4': 0}
                )
                if value.strip():
                    try:
                        value_int = int(value)
                        if value_int < 0 or value_int > 100:
                            error = True
                            messages.error(request, f'Calificación inválida {value_int} para {student_subject.student.get_full_name}. Debe estar entre 0 y 100.')
                        else:
                            setattr(grade, f'parcial_{parcial_number}', value_int)
                    except ValueError:
                        error = True
                        messages.error(request, f'Calificación inválida {value} para {student_subject.student.get_full_name}. Debe ser un número.')
                grade.save()

        if not error:
            messages.success(request, 'Calificaciones guardadas correctamente.')
        return redirect('materia_impartida', id=id)

    asignaciones_estudiantes = StudentSubject.objects.filter(subject=materia)
    estudiantes_con_calificaciones = []
    for asignacion in asignaciones_estudiantes:
        grade, created = Grade.objects.get_or_create(
            teacher=request.user,
            student_subject=asignacion,
            semester_taken=semester_taken,
            defaults={'parcial_1': 0, 'parcial_2': 0, 'parcial_3': 0, 'parcial_4': 0}
        )
        calificaciones = {
            'parcial_1': grade.parcial_1,
            'parcial_2': grade.parcial_2,
            'parcial_3': grade.parcial_3,
            'parcial_4': grade.parcial_4,
        }
        estudiantes_con_calificaciones.append({
            'estudiante': asignacion.student,
            'calificaciones': calificaciones
        })

    context = {
        'materia': materia,
        'asignacion_docente': asignacion_docente,
        'estudiantes_con_calificaciones': estudiantes_con_calificaciones,
    }

    return render(request, 'docente/materia_impartida.html', context)

@login_required
def asignacion_tutores(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        teacher_id = request.POST.get('teacher')
        semester = request.POST.get('semester')

        response_data = {
            'message': '',
            'message_type': 'error'
        }

        if group_name not in ['A', 'B']:
            response_data['message'] = 'El grupo debe ser A o B.'
            return JsonResponse(response_data)

        try:
            semester = int(semester)
            if semester < 1 or semester > 9:
                raise ValueError
        except ValueError:
            response_data['message'] = 'El semestre debe ser un número entre 1 y 9.'
            return JsonResponse(response_data)

        try:
            teacher = User.objects.get(id=teacher_id, user_type='Docente')

            group, created = Group.objects.update_or_create(
                group_name=group_name,
                semester=semester,
                defaults={'teacher': teacher}
            )

            response_data['message'] = f'Tutor {teacher.nombrecompleto} asignado correctamente al grupo {group_name} para el semestre {semester}.'
            response_data['message_type'] = 'success'
        except User.DoesNotExist:
            response_data['message'] = 'El docente seleccionado no existe.'
        except ValidationError as e:
            response_data['message'] = '; '.join(e.messages)
        except Exception as e:
            response_data['message'] = f'Ocurrió un error inesperado: {str(e)}'

        return JsonResponse(response_data)

    else:
        teachers = User.objects.filter(user_type='Docente')
        context = {'teachers': teachers}
        return render(request, 'coordinador/asignacion_tutores.html', context)

@login_required
def panel_docente_asistencia(request):
    if request.user.user_type != 'Docente':
        return redirect('inicio_docente')

    materias_por_semestre = {}
    teacher_subjects = TeacherSubject.objects.filter(teacher=request.user).select_related('subject').order_by('subject__semester')
    for ts in teacher_subjects:
        semestre = ts.subject.semester
        if semestre not in materias_por_semestre:
            materias_por_semestre[semestre] = []
        materias_por_semestre[semestre].append(ts.subject)

    materias_ordenadas_por_semestre = dict(sorted(materias_por_semestre.items()))

    return render(request, 'docente/panel_docente_asistencia.html', {'materias_por_semestre': materias_ordenadas_por_semestre})

@login_required
def captura_asistencia_docente(request, id):
    subject = get_object_or_404(Subject, id=id)
    teacher_subject = get_object_or_404(TeacherSubject, subject=subject, teacher=request.user)
    date_today = timezone.now().date()
    class_session, created = ClassSession.objects.get_or_create(
        teacher_subject=teacher_subject,
        date=date_today
    )

    if created:
        students_in_subject = StudentSubject.objects.filter(subject=subject)
        for student_subject in students_in_subject:
            Attendance.objects.get_or_create(
                class_session=class_session,
                student=student_subject.student,
            )

    attendance_records = Attendance.objects.filter(class_session=class_session).order_by('student__last_name', 'student__first_name')

    if request.method == 'POST':
        present_count = 0
        absent_count = 0
        for attendance_record in attendance_records:
            status_key = f'status_{attendance_record.student.id}'
            status = request.POST.get(status_key)
            attendance_record.status = status
            attendance_record.save()
            if status == 'Presente':
                present_count += 1
            else:
                absent_count += 1
        messages.success(request, f'Asistencia actualizada con éxito. Fecha: {date_today}, Presentes: {present_count}, Ausentes: {absent_count}.')
        return redirect('captura_asistencia_docente', id=id)

    context = {
        'class_session': class_session,
        'attendance_records': attendance_records,
    }

    return render(request, 'docente/materia_impartida_asistencia.html', context)

@login_required
def seleccion_alumno(request):
    user = request.user
    grupo = get_object_or_404(Group, teacher=user)
    estudiantes = StudentGroup.objects.filter(group=grupo).select_related('student').prefetch_related('student__studentsubject_set__subject')

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if student_id:
            return redirect('seguimiento_academico_individual', student_id=student_id)
        else:
            return JsonResponse({'status': 'error', 'message': 'Debe seleccionar un alumno.'})

    context = {
        'estudiantes': estudiantes
    }

    return render(request, 'tutor/seleccion_alumno.html', context)

@login_required
def seguimiento_academico_individual(request, student_id):
    student = get_object_or_404(User, id=student_id, user_type='Estudiante')

    student_group = get_object_or_404(StudentGroup, student=student)

    student_subjects = StudentSubject.objects.filter(student=student)
    seguimiento_academico = []

    tutorings = TutoringAttendance.objects.filter(student=student).select_related('session')

    for student_subject in student_subjects:
        grades = Grade.objects.filter(student_subject=student_subject)

        teacher_subjects = TeacherSubject.objects.filter(subject=student_subject.subject)
        class_sessions = ClassSession.objects.filter(teacher_subject__in=teacher_subjects)
        attendances = Attendance.objects.filter(class_session__in=class_sessions, student=student)

        total_classes = class_sessions.count()
        total_absent = attendances.filter(status='Ausente').count()
        total_present = total_classes - total_absent
        attendance_percentage = (total_present / total_classes) * 100 if total_classes > 0 else 0

        seguimiento_academico.append({
            'subject': student_subject.subject,
            'grades': grades,
            'class_sessions': class_sessions,
            'attendances': attendances,
            'total_absent': total_absent,
            'attendance_percentage': attendance_percentage
        })

    context = {
        'student': student,
        'seguimiento_academico': seguimiento_academico,
        'estudiantes': StudentGroup.objects.filter(group=student_group.group),
        'tutorings': tutorings
    }

    return render(request, 'tutor/seguimiento_academico_individual.html', context)


def exportar_reporte_seguimiento(request):
    try:
        # Validar que el usuario es un docente y tiene asignado un grupo
        if not request.user.is_authenticated or not Group.objects.filter(teacher=request.user).exists():
            return HttpResponse("Acceso no autorizado. Solo los tutores pueden generar este reporte.", status=403)

        # Generar el reporte pasándole el tutor (request.user)
        output = generar_reporte_seguimiento(request.user)

        # Preparar la respuesta HTTP para la descarga
        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename="R04-PC18 Seguimiento académico.xlsx"'
        return response
    except ValueError as e:
        return HttpResponse(str(e), status=400)
    except Exception as e:
        return HttpResponse(f"Error al generar el reporte: {str(e)}", status=500)
    
    
import zipfile
from io import BytesIO
from django.http import HttpResponse


def exportar_asistencia(request):
    """
    Exporta las listas de asistencia y el reporte de asistencia como un archivo ZIP.
    """
    try:
        # Validar que el usuario es un docente y tiene asignado un grupo
        if not request.user.is_authenticated or not Group.objects.filter(teacher=request.user).exists():
            return HttpResponse("Acceso no autorizado. Solo los tutores pueden generar este reporte.", status=403)

        # Generar ambos archivos
        listas_asistencia = generar_listas_asistencia_tutorias(request.user, parcial_numero=determinar_parcial_actual())
        reporte_asistencia = generar_reporte_asistencia(request.user)

        # Crear un buffer para el archivo ZIP
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            # Agregar la lista de asistencia al ZIP
            zip_file.writestr("R18-PC18 Lista de asistencia a tutoría Individual-Grupal-S6.xlsx", listas_asistencia.getvalue())
            # Agregar el reporte de asistencia al ZIP
            zip_file.writestr("R14-PC18 Reporte de asistencia a tutoría Individual - Grupal.xlsx", reporte_asistencia.getvalue())

        # Preparar la respuesta HTTP para el archivo ZIP
        zip_buffer.seek(0)
        response = HttpResponse(
            zip_buffer,
            content_type="application/zip"
        )
        response['Content-Disposition'] = 'attachment; filename="reportes_asistencia.zip"'
        return response

    except ValueError as e:
        return HttpResponse(str(e), status=400)
    except FileNotFoundError as e:
        return HttpResponse(f"Archivo base no encontrado: {str(e)}", status=404)
    except Exception as e:
        return HttpResponse(f"Error al generar los reportes: {str(e)}", status=500)




def determinar_parcial_actual():
    """
    Lógica para determinar el parcial actual.
    Puedes ajustar esto según las fechas del ciclo escolar o parámetros dinámicos.
    """
    from datetime import date
    hoy = date.today()

    if 1 <= hoy.month <= 3:
        return "1er Parcial"  # Primer parcial
    elif 4 <= hoy.month <= 6:
        return "2do Parcial"  # Segundo parcial
    elif 7 <= hoy.month <= 9:
        return "3er Parcial"  # Tercer parcial
    else:
        return "4to Parcial"  # Cuarto parcial


@api_view(['POST'])
def mobile_login_view(request):
    """
    Maneja el inicio de sesión solo para la aplicación móvil.
    Recibe las credenciales de inicio de sesión como datos JSON.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    # Autenticación de usuario
    user = authenticate(username=username, password=password)

    if user is not None:
        # Generar el nombre completo
        full_name = f"{user.first_name} {user.last_name}"

        # Datos del usuario que enviaremos a la app móvil
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'full_name': full_name,  # Enviar el nombre completo aquí
            'user_type': getattr(user, 'user_type', 'unknown'),  # Tipo de usuario (Ejemplo: Docente)
        }

        return JsonResponse({
            'message': 'Login exitoso',
            'status': 'success',
            'user_data': user_data
        })
    else:
        return JsonResponse({
            'message': 'Credenciales inválidas',
            'status': 'error'
        }, status=400)
        
def get_teacher_subjects(request, username):
    """
    Obtiene las materias asignadas al docente con el nombre de usuario proporcionado.
    """
    try:
        # Obtén el usuario docente
        teacher = User.objects.get(username=username, user_type='Docente')
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado o no es docente'}, status=404)

    # Obtener las materias del docente
    teacher_subjects = TeacherSubject.objects.filter(teacher=teacher).select_related('subject').order_by('subject__semester')

    materias_list = []
    for ts in teacher_subjects:
        materias_list.append({
            'subject_name': ts.subject.subject_name,
            'semester': ts.subject.semester,
        })

    # Devolver la respuesta como JSON
    return JsonResponse({'materias': materias_list})

@api_view(['GET'])
def get_students_by_subject_name(request, subject_name):
    """
    Obtiene la lista de estudiantes para una materia específica usando el nombre de la materia
    """
    try:
        # Obtener la materia por nombre
        subject = Subject.objects.get(subject_name=subject_name)
        
        # Obtener los estudiantes de la materia
        students = StudentSubject.objects.filter(subject=subject)
        
        # Crear lista de estudiantes con su información
        students_list = []
        for enrollment in students:
            students_list.append({
                'id': enrollment.student.id,
                'full_name': enrollment.student.nombrecompleto(),  # Llamar al método 'nombrecompleto'
                'status': 'Pendiente'  # Estado inicial de asistencia
            })
        
        return Response({
            'success': True,
            'subject_name': subject.subject_name,
            'students': students_list
        }, status=status.HTTP_200_OK)
        
    except Subject.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Materia no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)