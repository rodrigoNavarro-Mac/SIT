# Archivo: urls.py (AppSIT)

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from AppSIT.views import UserViewSet, SubjectViewSet, TeacherSubjectViewSet, GroupViewSet, StudentGroupViewSet, StudentSubjectViewSet, GradeViewSet, ClassSessionViewSet, AttendanceViewSet, TutoringSessionViewSet, TutoringAttendanceViewSet
from AppSIT import views

# Creación del enrutador para los viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'teacher-subjects', TeacherSubjectViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'student-groups', StudentGroupViewSet)
router.register(r'student-subjects', StudentSubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'class-sessions', ClassSessionViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'tutoring-sessions', TutoringSessionViewSet)
router.register(r'tutoring-attendance', TutoringAttendanceViewSet)

# Definición de urlpatterns
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("inicio_estudiante/", views.index_estudiante, name="inicio_estudiante"),
    path("inicio_docente/", views.index_docente, name="inicio_docente"),
    path("materia_alumno/", views.materia_alumno, name="materia_alumno"),
    path("panel_docente/", views.panel_docente, name="panel_docente"),
    path('materia_impartida/<int:id>/', views.materia_impartida, name='materia_impartida'),
    path("inicio_tutor/", views.index_tutor, name="inicio_tutor"),
    path("seleccion_materias_docente/", views.seleccion_materias_docente, name="seleccion_materias_docente"),
    path("seleccion_tutorados/", views.seleccion_tutorados, name="seleccion_tutorados"),
    path("logout/", views.logout_user, name="logout"),
    path("index_coordinador/", views.index_coordinador, name="inicio_coordinador"),
    path("asignacion_materia_coordinador/", views.asignacion_materia_coordinador, name="asignacion_materia_coordinador"),
    path("asignacion_tutores/", views.asignacion_tutores, name="asignacion_tutores"),
    path("panel_docente_asistencia/", views.panel_docente_asistencia, name="panel_docente_asistencia"),
    path('materia_impartida_asistencia/<int:id>/', views.captura_asistencia_docente, name='captura_asistencia_docente'),
    path("asistencia_tutoria/", views.asistencia_tutoria, name="asistencia_tutoria"),
    path('seleccion_alumno/', views.seleccion_alumno, name='seleccion_alumno'),
    path('seguimiento_academico/<int:student_id>/', views.seguimiento_academico_individual, name='seguimiento_academico_individual'),
    path('appsit/', include('AppSIT.urls')),
    path('', include(router.urls)),  # Incluye las rutas del router
]

# Personalización del encabezado del administrador
admin.site.site_header = "Panel administrador SIT"
