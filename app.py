import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message


app = Flask(__name__)
basedir= os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ os.path.join(basedir, 'planet.db')
app.config['JWT_SECRET_KEY'] = 'super-secret' #change this to stronger one
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'dc8fd41bb5ba81'
app.config['MAIL_PASSWORD'] = '390bbc53f82d0a'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db= SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

#create database
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database Created..")

#drop database
@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Databae Dropped...')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if(test):
        return jsonify(message="Email Already Exists"), 409
    else:
        first_name=request.form['first_name']
        last_name =request.form['last_name']
        password  =request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User Created Successfully..."), 201

#database seeding
@app.cli.command('db_seed')
def db_seed():
    mecury = Planet(planet_name="Mecury",planet_type="Class D", home_star="Sol",mass=3.258e23, radius=1252, distance=38.293e23)
    venus  =  Planet(planet_name="Venus",planet_type="Class A", home_star="Sol",mass=3.223e99, radius=2352, distance=38.234e23)
    earth  =  Planet(planet_name="Earth",planet_type="Class M", home_star="Sun",mass=5.734e24, radius=6400, distance=38.293e3)

    db.session.add(mecury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        first_name='Michael',
        last_name="James",
        email='test@gmail.com',
        password='password'
    )

    db.session.add(test_user)
    db.session.commit()
    print('Databae Seeded Successfully...')

@app.route('/')
def hello_world():
    return jsonify(message="Welcome to Flask...")


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all();
    result = planets_schema.dump(planets_list)
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email= request.form['email']
        password =request.form['password']
    test =User.query.filter_by(email=email, password=password).first()
    if(test):
        access_token = create_access_token(identity=email)
        return jsonify(message="Login Successful...", access_token=access_token)
    else:
        return jsonify(message="Login Credentials do not match our records..."), 401

@app.route('/reset_password/<string:email>',methods=['GET'])
def reset_passowrd(email:str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg =Message('Your Solar Flair API Password is '+user.password,sender="admin@solarflair.com", recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to"+email)
    else:
        return jsonify(message="Your Credentials Does not exist..."), 401
    
@app.route('/add', methods=['POST'])
@jwt_required()
def add():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if(test):
        return jsonify(message="Planet Name Alredy Exist...")
    else:
        planet_type = request.form['planet_type']
        home_star  = request.form['home_star']
        mass        = float(request.form['mass'])
        radius      = float(request.form['radius'])
        distance    = float(request.form['distance'])

        new_planet = Planet(planet_name = planet_name, planet_type=planet_type, home_star = home_star, mass=mass, radius=radius, distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="Record Added Successfully..."), 201

@app.route('/update', methods=['PUT'])
@jwt_required()
def update():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if(planet):
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star   = request.form['home_star']
        planet.mass        = float(request.form['mass'])
        planet.radius      = float(request.form['radius'])
        planet.distance    = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="Planet Info Updatetd Successfull..."), 202
    else:
        return jsonify(message="Planee Does Not exist..."), 404

@app.route('/delete/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if(planet):
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="Planet Delted Successfully...."), 202
    else:
        return jsonify(message="The Planet Does not Exist..."),404
    
@app.route('/planet/<int:planet_id>',methods=['GET'])
def planet_detail(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if(planet):
        result = planet_schema.dump(planet)
        return jsonify(result), 200
    else:
        return jsonify(message="Planet Data does not exist..."),404

# for database models
class User(db.Model):
    __tablename__="users"
    id = Column(Integer, primary_key=True)
    first_name =Column(String)
    last_name  = Column(String)
    email      = Column(String, unique=True)
    password   = Column(String)

class Planet(db.Model):
    __tablename__="planets"
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star   = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','firstat_name','last_name','email','password')

class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id','planet_name','planet_type','home_star','mass','radius','distance')

user_schema = UserSchema()
users_schema = UserSchema(many=True)
planet_schema = PlanetSchema()
planets_schema =PlanetSchema(many=True)
if __name__== '__main__':
    app.run()