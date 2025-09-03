import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Book, Author, Publisher, Category, Review, Order, CustomUser, Vizualizari, Promotii
from .forms import BookFilterForm, BookForm, UserRegistrationForm, CustomLoginForm, ContactForm, PromotionForm  
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
import json
from datetime import date
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
import uuid
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django import forms

logger = logging.getLogger('django')

#Decorator personalizat pentru a restricționa accesul la utilizatorii staff
def require_staff_login(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied("Doar utilizatorii staff pot accesa această resursă.")
        return view_func(request, *args, **kwargs)
    return wrapper

def index(request):
    logger.debug("Accesare pagina principală - DEBUG 1: Utilizatorul a accesat index-ul.")
    
    # Mesaje de tip DEBUG (2 locații relevante, conform cerinței anterioare)
    messages.debug(request, "DEBUG: Verifică starea sesiunii utilizatorului la accesarea paginii principale.")
    
    return render(request, 'aplicatie/index.html')

def book_list(request):
    logger.info("Accesare lista de cărți - INFO 1: Utilizatorul a accesat lista de cărți.")
    
    # Mesaje de tip INFO (2 locații relevante, conform cerinței anterioare)
    messages.info(request, "INFO: Filtrele sunt disponibile pentru a restrânge rezultatele listei de cărți.")
    #Filtrele pentru modelul Book din forms.py
    form = BookFilterForm(request.GET or None)
    books = Book.objects.all()

    if form.is_valid():
        #Aplică filtrele doar dacă câmpurile sunt completate în formular cu if cleaned_data
        cleaned_data = form.cleaned_data
        if cleaned_data['title']:
            books = books.filter(title__icontains=cleaned_data['title'])
        if cleaned_data['author']:
            books = books.filter(author=cleaned_data['author'])
        if cleaned_data['publisher']:
            books = books.filter(publisher=cleaned_data['publisher'])
        if cleaned_data['category']:
            books = books.filter(categories=cleaned_data['category'])
        if cleaned_data['min_price']:
            books = books.filter(price__gte=cleaned_data['min_price'])
        if cleaned_data['max_price']:
            books = books.filter(price__lte=cleaned_data['max_price'])
        if cleaned_data['publication_date']:
            books = books.filter(publication_date=cleaned_data['publication_date'])
        if cleaned_data['stock'] is not None:  # Verificăm explicit dacă stock există
            books = books.filter(stock=cleaned_data['stock'])
    else:
        logger.warning("Accesare lista de cărți - WARNING 1: Formularul de filtrare nu este valid.")
        
        # Mesaje de tip WARNING (2 locații relevante, conform cerinței anterioare)
        messages.warning(request, "WARNING: Ați trimis formularul de contact de prea multe ori. Vă rugăm să așteptați sau să contactați suportul.")
    
    # Verifică dacă cererea este AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        logger.debug("Cerere AJAX primită pentru filtrarea cărților.")
        # Randează doar lista de cărți ca HTML și returnează ca JSON
        books_html = render(request, 'aplicatie/book_list_partial.html', {'books': books}).content.decode('utf-8')
        return JsonResponse({'books_html': books_html}, status=200)
    
    # Pentru cererile normale (non-AJAX), returnează pagina completă
    return render(request, 'aplicatie/book_list.html', {'form': form, 'books': books})

def contact(request):
    logger.error("Procesare formular contact - ERROR 1: Eroare potențială la validarea datelor.")
    try:
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                # Preprocesare date
                data_nasterii = form.cleaned_data['data_nasterii']
                today = datetime.today()
                age = today.year - data_nasterii.year - ((today.month, today.day) < (data_nasterii.month, data_nasterii.day))
                months = today.month - data_nasterii.month
                if months < 0:
                    months += 12
                varsta = f"{age} ani și {months} luni"

                # Preprocesare mesaj
                mesaj = form.cleaned_data['mesaj']
                mesaj = ' '.join(mesaj.split())  # Înlocuiește linii noi și spații multiple

                # Salvare date în fișier JSON
                data = {
                    'nume': form.cleaned_data['nume'],
                    'prenume': form.cleaned_data['prenume'],
                    'varsta': varsta,
                    'email': form.cleaned_data['email'],
                    'tip_mesaj': form.cleaned_data['tip_mesaj'],
                    'subiect': form.cleaned_data['subiect'],
                    'zile_asteptare': form.cleaned_data['zile_asteptare'],
                    'mesaj': mesaj,
                }

                # Creează folderul "mesaje" dacă nu există
                
                if request.session['contact_attempts'] > 3:  # Presupunem că 3 trimiteri consecutive sunt „prea multe”
                    # Mesaje de tip WARNING (2 locații relevante, conform cerinței anterioare)
                    messages.warning(request, "WARNING: Ați trimis formularul de contact de prea multe ori. Vă rugăm să așteptați sau să contactați suportul.")
                
                # Salvare fișierul JSON
                timestamp = int(datetime.timestamp(datetime.now()))
                filename = f'mesaje/mesaj_{timestamp}.json'
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)

                logger.critical("Procesare formular contact - CRITICAL 1: Eșec la scrierea în fișierul JSON.")
                
                # Mesaje de tip SUCCESS (2 locații relevante, conform cerinței anterioare)
                messages.success(request, "SUCCESS: Formularul de contact a fost trimis cu succes!")
                
                return redirect('success')  # Redirecționează către o pagină de succes
            else:
                logger.critical("Procesare formular contact - CRITICAL 2: Formular invalid, date incorecte.")
                
                # Mesaje de tip ERROR (2 locații relevante, conform cerinței anterioare)
                messages.error(request, "ERROR: Formularul de contact conține erori. Vă rugăm să verificați câmpurile.")
    except Exception as e:
        logger.error("Procesare formular contact - ERROR 2: Eroare neașteptată: {e}".format(e=e))

    form = ContactForm()  # Inițializează form pentru GET
    return render(request, 'aplicatie/contact.html', {'form': form})

