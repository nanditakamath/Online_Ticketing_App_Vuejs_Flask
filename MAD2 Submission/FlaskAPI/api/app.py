from flask import Flask, make_response, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
from datetime import timedelta, date
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
#from report_html import send_reports_to_users
import datetime
import os

import csv

from celery import Celery, Task
import celeryconfig

# Local imports
from extensions import db
from config import config
from database import User, Theatre, Show, Ticket
from jobs.async_job import get_theatre_status


def celery_init(app: Flask):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app = Celery('background', task_cls=FlaskTask)
    celery_app.config_from_object(celeryconfig)
    celery_app.set_default()
    app.extensions['celery'] = celery_app

    return celery_app


app = Flask(__name__, template_folder='templates')

app.config.from_mapping(config)

db.init_app(app)

jwt = JWTManager(app)

TEMPLATE_DIR = 'Templates'
app.app_context().push()

# Bind celery to flask app context
celery_app = celery_init(app)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})  # Allow all origins for routes starting with /api/


# Function to check if the user is an admin
def is_admin(email):
    admin_emails = ["admin@gmail.com"]  # Add your admin emails here
    return email in admin_emails

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    claims = get_jwt()
    if claims['is_admin']:
        try :
            users = User.query.all()
            return make_response(jsonify([user.json() for user in users]), 200)
        except:
            return make_response(jsonify({'message': 'error getting users'}), 500)
    else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    is_admin_user = data.get('is_admin', False)

    # Check if the user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400
    # Create a new user (you should hash the password before storing it)
    new_user = User(email=email, password=password, is_admin=is_admin_user)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    

    # Check if the user exists and the password matches
    user = User.query.filter_by(email=email, password=password).first()
    print(user)

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate an access token for the authenticated user
    
    access_token = create_access_token(identity=email, additional_claims={'is_admin': user.is_admin})
    app.config["JWT_ACCESS_TOKEN_EXPIRES"]= timedelta(hours=1)
    return jsonify({"access_token": access_token}), 200


#ADD
#@app.route('/api/addTheatre', methods=['POST'])
@app.route('/api/theatre', methods=['POST'])
@jwt_required()
def addTheatre():
        claims = get_jwt()
        if claims['is_admin']:
            try:
                    data = request.get_json()
                    new_theatre = Theatre(name=data['name'],place=data['place'], location=data['location'], capacity = data['capacity'])
                    db.session.add(new_theatre)
                    db.session.commit()
                    return make_response(jsonify({'message': 'theatre created'}), 201)
            except:
                    return make_response(jsonify({'message': 'error creating theatre'}), 500)
        else: 
            return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403

#GET
#@app.route('/api/getTheatres', methods=['GET'])
@app.route('/api/theatres', methods=['GET'])
@jwt_required()
def getTheatres():
    try:
        theatres = Theatre.query.all()
        theater_list = []

        for theater in theatres:
            theater_json = theater.json()
            shows_details = theater.shows
            today_date = date.today()
            show_list = []

            for show_detail in shows_details:
                booking_count = Ticket.query.with_entities(db.func.sum(Ticket.noofTicket)).filter(
                    Ticket.show_id == show_detail.id,
                    Ticket.date_created == today_date
                ).scalar()
                if booking_count is None:
                    booking_count = 0
                data = show_detail.json()
                data["TicketAvailableCount"] = theater.capacity - booking_count
                show_list.append(data)

            theater_json['shows'] = show_list
            theater_list.append(theater_json)

        return make_response(jsonify(theater_list), 200)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors specifically
        print(e)  # Log the error for debugging
        return make_response(jsonify({'message': 'error getting theatres'}), 500)
    
#GET
#@app.route('/api/getTheatres', methods=['GET'])
@app.route('/api/locations', methods=['GET'])
@jwt_required()
def getTheatreLocations():
    try:
        theatres = Theatre.query.all()
        location_list = []

        for theater in theatres:
            location_list.append(theater.json()['location'])
            
        return make_response(jsonify(location_list), 200)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors specifically
        print(e)  # Log the error for debugging
        return make_response(jsonify({'message': 'error getting theatre locations'}), 500)    

