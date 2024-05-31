from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse

# Create your views here.
def home(request):
    if request.method == 'POST':
        return JsonResponse({'data' : 'success'})
    else:
        return render(request, "home.html")