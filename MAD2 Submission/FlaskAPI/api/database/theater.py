from extensions import db


class Theatre(db.Model):
    __tablename__ = 'theatre'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False)
    place = db.Column(db.String(40), nullable=False)
    location = db.Column(db.String(40), nullable = False)
    capacity = db.Column(db.Integer, nullable = False)
    shows = db.relationship("Show", backref = db.backref("theatre"))

    def json(self):
       
        return {'id' : self.id, 'name' : self.name, 'location' : self.location, 'capacity' : self.capacity}