#Search Theatres by location
@app.route('/api/theatres/<string:location>', methods=['GET'])
@jwt_required()
def getTheatresByLocation(location):
    try:
        theatres = Theatre.query.filter_by(location=location)
        theater_list = []

        for theater in theatres:
            theater_json = theater.json()
            shows_details = theater.shows
            today_date = date.today()
            show_list = []

            for show_detail in shows_details:
                booking_count = Ticket.query.with_entities(db.func.sum(Ticket.noofTicket)).filter(
                    Ticket.show_id == show_detail.id,
                    Ticket.date_created == today_date
                ).scalar()
                if booking_count is None:
                    booking_count = 0
                data = show_detail.json()
                data["TicketAvailableCount"] = theater.capacity - booking_count
                show_list.append(data)

            theater_json['shows'] = show_list
            theater_list.append(theater_json)

        return make_response(jsonify(theater_list), 200)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors specifically
        print(e)  # Log the error for debugging
        return make_response(jsonify({'message': 'error getting theatres'}), 500)
        
#GETBYID
#@app.route('/api/getTheatresById/<int:id>', methods=['GET'])
@app.route('/api/theatre/<int:id>', methods=['GET'])
@jwt_required()
def getTheatresById(id):
        try:
         
            theatre = Theatre.query.filter_by(id=id).first()
           
            return make_response(jsonify(theatre.json()), 200)
        except :
            return make_response(jsonify({'message': 'error getting theatre'}), 500)
      
#GETBYID
#@app.route('/api/getShowsThetureByID/<int:id>', methods=['GET'])
@app.route('/api/shows/<int:id>', methods=['GET'])
@jwt_required()
def getShowsThetureByID(id):
        try:
            result = Show.query.\
                    join(Theatre, Theatre.id == Show.theatreID).\
                    filter(Show.id==id).\
                    with_entities(Theatre, Show).\
                    first()
            TheatreResult, ShowResult = result
            today_date = datetime.date.today()
            booking_count = Ticket.query.with_entities(db.func.sum(Ticket.noofTicket)).filter(
                            Ticket.show_id == id,
                            Ticket.date_created == today_date
                        ).scalar()
    
            print(booking_count)
            if booking_count is None:
                booking_count = 0
            
            json_result=ShowResult.json()
            json_result["Theture"]=TheatreResult.json()
            json_result["TicketAVilableCount"]=TheatreResult.capacity-booking_count
           
            return make_response(jsonify(json_result), 200)
        except Exception as e:
            #print("An exception occurred:", e)
            #return make_response(jsonify(e), 500)
            return make_response(jsonify({'message': 'error getting theatres and Shows'}), 500)
        
#GET
@app.route('/api/shows/tags', methods=['GET'])
@jwt_required()
def getShowTags():
    try:
        shows = Show.query.all()
        tag_list = []

        for show in shows:
            tag_list.append(show.json()['tags'])
            
        return make_response(jsonify(tag_list), 200)
    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors specifically
        print(e)  # Log the error for debugging
        return make_response(jsonify({'message': 'error getting theatre locations'}), 500) 

#GetShowsByTag
@app.route('/api/shows/<string:tag>', methods=['GET'])
@jwt_required()
def getShowsByTag(tag):
        try:
            shows = Show.query.filter(Show.tags==tag)
            result = []
            for show in shows:
                result.append(show.json())
            return make_response(jsonify(result), 200)
        
        except Exception as e:
            print("An exception occurred:", e)
            #return make_response(jsonify(e), 500)
            return make_response(jsonify({'message': 'error getting shows by tag'}), 500)
        
