from extensions import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    tickets = db.relationship('Ticket', backref=db.backref('user'))
    
    def json(self):
        return {'id' : self.id, 'email' : self.email, 'password' : self.password, 'is_admin' : self.is_admin}

