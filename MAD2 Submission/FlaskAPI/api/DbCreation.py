from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' 
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Theatre(db.Model):
    __tablename__ = 'theatre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    place = db.Column(db.String(40), nullable=False)
    location = db.Column(db.String(40), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    tags = db.Column(db.String(40))
    ticketPrice = db.Column(db.Integer, nullable=False)
    timing = db.Column(db.String(40),nullable = False)
    theatreID = db.Column(db.Integer, db.ForeignKey('theatre.id'))

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    noofTicket = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable = False)
    date_created = db.Column(db.Date, default=datetime.date.today, nullable=False)
  


    def json(self):
        return {'id' : self.id, 'userid' : self.user_id, 'showid':self.show_id ,'rating' : self.rating, 'noofTicket' : self.noofTicket, 'amount' : self.amount, 'date_created' : self.date_created}



@app.route('/api/users', methods=['GET'])
def get_all_users():
    # Retrieve all users from the database
    new_user = User(email="Admin1@gmail.com", password="Admin", is_admin=True)
    db.session.add(new_user)
    db.session.commit()

    users = User.query.all()

    data = [{'id': user.id, 'email': user.email} for user in users]
    print(data)
    return jsonify(data), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = User.query.get(user_id)

    if user:
        return jsonify({'id': user.id, 'email': user.email}), 200
    else:
        return jsonify({'message': 'User not found.'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
   
    app.run()