#GetShowsByRating
@app.route('/api/shows/rating/<float:rating>', methods=['GET'])
@jwt_required()
def getShowsByRating(rating):
        try:
            shows = Show.query.filter(Show.rating >= rating)
            result = []
            for show in shows:
                result.append(show.json())
            return make_response(jsonify(result), 200)
        
        except Exception as e:
            print("An exception occurred:", e)
            #return make_response(jsonify(e), 500)
            return make_response(jsonify({'message': 'error getting shows by rating'}), 500)


#EDIT        
#@app.route('/api/editTheatre/<int:id>', methods=['PUT','POST'])
@app.route('/api/theatre/<int:id>', methods=['PUT'])
@jwt_required()
def editTheatres(id):
    claims = get_jwt()
    if claims['is_admin']:
        try:
            theatre = Theatre.query.filter_by(id=id).first()
            if theatre:
                data = request.get_json()
                theatre.name = data['name']
                theatre.place = data['place']
                theatre.location = data['location']
                theatre.capacity = data['capacity']
                db.session.commit()
                return make_response(jsonify({'message': 'theatre updated'}), 200)
            return make_response(jsonify({'message': 'theatre not found'}), 404)
        except:
            return make_response(jsonify({'message': 'error updating theatre'}), 500)
    else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403

#DELETE    
#@app.route('/api/deleteTheatre/<int:id>', methods=['POST'])
@app.route('/api/theatre/<int:id>', methods=['DELETE'])
@jwt_required()
def deleteTheatre(id):
   claims = get_jwt()
   if claims['is_admin']:
    try:
        theatre = Theatre.query.filter_by(id=id).first()
    
        if theatre:
            
            db.session.delete(theatre)
            db.session.commit()
            return make_response(jsonify({'message': 'theatre deleted'}), 200)
        return make_response(jsonify({'message': 'theatre not found'}), 404)
    except:
        return make_response(jsonify({'message': 'error deleting theatre'}), 500)
   else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403


#SHOWS APIS#

#ADD
#@app.route('/api/addShow', methods=['POST'])
@app.route('/api/show/<int:id>', methods=['POST'])
@jwt_required()
def addShow(id):
    claims = get_jwt()
    if claims['is_admin']:
        try:
            data = request.get_json()
            newShow = Show(name=data['name'],timing=data['timing'], rating=data['rating'], tags = data['tags'], ticketPrice = data['ticketPrice'], theatreID = data['theatreID'])
            db.session.add(newShow)
            db.session.commit()
            return make_response(jsonify({'message': 'show created'}), 201)
        except Exception as e:
            return make_response(jsonify({'message': f'error creating show, {e}'}), 500)
    else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403
 

#EDIT
#@app.route('/api/editShow/<int:id>', methods=['PUT','POST'])
@app.route('/api/show/<int:id>', methods=['PUT'])
@jwt_required()
def editShow(id):
    claims = get_jwt()
    if claims['is_admin']:
        try:
            show = Show.query.filter_by(id=id).first()
            if show:
                data = request.get_json()
                show.name = data['name']
                show.rating = data['rating']
                show.timing = data['timing']
                show.tags = data['tags']
                show.ticketPrice = data['ticketPrice']
                
                show.theatreID = data['theatreID']
                db.session.commit()
                return make_response(jsonify({'message': 'show updated'}), 200)
            return make_response(jsonify({'message': 'show not found'}), 404)
        except e:
            return make_response(jsonify({'message': 'error updating show'}), 500)  
    else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403
   

#DELETE
#@app.route('/api/deleteShow/<int:id>', methods=['POST'])
@app.route('/api/show/<int:id>', methods=['DELETE'])
@jwt_required()
def deleteShow(id):
    claims = get_jwt()
    if claims['is_admin']:
        try:
            show = Show.query.filter_by(id=id).first()

            if show:
                db.session.delete(show)
                db.session.commit()
                return make_response(jsonify({'message': 'show deleted'}), 200)
            return make_response(jsonify({'message': 'show not found'}), 404)
        except Exception as e :
            
            return make_response(jsonify({'message': 'Cannot Delete Show. Existing bookings already exist'}), 500)
    else:
        return jsonify({"message": "Access denied. You need admin privileges to access this route."}), 403


