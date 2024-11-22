from django.contrib import admin
from .models import User, Subject, TeacherSubject, Group, StudentGroup, Grade, StudentSubject, ClassSession, Attendance, TutoringSession, TutoringAttendance
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Recursos para importar/exportar datos
class SubjectResource(resources.ModelResource):
    class Meta:
        model = Subject
        fields = ('semester', 'subject_name', 'clave', 'credits', 'year', 'period')
        import_id_fields = []

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'apellido_paterno', 'apellido_materno', 'user_type', 'genero')
        import_id_fields = ['username']

@admin.register(User)
class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    resource_class = UserResource
    list_filter = ['genero', 'user_type', 'academia']
    list_display = ('username', 'first_name', 'apellido_paterno', 'apellido_materno', 'academia', 'email', 'user_type', 'genero')
    list_editable = ('first_name', 'apellido_paterno', 'apellido_materno', 'user_type', 'genero')
    list_per_page = 15

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'apellido_paterno', 'apellido_materno', 'user_type', 'genero', 'academia')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'apellido_paterno', 'apellido_materno', 'user_type', 'genero', 'academia'),
        }),
    )
    ordering = ["username"]

@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    resource_class = SubjectResource
    list_display = ['subject_name', 'clave', 'credits', 'year', 'period']
    list_editable = ['clave', 'credits', 'year', 'period']
    ordering = ['clave']
    list_per_page = 15

@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ('teacher_info', 'subject_info', 'schedule_monday', 'schedule_tuesday', 'schedule_wednesday', 'schedule_thursday', 'schedule_friday')
    list_editable = ['schedule_monday', 'schedule_tuesday', 'schedule_wednesday', 'schedule_thursday', 'schedule_friday']
    list_per_page = 15

    def teacher_info(self, obj):
        return f"{obj.teacher.username} - {obj.teacher.first_name} {obj.teacher.apellido_paterno} {obj.teacher.apellido_materno}"
    teacher_info.short_description = 'Información del Docente'

    def subject_info(self, obj):
        return f"Clave: {obj.subject.clave}, Nombre: {obj.subject.subject_name}, Período: {obj.subject.period} {obj.subject.year}"
    subject_info.short_description = 'Información de la Materia'

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'semester', 'teacher_info')
    list_per_page = 15

    def teacher_info(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.apellido_paterno} {obj.teacher.apellido_materno}"
    teacher_info.short_description = 'Tutor'

@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('user_info', 'group_info')
    list_per_page = 15

    def user_info(self, obj):
        return f"{obj.student.nombrecompleto()} - {obj.student.username}"

    def group_info(self, obj):
        return f"{obj.group.semester} {obj.group.group_name} {obj.group.teacher.nombrecompleto()}"

@admin.register(StudentSubject)
class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('student_info', 'subject_info')
    list_per_page = 15

    def student_info(self, obj):
        return f"{obj.student.nombrecompleto()} - {obj.student.username}"

    def subject_info(self, obj):
        return f"{obj.subject.subject_name} (Clave: {obj.subject.clave})"

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student_subject', 'semester_taken', 'final')  # Muestra estos campos en la lista
    fields = ('teacher', 'student_subject', 'semester_taken', 'parcial_1', 'parcial_2', 'parcial_3', 'parcial_4')  # Permite editar estos campos
    search_fields = ('teacher__username', 'student_subject__student__username', 'semester_taken')  # Búsqueda por estos campos
    list_per_page = 15

@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = ('teacher_subject', 'date')
    list_per_page = 15

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('class_session', 'student', 'status')
    list_per_page = 15

@admin.register(TutoringSession)
class TutoringSessionAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'date', 'is_group')
    list_filter = ('tutor', 'date', 'is_group')

@admin.register(TutoringAttendance)
class TutoringAttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'is_present')
    list_filter = ('session', 'student', 'is_present')
