from flask import render_template
import os

from database import User, Ticket, Show, Theatre
from extensions import db

from smtplib import SMTP 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_mail(to_email, from_email, bodyContent):
    to_email = to_email
    from_email = from_email
    subject = 'Your monthly report'
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email

    message.attach(MIMEText(bodyContent, "html"))
    msgBody = message.as_string()

    server = SMTP('smtp.gmail.com', 587)
    server.starttls()
    print(os.environ.get('EMAIL_PASSWORD'))
    print(from_email)
    server.login(from_email, os.environ.get('EMAIL_PASSWORD'))
    server.sendmail(from_email, to_email, msgBody)

    server.quit()


def generate_monthly_report():
    serialized_bookings = []
    users = User.query.all()
    for user in users:
        if user.is_admin:
            continue

        bookings = db.session.query(
            Ticket.date_created,
            Ticket.noofTicket,
            Ticket.amount,
            Ticket.rating,
            Show.name.label('show_name')
            ).join(Show, Show.id == Ticket.show_id).filter(Ticket.user_id == user.id).all()
        
        for booking in bookings:
            info = {
                'date': booking.date_created.strftime('%Y-%m-%d'),
                'noofTicket': booking.noofTicket,
                'show_name': booking.show_name,
                'amount': booking.amount,
                'rating': booking.rating
            }
            print(info)
            serialized_bookings.append(info)
    
        template = render_template('monthly_report_template.html', bookings=serialized_bookings)
        print(template)
