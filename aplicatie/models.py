from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid  # Pentru generarea codului aleatoriu

# Model pentru Autor
class Author(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume Autor")  # CharField
    bio = models.TextField(verbose_name="Biografie", blank=True, null=True)  # TextField
    birth_date = models.DateField(verbose_name="Data Nașterii", blank=True, null=True)  # DateField

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autori"


# Model pentru Editura
class Publisher(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume Editură")  # CharField
    address = models.TextField(verbose_name="Adresă", blank=True, null=True)  # TextField
    website = models.URLField(verbose_name="Website", blank=True, null=True)  # URLField

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Editura"
        verbose_name_plural = "Edituri"


# Model pentru Categorie
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume Categorie")  # CharField
    description = models.TextField(verbose_name="Descriere", blank=True, null=True)  # TextField

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"


# Model pentru Carte
class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titlu")  # CharField
    description = models.TextField(verbose_name="Descriere", blank=True, null=True)  # TextField
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Preț")  # DecimalField
    publication_date = models.DateField(verbose_name="Data Publicării", blank=True, null=True)  # DateField
    cover_image = models.ImageField(upload_to='covers/', verbose_name="Copertă", blank=True, null=True)  # ImageField
    stock = models.IntegerField(verbose_name="Număr de cărți", default=0)  # IntegerField, redenumit pentru claritate
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creării")  # Adăugat pentru raport

    # Relații
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books', verbose_name="Autor")  # One-to-Many
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, related_name='books', verbose_name="Editura")  # One-to-Many
    categories = models.ManyToManyField(Category, related_name='books', verbose_name="Categorii")  # Many-to-Many

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Carte"
        verbose_name_plural = "Cărți"


# Model pentru Recenzie
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Carte")  # One-to-Many
    text = models.TextField(verbose_name="Text Recenzie")  # TextField
    rating = models.IntegerField(verbose_name="Rating", choices=[(i, i) for i in range(1, 6)])  # IntegerField cu choices
    date = models.DateTimeField(auto_now_add=True, verbose_name="Data Recenzie")  # DateTimeField
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creării")  # Adăugat pentru raport

    def __str__(self):
        return f"Recenzie pentru {self.book.title}"

    class Meta:
        verbose_name = "Recenzie"
        verbose_name_plural = "Recenzii"


# Model pentru Comandă
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'În așteptare'),
        ('SHIPPED', 'Expediat'),
        ('CANCELED', 'Anulat'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='orders', verbose_name="Carte")  # One-to-Many
    quantity = models.IntegerField(verbose_name="Cantitate")  # IntegerField
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Data Comenzii")  # DateTimeField
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")  # CharField cu choices
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creării")  # Adăugat pentru raport

    def __str__(self):
        return f"Comandă #{self.id} pentru {self.book.title}"

    class Meta:
        verbose_name = "Comandă"
        verbose_name_plural = "Comenzi"


# Model personalizat pentru utilizatori
class CustomUser(AbstractUser):
    favorite_genre = models.CharField(max_length=100, verbose_name="Gen literar preferat", blank=True)
    birth_date = models.DateField(verbose_name="Data nașterii", blank=True, null=True)
    phone_number = models.CharField(max_length=20, verbose_name="Număr de telefon", blank=True)
    address = models.TextField(verbose_name="Adresă", blank=True)
    reading_frequency = models.CharField(
        max_length=50,
        verbose_name="Frecvența lecturii",
        choices=[
            ('daily', 'Zilnic'),
            ('weekly', 'Săptămânal'),
            ('monthly', 'Lunar'),
            ('rarely', 'Rareori'),
        ],
        default='weekly'
    )
    cod = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cod de confirmare")  # Folosit pentru confirmarea e-mailului
    email_confirmat = models.BooleanField(default=False, verbose_name="E-mail confirmat")  # Folosit, nenul, implicit fals

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Utilizator"
        verbose_name_plural = "Utilizatori"


# Model pentru Vizualizări
class Vizualizari(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Utilizator")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Produs")
    date_viewed = models.DateTimeField(auto_now_add=True, verbose_name="Data vizualizării")

    class Meta:
        verbose_name = "Vizualizare"
        verbose_name_plural = "Vizualizări"
        ordering = ['-date_viewed']  # Ordonează după data descrescător pentru a obține cele mai recente vizualizări

    def save(self, *args, **kwargs):
        # Verifică dacă există mai mult de 5 vizualizări pentru același utilizator
        user_visualizations = Vizualizari.objects.filter(user=self.user).order_by('date_viewed')
        if user_visualizations.count() >= 5:
            # Șterge cea mai veche vizualizare
            oldest_visualization = user_visualizations.first()
            oldest_visualization.delete()
        super().save(*args, **kwargs)


# Model pentru Promoții
class Promotii(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nume promoție")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Data creării")
    date_expiry = models.DateTimeField(verbose_name="Data expirării")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Procent reducere", default=0)
    description = models.TextField(verbose_name="Descriere", blank=True, null=True)
    categories = models.ManyToManyField(Category, verbose_name="Categorii", related_name='promotii')

    class Meta:
        verbose_name = "Promoție"
        verbose_name_plural = "Promoții"

    def __str__(self):
        return self.name