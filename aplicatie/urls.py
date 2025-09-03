from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Pagina principală
    path('books/', views.book_list, name='book_list'),
    path('books/create/', views.create_book, name='create_book'),
    path('contact/', views.contact, name='contact'),
    path('success/', views.success, name='success'),
    path('register/', views.register, name='register'),  # Rută pentru înregistrare
    path('login/', views.login_view, name='login'),  # Rută pentru login
    path('logout/', views.logout_view, name='logout'),  # Rută pentru logout
    path('profile/', views.profile, name='profile'),  # Rută pentru profil
    path('change-password/', views.change_password, name='change_password'),  # Rută pentru schimbarea parolei
    path('promotii/', views.promotii, name='promotii'),  # Rută pentru crearea promoțiilor
    path('user-data-with-confirmation/', views.user_data_with_confirmation, name='user_data_with_confirmation'),  # Noua rută
    # Pagini detaliu pentru fiecare model
    path('author/<int:pk>/', views.author_detail, name='author_detail'),
    path('publisher/<int:pk>/', views.publisher_detail, name='publisher_detail'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),  # Adăugat pentru detalii despre cărți
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('user/<int:pk>/', views.user_detail, name='user_detail'),
    # Rută pentru confirmarea e-mailului
    path('confirma_mail/<str:cod>/', views.confirm_email, name='confirm_email'),
]