#@app.route('/api/getShowsById/<int:id>', methods=['GET'])
@app.route('/api/show/<int:id>', methods=['GET'])
@jwt_required()
def getShowsById(id):
        try:
            show = Show.query.filter_by(id=id).first()
           
            return make_response(jsonify(show.json()), 200)
        except :
            return make_response(jsonify({'message': 'error getting theatres'}), 500)




#GET ALL SHOWS FOR A THEATRE
#@app.route('/api/getShows/<int:theatreID>', methods=['GET'])
@app.route('/api/shows/<int:theatreID>', methods=['GET'])
@jwt_required()
def getShowsByTheatre(theatreID):
    try:
        shows = Show.query.filter_by(theatreID=theatreID)
        return make_response(jsonify([show.json() for show in shows]), 200)
    except e:
        return make_response(jsonify({'message': 'error getting theatres'}), 500)


#GETBYID
#@app.route('/api/shows/getShowsThetureByUserTicket', methods=['GET'])
@app.route('/api/user/shows', methods=['GET'])
@jwt_required()
def getShowsThetureByUserTicket():
        try:
            current_user_email = get_jwt_identity()
           
            current_user = User.query.filter_by(email=current_user_email).first()
            if not current_user:
                return jsonify({"message": "User not found"}), 404
            user_id=current_user.id
            showsList=[]
            booked_shows = Show.query.join(Ticket, Show.id == Ticket.show_id).filter(
                            Ticket.user_id == user_id).all()
            if not booked_shows:
                showsList=[]
            else:
                for show in booked_shows:
                    data=show.json()
                    theatre = Theatre.query.filter_by(id=show.theatreID).first()
                    data["theatureName"]=theatre.name
                    showsList.append(data)
          
            return make_response(jsonify(showsList), 200)
        except Exception as e:
            #print("An exception occurred:", e)
            #return make_response(jsonify(e), 500)
            return make_response(jsonify({'message': 'error getting theatres and Shows'}), 500)
        

#@app.route('/api/shows/bookTicket', methods=['POST'])
@app.route('/api/shows/book', methods=['POST'])
@jwt_required()
def book_ticket():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    show_id = data.get('show_id')
    noofTicket = data.get('noofTicket')
    amount = data.get('amount')

    # Check if the show exists
    show = Show.query.get(show_id)
    if not show:
        return jsonify({"message": "Show not found"}), 404

    # Create a new ticket for the current user and show
    current_user = User.query.filter_by(email=current_user_email).first()
    if not current_user:
        return jsonify({"message": "User not found"}), 404

    ticket = Ticket(user_id=current_user.id, show_id=show.id, noofTicket=noofTicket, amount=amount)
    db.session.add(ticket)
    db.session.commit()

    return jsonify({"message": f"Ticket booked for {show.name}"}), 201


def get_current_month_tickets():
    current_month = datetime.date.today().month
    current_year = datetime.date.today().year

    return Ticket.query.filter(
        db.extract('month', Ticket.date_created) == current_month,
        db.extract('year', Ticket.date_created) == current_year
    ).all()
#GET ALL SHOWS
@app.route('/api/shows', methods=['GET'])
def get_shows():
    try:
        shows = Show.query.all()
        show_list = [{'id': show.id, 'name': show.name} for show in shows]
        return jsonify(show_list), 200
    except:
        return jsonify({'message': 'Error fetching shows'}), 500

@app.route('/api/generate_summary_report_0', methods=['GET'])
#@jwt_required()
def generate_summary_report():
    try:
        theaters = Theatre.query.all()
        print("Check1")

        summary_data = []
        current_month_tickets = get_current_month_tickets()

        for theater in theaters:
            theater_data = {'theater_name': theater.name, 'shows': []}

            for show in theater.shows:
                show_tickets = [ticket for ticket in current_month_tickets if ticket.show_id == show.id]
                bookings = len(show_tickets)
                if bookings > 0:
                    average_rating = sum(ticket.rating for ticket in show_tickets) / bookings
                else:
                    average_rating = 0

                theater_data['shows'].append({
                    'show_name': show.name,
                    'bookings': bookings,
                    'average_rating': average_rating
                })

            summary_data.append(theater_data)
            print(summary_data)
    except Exception as e:
            print(e)

