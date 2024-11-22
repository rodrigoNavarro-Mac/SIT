from .models import Group

def es_tutor(request):
    if request.user.is_authenticated:
        return {'es_tutor': Group.objects.filter(teacher=request.user).exists()}
    return {'es_tutor': False}