def success(request):
    # Mesaje de tip INFO (2 locații relevante, conform cerinței anterioare)
    messages.info(request, "INFO: Ați fost redirecționat către pagina de succes după trimiterea mesajului.")
    
    return render(request, 'aplicatie/success.html')

@require_staff_login
@login_required
def create_book(request):
    logger.debug("Creare carte - DEBUG 1: Utilizatorul a accesat formularul de creare.")
    
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)  # Adăugat request.FILES pentru cover_image
        if form.is_valid():
            book = form.save()  # Salvează cartea cu stocul calculat
            
            # Mesaje de tip DEBUG (2 locații relevante, conform cerinței anterioare)
            messages.debug(request, "DEBUG: Procesul de creare a cărții a fost finalizat cu succes.")
            
            return redirect('book_list')  # Redirecționează către lista de cărți
    else:
        form = BookForm()
    
    return render(request, 'aplicatie/create_book.html', {'form': form})

def register(request):
    logger.info("Înregistrare utilizator - INFO 1: Utilizatorul a accesat formularul de înregistrare.")
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generează un cod aleatoriu unic
            user.cod = str(uuid.uuid4())  # Generează un UUID ca string
            user.email_confirmat = False  # Setează e-mailul ca neconfirmat implicit
            user.save()

            # Trimite e-mailul de confirmare
            subject = 'Confirmă-ți contul pe Bookstore'
            confirmation_link = request.build_absolute_uri(f'/confirma_mail/{user.cod}/')
            context = {
                'user': user,
                'confirmation_link': confirmation_link,
            }
            message = render_to_string('aplicatie/email_confirmation.html', context)
            try:
                send_mail(
                    subject,
                    '',  # Corpul textului simplu (nu e necesar, deoarece folosim HTML)
                    settings.DEFAULT_FROM_EMAIL,  # Adresa expeditorului (fictivă, conform cerinței)
                    [user.email],
                    html_message=message,  # Folosim HTML pentru template
                    fail_silently=True,  # Evită erori dacă e-mailul e configurat ca dummy
                )
                logger.info(f"E-mail de confirmare trimis către {user.email}.")
            except Exception as e:
                logger.error(f"Eroare la trimiterea e-mailului de confirmare: {e}")

            # Mesaje de tip SUCCESS (2 locații relevante, conform cerinței anterioare)
            messages.success(request, "SUCCESS: Înregistrarea dumneavoastră a fost realizată cu succes! Verificați e-mailul pentru confirmare.")
            
            return redirect('index')  # Redirecționează către pagina principală după înregistrare
        else:
            # Mesaje de tip ERROR (2 locații relevante, conform cerinței anterioare)
            messages.error(request, "ERROR: Datele introduse sunt invalide. Vă rugăm să completați corect toate câmpurile.")
    else:
        form = UserRegistrationForm()
    return render(request, 'aplicatie/register.html', {'form': form})

