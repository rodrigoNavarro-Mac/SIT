from django.core.exceptions import ValidationError
import re

# Validadores personalizados
def validate_username(value):
    if not any(char.isdigit() for char in value) or sum(char.isdigit() for char in value) < 4:
        raise ValidationError('El nombre de usuario debe contener al menos 4 números.')

def validate_no_numbers(value):
    if any(char.isdigit() for char in value):
        raise ValidationError('Este campo no puede contener números.')