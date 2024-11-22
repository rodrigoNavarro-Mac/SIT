from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .validators import validate_username, validate_no_numbers


class User(AbstractUser):
    """
    Modelo de Usuario extendiendo el modelo User predeterminado de Django.
    """
    username = models.CharField(max_length=150, unique=True, validators=[validate_username])
    apellido_paterno = models.CharField(max_length=150, blank=True, validators=[validate_no_numbers])
    apellido_materno = models.CharField(max_length=150, blank=True, validators=[validate_no_numbers])
    first_name = models.CharField(max_length=150, validators=[validate_no_numbers])
    user_type = models.CharField(
        max_length=50,
        choices=[
            ('Docente', 'Docente'),
            ('Administrador', 'Administrador'),
            ('Estudiante', 'Estudiante'),
            ('Coordinador', 'Coordinador')
        ]
    )
    genero = models.CharField(
        max_length=15,
        choices=[
            ('Masculino', 'Masculino'),
            ('Femenino', 'Femenino'),
            ('Otro', 'Otro')
        ],
        default='Otro'
    )
    academia = models.CharField(
        max_length=15,
        choices=[
            ('ISC', 'Ingenieria Sistemas Computacionales'),
            ('IM', 'Ingenieria Mecatronica'),
            ('IB', 'Ingenieria Bioquimica'),
            ('II', 'Ingenieria Industrial'),
            ('LG', 'Licenciatura Gastronomia'),
            ('N/A', 'No aplica')
        ],
        default='N/A'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='appsit_user_set',
        blank=True,
        help_text='Los grupos a los que pertenece el usuario.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='appsit_user_set',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        verbose_name='user permissions'
    )

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.upper()
        self.apellido_paterno = self.apellido_paterno.upper()
        self.apellido_materno = self.apellido_materno.upper()
        if self.apellido_paterno and self.first_name:
            self.email = f"{slugify(self.first_name)}.{slugify(self.apellido_paterno)}@istatlixco.edu.mx"
        super(User, self).save(*args, **kwargs) 

    def nombrecompleto(self) -> str:
        return f"{self.first_name} {self.apellido_paterno} {self.apellido_materno}"

    def __str__(self):
        return self.username

class Subject(models.Model):
    """Modelo para representar una materia."""
    SEMESTER_CHOICES = (
        ('agosto-diciembre', 'Agosto-Diciembre'),
        ('enero-junio', 'Enero-Junio'),
    )

    semester = models.IntegerField(verbose_name="Semestre")
    subject_name = models.CharField(max_length=100, verbose_name="Nombre de materia")
    clave = models.CharField(max_length=15, verbose_name="Clave de Materia", unique=True, default='default_clave')
    credits = models.IntegerField(verbose_name="Créditos", default=1)
    year = models.IntegerField(verbose_name="Año", default=timezone.now().year)
    period = models.CharField(max_length=20, verbose_name="Período", choices=SEMESTER_CHOICES, default='enero-junio')

    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'

    def __str__(self) -> str:
        return f"{self.subject_name} (Semestre: {self.semester}, Clave: {self.clave}, Créditos: {self.credits}, Período: {self.period})"    

class TeacherSubject(models.Model):
    """
    Modelo para representar la asignación de materias a docentes.
    """
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Docente", limit_choices_to={'user_type': 'Docente'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Materia")
    schedule_monday = models.CharField(max_length=11, verbose_name="Horario Lunes", null=True, blank=True)
    schedule_tuesday = models.CharField(max_length=11, verbose_name="Horario Martes", null=True, blank=True)
    schedule_wednesday = models.CharField(max_length=11, verbose_name="Horario Miércoles", null=True, blank=True)
    schedule_thursday = models.CharField(max_length=11, verbose_name="Horario Jueves", null=True, blank=True)
    schedule_friday = models.CharField(max_length=11, verbose_name="Horario Viernes", null=True, blank=True)

    class Meta:
        verbose_name = 'Docente-Materia'
        verbose_name_plural = 'Docentes-Materias'
        unique_together = ('teacher', 'subject')  

    def __str__(self) -> str:
        return f"{self.subject} ({self.teacher.username})"

User = get_user_model()

