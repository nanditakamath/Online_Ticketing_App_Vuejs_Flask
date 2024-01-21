from database import User, Theatre, Ticket, Show
from extensions import db
from sqlalchemy import func


def get_theatre_status(theatre_id: int):
    row = db.session.query(
        Theatre.name.label('theatre_name'),
        func.count(Show.id).label('number_of_shows'),
        func.count(Ticket.id).label('number_of_bookings'),
        func.avg(Ticket.rating).label('average_rating')
    ).join(Show, Show.theatreID == Theatre.id)\
    .join(Ticket, Ticket.show_id == Show.id)\
    .filter(Theatre.id == theatre_id)\
    .group_by(Theatre.name)\
    .first()

    return {
        'name': row.theatre_name,
        'number_of_shows': row.number_of_shows,
        'number_of_bookings': row.number_of_bookings,
        'average_rating': row.average_rating 
    }

    
