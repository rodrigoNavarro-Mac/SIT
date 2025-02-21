from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    UserViewSet, SubjectViewSet, TeacherSubjectViewSet,
    GroupViewSet, StudentGroupViewSet, StudentSubjectViewSet,
    GradeViewSet, ClassSessionViewSet, AttendanceViewSet,
    TutoringSessionViewSet, TutoringAttendanceViewSet
)

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

urlpatterns = [
    path('', include(router.urls)),  # API patterns
    
    path('exportar_reporte_seguimiento/', views.exportar_reporte_seguimiento, name='exportar_reporte_seguimiento'),
    path('exportar_asistencia/', views.exportar_asistencia, name='exportar_asistencia'),
    
    
]