def login_view(request):
    logger.warning("Autentificare - WARNING 1: Tentativă de login cu date invalide.")
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.email_confirmat:
                    # Mesaje de tip ERROR (2 locații relevante, conform cerinței anterioare)
                    messages.error(request, "ERROR: Trebuie să confirmați e-mailul înainte de a vă loga. Verificați e-mailul pentru linkul de confirmare.")
                    return render(request, 'aplicatie/login.html', {'form': form})
                login(request, user)
                # Verifică dacă utilizatorul dorește să fie păstrat logat timp de o zi
                if form.cleaned_data['remember_me']:
                    request.session.set_expiry(86400)  # 24 ore (1 zi) în secunde
                else:
                    request.session.set_expiry(0)  # Sesiune până la închiderea browserului
                
                # Mesaje de tip SUCCESS (2 locații relevante, conform cerinței anterioare)
                messages.success(request, "SUCCESS: Autentificarea dumneavoastră a fost realizată cu succes!")
                
                if user.is_staff:
                    messages.debug(request, "DEBUG: Logarea pe pagina de administrare (admin) a fost finalizată cu succes pentru utilizatorul staff.")
                
                return redirect('user_data_with_confirmation')  # Redirecționează către noua pagină
            else:
                # Mesaje de tip ERROR (2 locații relevante, conform cerinței anterioare)
                messages.error(request, "ERROR: Datele de autentificare sunt incorecte. Vă rugăm să verificați username-ul și parola.")
    else:
        form = CustomLoginForm()
    return render(request, 'aplicatie/login.html', {'form': form})

@login_required
def user_data_with_confirmation(request):
    """Afișează datele utilizatorului și linkul de confirmare a e-mailului (dacă este necesar)."""
    user = request.user
    confirmation_link = None
    if not user.email_confirmat and user.cod:
        confirmation_link = request.build_absolute_uri(f'/confirma_mail/{user.cod}/')

    # Stochează datele utilizatorului în sesiune (pentru consistență cu profile)
    request.session['user_data'] = {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'favorite_genre': user.favorite_genre,
        'birth_date': user.birth_date.isoformat() if user.birth_date else None,
        'phone_number': user.phone_number,
        'address': user.address,
        'reading_frequency': user.reading_frequency,
    }
    
    # Mesaje de tip INFO (2 locații relevante, conform cerinței anterioare)
    messages.info(request, "INFO: Aici vă puteți vizualiza datele personale și confirma e-mailul, dacă este necesar.")
    
    if not user.email_confirmat:
        # Mesaje de tip WARNING (2 locații relevante, conform cerinței anterioare)
        messages.warning(request, "WARNING: Email-ul dumneavoastră nu este confirmat. Vă rugăm să îl confirmați pentru a evita restricții.")
    
    return render(request, 'aplicatie/user_data_with_confirmation.html', {'user': user, 'confirmation_link': confirmation_link})

@login_required
def profile(request):
    # Păstrăm profilul existent pentru compatibilitate, dar îl vom folosi mai puțin
    # Stochează datele utilizatorului în sesiune
    request.session['user_data'] = {
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'favorite_genre': request.user.favorite_genre,
        'birth_date': request.user.birth_date.isoformat() if request.user.birth_date else None,
        'phone_number': request.user.phone_number,
        'address': request.user.address,
        'reading_frequency': request.user.reading_frequency,
    }
    
    # Mesaje de tip INFO (2 locații relevante, conform cerinței anterioare)
    messages.info(request, "INFO: Aici vă puteți vizualiza datele personale.")
    
    if not request.user.email_confirmat:
        # Mesaje de tip WARNING (2 locații relevante, conform cerinței anterioare)
        messages.warning(request, "WARNING: Email-ul dumneavoastră nu este confirmat. Vă rugăm să îl confirmați pentru a evita restricții.")
    
    return render(request, 'aplicatie/profile.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('index')  # Redirecționează către pagina principală după logout

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if request.user.check_password(old_password):
            if new_password1 == new_password2:
                if len(new_password1) >= 8:  # Validare simplă pentru lungime minimă
                    request.user.set_password(new_password1)
                    request.user.save()
                    return redirect('user_data_with_confirmation')  # Redirecționează către noua pagină
                else:
                    return render(request, 'aplicatie/change_password.html', {'error': 'Parola nouă trebuie să aibă cel puțin 8 caractere.'})
            else:
                return render(request, 'aplicatie/change_password.html', {'error': 'Parolele noi nu coincid.'})
        else:
            return render(request, 'aplicatie/change_password.html', {'error': 'Parola veche este incorectă.'})
    return render(request, 'aplicatie/change_password.html')

# View-uri pentru paginile detaliu ale modelelor
def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, 'aplicatie/author_detail.html', {'author': author})

