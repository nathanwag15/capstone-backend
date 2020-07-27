from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_heroku import Heroku
import io
import os




app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://tnxazjsczyqfck:de88e14b81c323fff046f60e99fad1e541ee947033d4d2be2d995e4fc9b2cef0@ec2-52-201-55-4.compute-1.amazonaws.com:5432/dblkq8te01snpp"



db = SQLAlchemy(app)
ma = Marshmallow(app)

heroku = Heroku(app)
CORS(app)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(), nullable=False)
    lat = db.Column(db.Integer, nullable=False)
    lon = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, location, lat, lon, user_id):
        self.location = location
        self.lat = lat
        self.lon = lon
        self.user_id = user_id

class LocationSchema(ma.Schema):
    class Meta:
        fields = ("id", "location", "lat", "lon", "user_id")

location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)


class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    files = db.relationship("Location", cascade="all,delete", backref="user", lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class userSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password")

user_schema = userSchema()
users_schema = userSchema(many=True)


@app.route("/location/add", methods=["POST"])
def add_file():
    location = request.form.get("location")
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    username = request.form.get("username")

    user_id = db.session.query(user.id).filter(user.username == username).first()

    new_location = Location(location, lat, lon, user_id[0])
    db.session.add(new_location)
    db.session.commit()

    return jsonify("Location added successfully")

@app.route("/location/get/data", methods=["GET"])
def get_location_data():
    location_data = db.session.query(Location).all()
    return jsonify(locations_schema.dump(location_data))

@app.route("/location/get/data/<username>", methods=["GET"])
def get_location_data_by_username(username):
    user_id = db.session.query(user.id).filter(user.username == username).first()[0]
    location_data = db.session.query(Location).filter(Location.user_id == user_id).all()
    return jsonify(locations_schema.dump(location_data))



@app.route("/location/delete/<id>", methods=["DELETE"])
def delete_location(id):
    location_data = db.session.query(Location).filter(Location.id == id).first()
    db.session.delete(location_data)
    db.session.commit()
    return jsonify("Location Deleted Successfully")


@app.route("/user/create", methods=["POST"])
def create_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    username_check = db.session.query(user.username).filter(user.username == username).first()
    if username_check is not None:
        return jsonify("Username Taken")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = user(username, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify("User Created Successfully")

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/user/get/<id>", methods=["GET"])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(User))

@app.route("/user/verification", methods=["POST"])
def verify_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    stored_password = db.session.query(user.password).filter(user.username == username).first()

    if stored_password is None:
        return jsonify("User NOT Verified")

    valid_password_check = bcrypt.check_password_hash(stored_password[0], password)

    if valid_password_check == False:
        return jsonify("User NOT Verified")

    return jsonify("User Verified")



if __name__ == "__main__":
    app.run(debug=True)