@app.route('/api/generate_summary_report', methods=['GET'])
# @jwt_required()
def gen_summary_report_test():
    try:
        html_content = send_reports_to_users()  # Call the function with the user's email

        return jsonify({'html_content': html_content}), 200

    except Exception as e:
        print('Exception')
        print(e)
        return jsonify({'error': 'An error occurred'}), 500

    return make_response(jsonify(summary_data), 200)


#@app.route('/api/shows/bookTicketRating', methods=['POST','PUT'])
@app.route('/api/shows/rating', methods=['PUT'])
@jwt_required()
def bookTicketRating():
    current_user_email = get_jwt_identity()
    data = request.get_json()
    show_id = data.get('show_id')
    theatureId = data.get('theatureId')
    rating = data.get('rating')  
    current_user = User.query.filter_by(email=current_user_email).first()
    if not current_user:
        return jsonify({"message": "User not found"}), 404
    tickets_to_update = Ticket.query.filter_by(user_id=current_user.id,show_id=show_id).all()
    if not tickets_to_update:
        return jsonify({"message": f"Booking Ticket found for User ID {current_user.id} and Show ID {show_id}"}), 201
    else:

        for ticket in tickets_to_update:
            ticket.rating = rating

        # Commit the changes to the database to persist the updated ratings
        db.session.commit()


    return jsonify({"message": f"Rating Updated Sucessfully"}), 201


@app.route('/api/export_csv/<int:theatre_id>', methods=['GET'])
def export_csv(theatre_id):
    theatre = Theatre.query.get(theatre_id)

    if not theatre:
        return "Theatre not found", 404

    shows = Show.query.filter_by(theatreID=theatre_id).all()

    if not shows:
        return "No shows found for this theatre", 404

    csv_data = []
    for show in shows:
        csv_data.append([show.name, show.ticketPrice, show.rating])  # Add more data as needed

    # Prepare CSV file
    csv_filename = f"{theatre.name}_shows.csv"
    csv_filepath = os.path.join("csv_exports", csv_filename)  # Modify this path based on your setup

    # Write CSV data to the file
    with open(csv_filepath, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Show Name', 'Ticket Price', 'Rating'])  # CSV header
        writer.writerows(csv_data)

    # Return a response to notify the user
    return f"CSV file '{csv_filename}' has been saved."


@celery_app.task(name='async_job')
def run_async_job(theatre_id):
    return get_theatre_status(theatre_id=theatre_id)


def export_to_csv(data_dict: dict):
    with open('output.csv', 'w') as f:
        header = data_dict.keys()
        header_line = ','.join(header) + '\n'
        f.write(header_line)

        values = data_dict.values()
        line = ''
        for val in values:
            line = line + str(val) + ','
        f.write(line.strip(','))


#@app.route('/api/theatreStatus', methods=['POST'])
@app.route('/api/theatre/status', methods=['POST'])
def get_status():
    data = request.json
    task_id = data['taskId']

    if not task_id:
        theatre_id = data['theatreId']
        theatre = Theatre.query.get(theatre_id)
        if not theatre:
            return {'error': f'Theatre with id {theatre_id} not found'}, 404
        
        task_id = run_async_job.delay(theatre_id)
        return {'message': f'Job with task id {task_id} is in progress'}
 
    result = celery_app.AsyncResult(task_id)

    if result.status == 'SUCCESS':
        status = result.get()
        export_to_csv(status)
        return {'status': 'SUCCESS', 'taskId': task_id}
    else:
        return {'status': result.status, 'taskId': task_id}


@app.route('/api/download')
def download_csv():
    return send_file('output.csv', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True,use_reloader=False)


