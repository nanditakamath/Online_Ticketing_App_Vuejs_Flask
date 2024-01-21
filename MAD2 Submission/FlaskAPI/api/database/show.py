from extensions import db


class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False)
    rating = db.Column(db.Float, nullable = False)
    tags = db.Column(db.String(40))
    ticketPrice = db.Column(db.Integer, nullable = False)
    timing = db.Column(db.String(40),nullable = False)
    theatreID = db.Column(db.Integer, db.ForeignKey('theatre.id'))
    tickets = db.relationship('Ticket', backref=db.backref('show'))
   
    def json(self):
        return {'id' : self.id, 'name' : self.name, 'timing':self.timing ,'rating' : self.rating, 'tags' : self.tags, 'ticketPrice' : self.ticketPrice, 'theatre' : self.theatreID}