def publisher_detail(request, pk):
    publisher = get_object_or_404(Publisher, pk=pk)
    return render(request, 'aplicatie/publisher_detail.html', {'publisher': publisher})

def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, 'aplicatie/category_detail.html', {'category': category})

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    # Salvează vizualizarea în tabelul Vizualizari, dacă utilizatorul este autentificat
    if request.user.is_authenticated:
        Vizualizari.objects.get_or_create(
            user=request.user,
            book=book
        )
    return render(request, 'aplicatie/book_detail.html', {'book': book})

def review_detail(request, pk):
    review = get_object_or_404(Review, pk=pk)
    return render(request, 'aplicatie/review_detail.html', {'review': review})

def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'aplicatie/order_detail.html', {'order': order})

def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'aplicatie/user_detail.html', {'user': user})

def confirm_email(request, cod):
    """View pentru confirmarea e-mailului prin link-ul de confirmare."""
    try:
        user = CustomUser.objects.get(cod=cod)
        user.email_confirmat = True
        user.cod = None  # Șterge codul după confirmare pentru securitate
        user.save()
        logger.info(f"E-mail confirmat pentru utilizatorul {user.username}.")
        return render(request, 'aplicatie/email_confirmation_success.html', {'username': user.username})
    except CustomUser.DoesNotExist:
        logger.warning("Cod de confirmare invalid sau expirat.")
        messages.error(request, "Cod de confirmare invalid sau expirat. Vă rugăm să vă înregistrați din nou.")
        return redirect('index')

@login_required
@require_staff_login
def promotii(request):
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            promotion = form.save()
            # Găsește utilizatorii eligibili pentru promoții
            categories = promotion.categories.all()
            email_count = 0  # Contor pentru numărul de e-mailuri trimise
            
            for category in categories:
                # Găsește utilizatorii care au vizualizat cel puțin un produs din această categorie
                viewed_books = Vizualizari.objects.filter(book__categories=category).values('user').distinct()
                users = CustomUser.objects.filter(id__in=[v['user'] for v in viewed_books], email_confirmat=True)
                
                # Alege template-ul de e-mail în funcție de categorie
                if category.name == 'Poezie':
                    template_name = 'aplicatie/email_promotion_poetry.html'
                elif category.name == 'Ficțiune':
                    template_name = 'aplicatie/email_promotion_fiction.html'
                else:
                    continue  # Ignoră categoriile fără template

                for user in users:
                    context = {
                        'user': user,
                        'promotion': promotion,
                        'expiry_date': promotion.date_expiry,
                    }
                    # Subiect și mesaj implicite, bazate pe nume și categorie
                    subject = f"Promoție {promotion.name} - {category.name}"
                    html_message = render_to_string(template_name, context)
                    # Trimite e-mail individual folosind send_mail() cu suport HTML
                    try:
                        send_mail(
                            subject,
                            '',  # Corpul textului simplu (nu e necesar, deoarece folosim HTML)
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            html_message=html_message,  # Folosim HTML pentru template
                            fail_silently=True,  # Evită erori dacă e-mailul e configurat ca dummy
                        )
                        email_count += 1
                    except Exception as e:
                        logger.error(f"Eroare la trimiterea e-mailului pentru utilizatorul {user.email}: {e}")
            
            if email_count > 0:
                logger.info(f"Promoție {promotion.name} trimisă către {email_count} utilizatori.")
            
            messages.success(request, "Promoția a fost creată și e-mailurile au fost trimise cu succes!")
            return redirect('promotii')
    else:
        form = PromotionForm()
    
    return render(request, 'aplicatie/promotii.html', {'form': form})