from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def browse(request):
    return render(request, 'browse.html')

def impressum(request):
    return render(request, 'impressum.html')
	
def kontakt(request):
    return render(request, 'kontakt.html')