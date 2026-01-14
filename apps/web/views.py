from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from .forms import ContactRequestForm
from .models import ContactRequestImage


def home(request):
    return render(request, 'web/index.html')


def services(request):
    return render(request, 'web/services.html')


def projects(request):
    return render(request, 'web/projects.html')


def about_us(request):
    return render(request, 'web/about_us.html')


@require_http_methods(["GET", "POST"])
@csrf_protect
def contact_us(request):
    """
    Vista para manejar el formulario de contacto/solicitud de presupuesto.

    GET: Muestra el formulario vacío
    POST: Procesa el formulario, guarda los datos y las imágenes
    """
    if request.method == 'POST':
        form = ContactRequestForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Guardar la solicitud de contacto
                contact_request = form.save()

                # Guardar las imágenes si existen
                images = request.FILES.getlist('images')
                for image in images:
                    ContactRequestImage.objects.create(
                        contact_request=contact_request,
                        image=image
                    )

                # Mensaje de éxito
                messages.success(
                    request,
                    '¡Solicitud enviada correctamente! Nos pondremos en contacto contigo en menos de 24 horas.'
                )

                # Redireccionar para evitar reenvío al recargar (patrón POST-Redirect-GET)
                return redirect('contact_us')

            except Exception as e:
                # Si hay algún error al guardar
                messages.error(
                    request,
                    f'Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo.'
                )
        else:
            # Si el formulario tiene errores de validación
            messages.error(
                request,
                'Por favor, corrige los errores del formulario.'
            )
    else:
        # GET: Mostrar formulario vacío
        form = ContactRequestForm()

    return render(request, 'web/contact_us.html', {'form': form})