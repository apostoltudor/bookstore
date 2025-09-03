from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Author, Publisher, Category, Book, Review, Order, CustomUser, Promotii, Vizualizari

#Am schimbat numele panoului de administrare
admin.site.site_header = "Panoul Admin Bookstore"
admin.site.site_title = "Bookstore Admin"
admin.site.index_title = "Bine ați venit în Administrația Bookstore"

# Filtru pentru titlu (text)
class TitleFilter(admin.SimpleListFilter):
    title = _('Titlu')  # Titlul filtrului
    parameter_name = 'title'  # Numele parametrului URL
    # În admin ordonam după coloane cu aceste filtre laterale
    def lookups(self, request, model_admin):
        # Opțiuni de filtrare
        return (
            ('contains_a', _('Conține litera "A"')),
            ('contains_e', _('Conține litera "Y"')),
        )

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value() == 'contains_a':
            return queryset.filter(title__icontains='a')
        if self.value() == 'contains_y':
            return queryset.filter(title__icontains='y')


# Filtru pentru preț (număr)
class PriceFilter(admin.SimpleListFilter):
    title = _('Preț')  # Titlul filtrului
    parameter_name = 'price'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare
        return (
            ('lt_30', _('Mai mic de 30')),
            ('gte_30', _('Mai mare sau egal cu 30')),
        )

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value() == 'lt_30':
            return queryset.filter(price__lt=30)
        if self.value() == 'gte_30':
            return queryset.filter(price__gte=30)


# Filtru pentru data publicării (dată)
class PublicationDateFilter(admin.SimpleListFilter):
    title = _('Data Publicării')  # Titlul filtrului
    parameter_name = 'publication_date'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare
        return (
            ('this_year', _('Anul curent')),
            ('last_year', _('Anul trecut')),
        )

    def queryset(self, request, queryset):
        # Logica de filtrare
        from datetime import date
        if self.value() == 'this_year':
            return queryset.filter(publication_date__year=date.today().year)
        if self.value() == 'last_year':
            return queryset.filter(publication_date__year=date.today().year - 1)


# Filtru pentru stoc (număr)
class StockFilter(admin.SimpleListFilter):
    title = _('Stoc')  # Titlul filtrului
    parameter_name = 'stock'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare
        return (
            ('available', _('Disponibil')),
            ('out_of_stock', _('Stoc epuizat')),
        )

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value() == 'available':
            return queryset.filter(stock__gt=0)
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)


# Filtru pentru autor (relație)
class AuthorFilter(admin.SimpleListFilter):
    title = _('Autor')  # Titlul filtrului
    parameter_name = 'author'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare bazate pe autori existenți
        from .models import Author
        authors = Author.objects.all()
        return [(author.id, author.name) for author in authors]

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value():
            return queryset.filter(author_id=self.value())


# Filtru pentru editura (relație)
class PublisherFilter(admin.SimpleListFilter):
    title = _('Editura')  # Titlul filtrului
    parameter_name = 'publisher'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare bazate pe edituri existente
        from .models import Publisher
        publishers = Publisher.objects.all()
        return [(publisher.id, publisher.name) for publisher in publishers]

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value():
            return queryset.filter(publisher_id=self.value())


# Filtru pentru categorii (relație many-to-many)
class CategoryFilter(admin.SimpleListFilter):
    title = _('Categorie')  # Titlul filtrului
    parameter_name = 'category'  # Numele parametrului URL

    def lookups(self, request, model_admin):
        # Opțiuni de filtrare bazate pe categorii existente
        from .models import Category
        categories = Category.objects.all()
        return [(category.id, category.name) for category in categories]

    def queryset(self, request, queryset):
        # Logica de filtrare
        if self.value():
            return queryset.filter(categories__id=self.value())

#Înregistrează modelele în admin
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['title', 'author__name', 'publisher__name']  # Caută după titlu, nume autor și nume editura
    list_display = ['title', 'author', 'publisher', 'price', 'publication_date', 'stock'] #Am schimbat ordinea afișării câmpurilor
    # Filtre laterale
    list_filter = [
        TitleFilter,
        PriceFilter,
        PublicationDateFilter,
        StockFilter,
        AuthorFilter,
        PublisherFilter,
        CategoryFilter,
    ]    # Reordonare
    fields = ['title', 'author', 'publisher', 'categories', 'description', 'price', 'publication_date', 'cover_image', 'stock']
    verbose_name = 'Carte'  # Titlu singular
    verbose_name_plural = 'Cărți'  # Titlu plural
    #qset colectie de obiecte din model.obj
    list_per_page = 10  #Afișează doar 10 cărți pe pagină

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['name', 'bio']  # Caută după nume și biografie
    verbose_name = 'Scriitor'  # Titlu singular
    verbose_name_plural = 'Scriitori'  # Titlu plural

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['name', 'address']  # Caută după nume și adresă
    verbose_name = 'Editură'  # Titlu singular
    verbose_name_plural = 'Edituri'  # Titlu plural

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['name']  # Caută după nume
    verbose_name = 'Categorie'  # Titlu singular
    verbose_name_plural = 'Categorii'  # Titlu plural

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['book__title', 'text']  # Caută după titlul cărții și textul recenziei
    verbose_name = 'Recenzie'  # Titlu singular
    verbose_name_plural = 'Recenzii'  # Titlu plural

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Câmpuri de căutare
    search_fields = ['book__title', 'status']  #Caută după ce e mai relevant
    # 2 secțiuni pentru câmpuri
    fieldsets = [
        ('Informații de Bază', {
            'fields': ['book', 'quantity'],
            'description': 'Detalii de bază despre comandă.',
        }),
        ('Date Suplimentare', {
            'fields': ['status'],  # Excludem `order_date` din câmpurile editabile
            'description': 'Status comandă.',
            'classes': ['collapse'],  # Opțional: permite colapsarea secțiunii
        }),
    ]
    readonly_fields = ('order_date',)  # Adăugăm `order_date` ca câmp doar pentru citire
    list_display = ('id', 'book', 'quantity', 'order_date', 'status')  # Păstrăm `order_date` în listă pentru vizualizare
    #Am schimbat numele cu verbose_name
    verbose_name = 'Comandă'  # Titlu singular
    verbose_name_plural = 'Comenzi'  # Titlu plural
    
admin.site.register(CustomUser)  
admin.site.register(Promotii)
admin.site.register(Vizualizari)


