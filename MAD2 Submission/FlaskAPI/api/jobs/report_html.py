import os
import datetime
from flask import Flask, request, jsonify, make_response
from jinja2 import FileSystemLoader, Environment
from extensions import db
from database import User, Ticket, Show, Theatre  # Import your models
from config import config 
import json
from flask_mail import Mail,Message

tapp = Flask(__name__)
tapp.config['MAIL_SERVER'] = ''
tapp.config['MAIL_PORT'] = 465
tapp.config['MAIL_USERNAME'] = ''
tapp.config['MAIL_PASSWORD'] =  ''
tapp.config['MAIL_USE_TLS'] = False
tapp.config['MAIL_USE_SSL'] = True  
mail = Mail(tapp)

def generate_summary_report(user_email):
    try:
        # user_email = request.args.get('user_email')  # Get the user's email from the request
        print(user_email)
        # Fetch the user's data based on the provided email
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        print('finding user tickets')
        # Fetch the user's tickets data
        user_tickets = Ticket.query.filter_by(user_id=user.id).all()

        summary_data = []

        for ticket in user_tickets:
            show = Show.query.get(ticket.show_id)
            theater = Theatre.query.get(show.theatreID)
            booking_price = show.ticketPrice * ticket.noofTicket

            # Calculate the average rating for the show
            #show_tickets = Ticket.query.filter_by(show_id=show.id).all()
            summary_data.append({
                'show_name': show.name,
                'theater_name': theater.name,
                'bookings': ticket.noofTicket,
                'price_per_ticket': show.ticketPrice,
                'total_cost': booking_price,
                'booking_date': ticket.date_created.strftime('%d-%m-%Y'),
                'average_rating': show.rating
            })
        print('generating html report')
        # Load the HTML template from a relative path
        template_loader = FileSystemLoader(searchpath='templates')  # Assuming the templates folder is in the same directory
        template_env = Environment(loader=template_loader)
        template = template_env.get_template("monthly_report_template.html")
        print('getting month and year')
        # Get the current month and year
        current_month = datetime.datetime.now().strftime('%B')
        current_year = datetime.datetime.now().year
        print(summary_data)
        # Render the HTML template with dynamic data
        rendered_template = template.render(user_email=user_email, month_name=current_month, year=current_year, summary_data=summary_data)
        print('writing report')
        with open('monthly_report.html', 'w') as html_file:
            html_file.write(rendered_template)
        return jsonify({'html': rendered_template})
        # return  200

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'An error occurred'}), 500

def send_reports_to_users():
        users = User.query.all()

        for user in users:
            # Generate the summary report for the user
            generate_summary_report(user.email)
            print('report html generated, sending email')
            subject = f"Monthly Entertainment Summary Report for {user.email}"
            print(subject)
            try:
                # Create the email message
                message = Message(
                    subject=subject,
                    body=subject,
                    sender='',
                    recipients=['']
                )
                with tapp.open_resource("../monthly_report.html") as fp:  
                    message.attach("monthly_report.html","application/html",fp.read())  
                
                print('message composed for sending')
                # Send the email
                mail.send(message)
                print(f"Report email sent to {user.email}")
            except Exception as e:
                print('Exception')
                print(type(e).__name__)