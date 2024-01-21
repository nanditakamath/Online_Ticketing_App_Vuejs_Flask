# csv_export.py

import csv
import io
from flask import make_response
from database import Theatre, Show  

def export_csv(theatre_id):
    theatre = Theatre.query.get(theatre_id)

    if not theatre:
        return "Theatre not found", 404

    shows = Show.query.filter_by(theatreID=theatre_id).all()

    if not shows:
        return "No shows found for this theatre", 404

    csv_data = []
    for show in shows:
        total_bookings = sum(ticket.noofTicket for ticket in show.tickets)  # Calculate total bookings
        csv_data.append([show.name, show.ticketPrice, show.rating, total_bookings])  # Include total_bookings

    # Prepare CSV data in memory
    csv_stream = io.StringIO()
    csv_writer = csv.writer(csv_stream)
    csv_writer.writerow(['Show Name', 'Ticket Price', 'Rating', 'Total Bookings'])  # CSV header
    csv_writer.writerows(csv_data)

    # Create response with CSV data
    response = make_response(csv_stream.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename="{theatre.name}_shows.csv"'

    return response