class Group(models.Model):
    group_name = models.CharField(max_length=2, verbose_name="Grupo")
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Tutor",
        limit_choices_to={'user_type': 'Docente'}
    )
    semester = models.IntegerField(verbose_name="Semestre")

    class Meta:
        verbose_name = 'Grupo-Tutor'
        verbose_name_plural = 'Grupos-Tutores'
        unique_together = ('group_name', 'semester')
        constraints = [
            models.UniqueConstraint(fields=['teacher'], name='unique_teacher_per_group')
        ]

    def clean(self):
        # Verificar unicidad de group_name y semester
        if Group.objects.filter(group_name=self.group_name, semester=self.semester).exclude(id=self.id).exists():
            raise ValidationError('El grupo y semestre ya existen.')

        # Verificar que el teacher no esté asignado a otro grupo
        if Group.objects.filter(teacher=self.teacher).exclude(id=self.id).exists():
            raise ValidationError('Este tutor ya está asignado a otro grupo.')

    def save(self, *args, **kwargs):
        self.clean()  # Asegurar que las validaciones se ejecuten al guardar
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.group_name} Tutor: {self.teacher.username}"
    
    
class StudentGroup(models.Model):
    """
    Modelo para representar la asignación de estudiantes a grupos.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante", limit_choices_to={'user_type': 'Estudiante'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Grupo")

    class Meta:
        verbose_name = 'Estudiante-Grupo'
        verbose_name_plural = 'Estudiantes-Grupos'
        unique_together = ('student', 'group')  # Añade la restricción de unicidad

    def __str__(self) -> str:
        return f"{self.student.username} en Grupo: {self.group.group_name}"

class StudentSubject(models.Model):
    """
    Modelo para representar la asignación de materias a estudiantes.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante", limit_choices_to={'user_type': 'Estudiante'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Materia")

    class Meta:
        verbose_name = 'Estudiante-Materia'
        verbose_name_plural = 'Estudiantes-Materias'
        unique_together = ('student', 'subject')  # Evita asignaciones duplicadas

    def __str__(self) -> str:
        return f"{self.student.username} - {self.subject.subject_name}"

class Grade(models.Model):
    """
    Modelo para representar las calificaciones de los estudiantes.
    Calcula la calificación final como el promedio de cuatro parciales.
    """
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Docente", limit_choices_to={'user_type': 'Docente'})
    student_subject = models.ForeignKey(StudentSubject, on_delete=models.CASCADE, verbose_name="Estudiante y Materia")
    semester_taken = models.IntegerField(verbose_name="Semestre Tomado", default=1)
    parcial_1 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    parcial_2 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    parcial_3 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    parcial_4 = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)

    @property
    def final(self):
        """
        Calcula la calificación final como el promedio de los parciales.
        """
        return (self.parcial_1 + self.parcial_2 + self.parcial_3 + self.parcial_4) / 4

    def save(self, *args, **kwargs):
        if self.semester_taken is None:
            raise ValidationError("El campo 'semester_taken' no puede ser nulo.")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ('teacher', 'student_subject', 'semester_taken')

    def __str__(self) -> str:
        return f"{self.student_subject.student.username} - {self.student_subject.subject.subject_name}: Calificación Final = {self.final} (Semestre: {self.semester_taken})"
class ClassSession(models.Model):
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.CASCADE, verbose_name="Docente y Materia")
    date = models.DateField(verbose_name="Fecha")
    
    class Meta:
        verbose_name = 'Sesión de Clase'
        verbose_name_plural = 'Sesiones de Clase'
    
    def __str__(self):
        return f"Sesión para {self.teacher_subject} el {self.date}"
    
class Attendance(models.Model):
    class_session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, verbose_name="Sesión de Clase")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante", limit_choices_to={'user_type': 'Estudiante'})
    status = models.CharField(max_length=8, choices=[('Presente', 'Presente'), ('Ausente', 'Ausente')], default='Presente', verbose_name="Estado")
    
    class Meta:
        unique_together = ('class_session', 'student')
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
    
    def __str__(self):
        return f"{self.student.username} - {self.status} en {self.class_session}"

class TutoringSession(models.Model):
    tutor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutoring_sessions',
        limit_choices_to={'user_type': 'Docente'}
    )
    date = models.DateField(verbose_name="Fecha")
    is_group = models.BooleanField(default=False, verbose_name="Es grupo")

    class Meta:
        unique_together = ('tutor', 'date', 'is_group')

    def clean(self):
        if self.is_group:
            existing_sessions = TutoringSession.objects.filter(
                tutor=self.tutor, date=self.date, is_group=True
            )
            if existing_sessions.exists():
                raise ValidationError('Ya existe una sesión grupal para este día.')

    def __str__(self):
        session_type = "Grupo" if self.is_group else "Individual"
        return f"{self.tutor.nombrecompleto()} - {self.date} ({session_type})"

class TutoringAttendance(models.Model):
    session = models.ForeignKey(TutoringSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Estudiante", limit_choices_to={'user_type': 'Estudiante'})
    is_present = models.BooleanField(default=True, verbose_name="Presente")

    def save(self, *args, **kwargs):
        print(f'Creando TutoringAttendance para {self.student} en sesión {self.session}')
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.nombrecompleto()} - {'Presente' if self.is_present else 'Ausente'}"
