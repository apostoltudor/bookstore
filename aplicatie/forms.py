from django import forms
from .models import Author, Publisher, Category, Book, CustomUser, Promotii
from django.core.exceptions import ValidationError
import re
from datetime import date, datetime
import os
import json
from decimal import Decimal
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class BookFilterForm(forms.Form):
    title = forms.CharField(label='Titlu', required=False)
    author = forms.ModelChoiceField(
        label='Autor',
        queryset=Author.objects.all(),
        required=False,
        empty_label="Toți autorii"
    )
    publisher = forms.ModelChoiceField(
        label='Editură',
        queryset=Publisher.objects.all(),
        required=False,
        empty_label="Toate editurile"
    )
    category = forms.ModelChoiceField(
        label='Categorie',
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toate categoriile"
    )
    min_price = forms.DecimalField(
        label='Preț minim',
        required=False,
        min_value=0,
        decimal_places=2
    )
    max_price = forms.DecimalField(
        label='Preț maxim',
        required=False,
        min_value=0,
        decimal_places=2
    )
    publication_date = forms.DateField(
        label='Data publicării',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    stock = forms.IntegerField(
        label='Stoc',
        required=False,
        min_value=0
    )
    #Cum funcționează:
    # După ce fiecare câmp a fost validat individual, Django apelează clean().
    # În clean(), ai acces la toate datele deja validate în self.cleaned_data.
    # Poți face verificări între câmpuri și ridica erori dacă ceva nu e corect.
    def clean(self):
        cleaned_data = super().clean()   #folosită pentru validări care implică mai multe câmpuri în același timp.
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationError("Prețul minim nu poate fi mai mare decât prețul maxim.")
        
        return cleaned_data
#regex, sablon de cautare expresii reg
class ContactForm(forms.Form):
    # Câmpuri
    nume = forms.CharField(
        label="Nume",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Introduceți numele'})
    )
    prenume = forms.CharField(
        label="Prenume",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Introduceți prenumele'})
    )
    data_nasterii = forms.DateField(
        label="Data nașterii",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    email = forms.EmailField(
        label="E-mail",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Introduceți e-mailul'})
    )
    confirmare_email = forms.EmailField(
        label="Confirmare e-mail",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Confirmați e-mailul'})
    )
    tip_mesaj = forms.ChoiceField(
        label="Tip mesaj",
        choices=[
            ('reclamatie', 'Reclamație'),
            ('intrebare', 'Întrebare'),
            ('review', 'Review'),
            ('cerere', 'Cerere'),
            ('programare', 'Programare'),
        ],
        required=True
    )
    subiect = forms.CharField(
        label="Subiect",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Introduceți subiectul'})
    )
    zile_asteptare = forms.IntegerField(
        label="Minim zile așteptare",
        required=True,
        min_value=1
    )
    mesaj = forms.CharField(
        label="Mesaj",
        required=True,
        widget=forms.Textarea(attrs={'placeholder': 'Introduceți mesajul'})
    )

    # Validare pentru email și confirmare email
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        confirmare_email = cleaned_data.get('confirmare_email')

        if email and confirmare_email and email != confirmare_email:
            raise ValidationError("E-mailul și confirmarea e-mailului nu coincid.")

        return cleaned_data

    # Validare pentru data nașterii (utilizatorul trebuie să fie major)
    def clean_data_nasterii(self):
        data_nasterii = self.cleaned_data['data_nasterii']
        today = date.today()
        age = today.year - data_nasterii.year - ((today.month, today.day) < (data_nasterii.month, data_nasterii.day))

        if age < 18:
            raise ValidationError("Trebuie să aveți cel puțin 18 ani pentru a trimite un mesaj.")

        return data_nasterii

    # Validare pentru mesaj (între 5 și 100 de cuvinte, fără link-uri, semnătura corectă)
    def clean_mesaj(self):
        mesaj = self.cleaned_data['mesaj']

        # Verifică numărul de cuvinte cu regex #cu modulul de expresii regulate cautam cuv regulate
        words = re.findall(r'\b\w+\b', mesaj) #de forma \b limita de cuv si \w+ unu sau mai multe caractere
        if len(words) < 5 or len(words) > 100: #adica cautam cuvinte intregi
            raise ValidationError("Mesajul trebuie să conțină între 5 și 100 de cuvinte.")

        # Verifică dacă mesajul conține link-uri si cauta prima potrivire care incepe cu
        if re.search(r'https?://\S+', mesaj): #http(eventual si s) si mai are caractere dupa (\S+)
            raise ValidationError("Mesajul nu poate conține link-uri.")

        # Verifică semnătura (ultimul cuvânt trebuie să fie numele)
        nume = self.cleaned_data.get('nume')
        if words[-1].lower() != nume.lower():
            raise ValidationError("Mesajul trebuie să se termine cu numele dumneavoastră.")

        return mesaj

    # Validare comună pentru nume, prenume și subiect
    def validate_text(self, text, field_name):
        if not re.match(r'^[A-Z][a-zA-Z ]*$', text): #* 0 sau mai multe
            raise ValidationError(f"{field_name} trebuie să înceapă cu literă mare și să conțină doar litere și spații.")

    def clean_nume(self):
        nume = self.cleaned_data['nume']
        self.validate_text(nume, "Numele")
        return nume

    def clean_prenume(self):
        prenume = self.cleaned_data['prenume']
        if prenume:  # Prenumele este opțional
            self.validate_text(prenume, "Prenumele")
        return prenume

    def clean_subiect(self):
        subiect = self.cleaned_data['subiect']
        self.validate_text(subiect, "Subiectul")
        return subiect

class BookForm(forms.ModelForm):
    # Înlocuim câmpurile "Număr de cutii" și "Cărți per cutie" cu "Număr de cărți"
    book_quantity = forms.IntegerField(
        label='Număr de cărți',
        required=False,  # Nu este obligatoriu, implicit 0 dacă e gol
        min_value=0,
        help_text='Introduceți numărul de cărți disponibile. Dacă este lăsat gol, valoarea implicită va fi 0.'
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'publication_date', 'description', 'price', 'cover_image', 'book_quantity']
        labels = {
            'title': 'Titlul cărții',
            'author': 'Autor',
            'publication_date': 'Data publicării',
            'description': 'Descriere',
            'price': 'Preț',
            'cover_image': 'Copertă',
            'book_quantity': 'Număr de cărți'
        }
        error_messages = {
            'title': {
                'required': 'Vă rugăm să introduceți titlul cărții',
                'max_length': 'Titlul este prea lung'
            },
            'author': {
                'required': 'Vă rugăm să selectați autorul'
            },
            'publication_date': {
                'required': 'Vă rugăm să introduceți data publicării'
            }
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 3:
            raise ValidationError('Titlul trebuie să conțină cel puțin 3 caractere')
        if not title[0].isupper():
            raise ValidationError('Titlul trebuie să înceapă cu literă mare')
        return title

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise ValidationError('Prețul nu poate fi negativ')
        return price

    def clean_book_quantity(self):
        book_quantity = self.cleaned_data['book_quantity']
        if book_quantity is None:  # Dacă câmpul e gol, setăm implicit 0
            return 0
        return book_quantity

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Setăm stocul (stock) ca fiind egal cu book_quantity
        instance.stock = self.cleaned_data['book_quantity'] or 0
        
        if commit:
            instance.save()
        return instance
    
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="E-mail")
    first_name = forms.CharField(max_length=30, required=True, label="Prenume")
    last_name = forms.CharField(max_length=30, required=True, label="Nume")
    favorite_genre = forms.CharField(max_length=100, required=True, label="Gen literar preferat")
    birth_date = forms.DateField(required=True, label="Data nașterii", widget=forms.DateInput(attrs={'type': 'date'}))
    phone_number = forms.CharField(max_length=20, required=True, label="Număr de telefon")
    address = forms.CharField(max_length=200, required=True, label="Adresă")
    reading_frequency = forms.ChoiceField(
        choices=[
            ('daily', 'Zilnic'),
            ('weekly', 'Săptămânal'),
            ('monthly', 'Lunar'),
            ('rarely', 'Rareori'),
        ],
        required=True,
        label="Frecvența lecturii"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'favorite_genre', 'birth_date', 'phone_number', 'address', 'reading_frequency']

    def clean_favorite_genre(self):
        favorite_genre = self.cleaned_data['favorite_genre']
        if not favorite_genre[0].isupper():
            raise ValidationError('Genul literar preferat trebuie să înceapă cu literă mare.')
        if len(favorite_genre.split()) > 3:
            raise ValidationError('Genul literar preferat nu poate conține mai mult de 3 cuvinte.')
        return favorite_genre

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if not re.match(r'^\+?\d{10,15}$', phone_number):
        #daca nu se potriveste: :^ incep sir, + optional, intre 10/15 cifre
            raise ValidationError('Numărul de telefon trebuie să fie format din 10-15 cifre, eventual cu prefix (+).')
        return phone_number

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise ValidationError('Trebuie să aveți cel puțin 18 ani pentru a vă înregistra.')
        return birth_date

class CustomLoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        label="Păstrează-mă logat timp de o zi",
        widget=forms.CheckboxInput()
    )
    
class PromotionForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        label="Categorii pentru promoție",
        required=True,
        widget=forms.CheckboxSelectMultiple,
        initial=Category.objects.all()  # Implicit, toate categoriile sunt selectate
    )
    #Am modificat titlurile si numele câmpurilor
    class Meta:
        model = Promotii
        fields = ['name', 'discount_percentage', 'description', 'date_expiry', 'categories']  # Incluzând categories
        labels = {
            'name': 'Nume promoție',
            'discount_percentage': 'Procent reducere (%)',
            'description': 'Descriere',
            'date_expiry': 'Data expirării',
            'categories': 'Categorii pentru promoție'
        }
        widgets = {
            'date_expiry': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        discount_percentage = cleaned_data.get('discount_percentage')
        if discount_percentage is not None and (discount_percentage < 0 or discount_percentage > 100):
            raise ValidationError("Procentul de reducere trebuie să fie între 0 și 100.")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.date_created = datetime.now()
        if commit:
            instance.save()
            self.save_m2m()  # Salvează relația ManyToMany cu categoriile
        return instance