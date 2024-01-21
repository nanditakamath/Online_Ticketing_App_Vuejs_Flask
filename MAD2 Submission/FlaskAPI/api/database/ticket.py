from datetime import datetime, date

from extensions import db



class Ticket(db.Model):
    __tablename__ = 'ticket'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    noofTicket = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, default=0.0, nullable = False)
    date_created = db.Column(db.Date, default=date.today, nullable=False)
    

    def json(self):
        return {'id' : self.id, 'userid' : self.user_id, 'showid':self.show_id ,'rating' : self.rating, 'noofTicket' : self.noofTicket, 'amount' : self.amount, 'date_created' : self.date_created}
