from django.core.management.base import BaseCommand
from aplicatie.models import CustomUser, Book, Order, Review
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import os
import logging
from django.core.mail import send_mass_mail
from django.conf import settings

logger = logging.getLogger('django')

class Command(BaseCommand):
    help = 'Scheduled tasks for the bookstore application'

    def clean_unconfirmed_users(self):
        #sterge utilizatorii care sunt inregistrați dar nu au e-mail confirmat, la fiecare 60 de minute.
        two_minutes_ago = timezone.now() - timedelta(minutes=2)  # doar 2 minute pentru testare
        unconfirmed_users = CustomUser.objects.filter(email_confirmat=False, date_joined__lte=two_minutes_ago)
        count = unconfirmed_users.count()
        unconfirmed_users.delete()
        logger.info(f"Șterse {count} utilizatori fără e-mail confirmat.")

    def send_newsletter(self):
        #Trimite un newsletter către toți utilizatorii mai vechi de 2 minute, în fiecare joi la 18:00.
        two_minutes_ago = timezone.now() - timedelta(minutes=2)  # folosim 2 minute pentru testare
        users = CustomUser.objects.filter(date_joined__lte=two_minutes_ago)
        
        messages = []
        newsletter_subject = 'Newsletter Bookstore - Oferte speciale!'
        newsletter_message = """
        Bună,

        Vă invităm să descoperiți ultimele noastre oferte și cărți noi pe Bookstore!
        Accesați site-ul nostru la http://127.0.0.1:8000 pentru mai multe detalii.

        Cu respect,
        Echipa Bookstore
        """
        
        for user in users:
            messages.append((
                newsletter_subject,
                newsletter_message,
                'no-reply@bookstore.example.com',
                [user.email],
            ))
        
        if messages:
            send_mass_mail(messages, fail_silently=True)
            logger.info(f"Newsletter trimis către {len(messages)} utilizatori.")
        else:
            logger.warning("Nu există utilizatori eligibili pentru newsletter.")

    def generate_activity_report(self):
        #Generează un raport zilnic cu numărul de utilizatori noi și acțiunile/erorile importante, salvat în fiecare duminică la 23:59.
        from datetime import date
        
        today = date.today()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
        
        # Număr de utilizatori noi (înregistrați astăzi)
        new_users_count = CustomUser.objects.filter(date_joined__range=(start_of_day, end_of_day)).count()
        
        # Acțiuni importante (ex. cărți create, comenzi plasate, recenzii adăugate)
        books_created = Book.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
        orders_placed = Order.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
        reviews_added = Review.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
        
        # Accesează fișierele de log folosind configurația din settings.LOGGING
        error_logs = settings.LOGGING['handlers']['error_file']['filename']
        critical_logs = settings.LOGGING['handlers']['critical_file']['filename']
        
        report_content = f"""
Raport de Activitate - {today}

1. Număr de utilizatori noi: {new_users_count}
2. Acțiuni importante:
   - Cărți create: {books_created}
   - Comenzi plasate: {orders_placed}
   - Recenzii adăugate: {reviews_added}
3. Erori și probleme:
   - Verificați fișierul de erori: {error_logs}
   - Verificați fișierul de erori critice: {critical_logs}

Generat automat de Bookstore.
        """
        
        report_path = settings.REPORTS_DIR / f'report_{today}.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Raport de activitate generat și salvat în {report_path}")