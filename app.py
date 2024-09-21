from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd
import numpy as np
import joblib
from utils.recommendations import get_recommendations
from utils.format_date import format_date
from flask_bcrypt import Bcrypt 
import os
from dotenv import load_dotenv
from flask_mail import Mail
from db import db
from models.userModel import User
from datetime import timedelta
from utils.data_load import get_data, get_facility, load_temp_data, save_new_service_to_dict
from utils.auth import *
from geopy.geocoders import Photon


app = Flask(__name__)
geolocator = Photon(user_agent="measurements")
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
ADMIN_ID = os.environ.get('ADMIN_ID')
DATA_PATH = os.environ.get('DATA_PATH')
TEMP_DATA = os.environ.get('TEMP_DATA')
HOST = os.environ.get('HOST')

db.init_app(app)
mail = Mail(app)
bcrpy = Bcrypt(app)


def extract_elements(elements : list, is_service = False) -> set:
    elements_set = list()
    for element in elements:
        for s in str(element).split(','):
            s = s.lower().strip()
            if s == 'nan':
                continue
            if s != '':
                elements_set.append(s)
    
    return sorted(set(elements_set))

@app.route('/health_check', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route('/')
def home():
    data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    services_dict = joblib.load("./data/services_dict.pkl")
    services = data['cleaned services'].values
    services_set = extract_elements(services, True)

    return render_template('home.html', services=services_set, services_dict=services_dict)

def extract_dict(df : pd.DataFrame) -> dict:
    hospital_ids = df['hospital Id'].values.tolist()
    hospital_names = df['facility_name'].values.tolist()
    print(df.columns)
    Services = df['cleaned services'].values.tolist()
    Subcounty = df['Subcounty'].values.tolist()
    care_system = df['care_system'].values.tolist()
    rating = df['rating'].values.tolist()
    Operation_Time = df['operating_hours'].apply(format_date).values.tolist()
    Latitude = df['latitude'].values.tolist()
    Longitude = df['longitude'].values.tolist()
    Payment = df['mode of payment'].values.tolist()
    contact = df['phone_number'].values.tolist()

    data_json =  {'hospital Id' : hospital_ids, 'facility_name' : hospital_names, 'mode of payment' : Payment,
                        'cleaned services' : Services, 'Subcounty' : Subcounty, 'rating' : rating, 'care_system' : care_system,
                        'operating_hours' : Operation_Time, 'latitude' : Latitude, 'longitude' : Longitude, 'phone_number' : contact}
    
    return data_json


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email = email).first()
        if user and bcrpy.check_password_hash(user.password, password):
            token = create_access_token(str(user.id))
            session['user_token'] = token

            hospitals, data_len = get_data(start_index=0, end_index=20)
            return render_template('show_data.html', hospitals = hospitals, authenticated = True, is_admin = is_user_admin(user.id), data_len = data_len, start = 0)
        else:
            return render_template('contribute.html', error = "Invalid Email or Password")

    return render_template('contribute.html', authenticated=False)

@app.route('/show_data', methods=['GET'])
def show_data():
    
    if 'user_token' not in session:
        return redirect(url_for('login'))
    
    is_auth, is_admin = is_authenticated(User, session)
    print(is_admin)
    if not is_auth:
        return redirect(url_for('login'))
    
    # Accessing query parameters
    start = request.args.get('start')

    if start is None:
        start = 0
    
    end = int(start) + 50
    
    hospitals, data_len = get_data(start_index=int(start), end_index=int(end))
    
    return render_template('show_data.html', hospitals = hospitals, authenticated = True, is_admin = is_admin, data_len = data_len, start = start)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        expires = timedelta(seconds=300)
        
        if password != confirm_password:
            return render_template('register.html', error = "Password mismatch")
        
        user = User.query.filter_by(email = email).first()
        if user:
            if user.status == 1:
                return render_template('register.html', error = "Email already exists")
        
            elif user.status == 0:
                token = create_access_token(str(user.id))
                send_email(user.username, user.email, user, expires, mail=mail, token=token)
                return render_template('register.html', error = "User isn't verified yet, check your email")


        try:
            password = bcrpy.generate_password_hash(password).decode('utf8')
            user = User(username = username, email = email, password = password)
            db.session.add(user)
            db.session.commit()

            token = create_access_token(str(user.id))
            send_email(username, email, user, expires,mail=mail, token=token)

            return render_template('register.html', message = "Registration successful, Check your email to verify your registration")
        
        except Exception as e:
            print(e)
            return render_template('register.html', error = "Registration Failed")

    else:
        return render_template('register.html', error = None)


@app.route('/get_recommendations', methods=['POST'])
def get_recommendation():
    if request.method == 'POST':
        data = request.get_json()
        services = data.get('services', [])
        latitude = data.get('latitude', 0.0)
        longitude = data.get('longitude', 0.0)
        date = data.get('date', [])
        care_system = data.get('careSystem', '')
        payment = data.get('paymentMode', '')
        approach = data.get('approach')

        recommendation = get_recommendations(services_str=",".join(services), 
                                         latitude=latitude, longitude=longitude, payment_str=payment, op_day_str=",".join(date), care_system=care_system, approach=approach)
        session['recommendations'] = extract_dict(recommendation)

        return jsonify({"response" : True})


@app.route('/view', methods=['GET'])
def view():
    kwargs = {
        'sort_by' : None,
        'care_system' : 'all',
    }

    if 'recommendations' not in session:
        return redirect(url_for('home'))
    
    if 'sort-by' in session:
        kwargs['sort_by'] = session['sort-by']
    
    if 'care-system' in session:
        kwargs['care_system'] = session['care-system']
    
    recommendations = session['recommendations']
    return render_template('view.html', recommendations=recommendations, filter_args=kwargs)

@app.route('/filter', methods=['POST'])
def filter():
    care_system = request.form.get('care-system', None)
    sort_by = request.form.get('sort-by',None)

    if 'sort-by' in session:
        session.pop('sort-by')
    
    if 'care-system' in session:
        session.pop('care-system')

    df = pd.DataFrame(session['recommendations'])
    if care_system is not None:
        if 'temp_df' in session:
            df = pd.DataFrame(session['temp_df'])
        else:
            session['temp_df'] = extract_dict(df)
        
        if care_system == 'all':
            session['recommendations'] = df
        
        else:   
            df = df[df['care_system'] == care_system]
            session['recommendations'] = extract_dict(df)
            session['care-system'] = care_system
    
    if sort_by is not None:
        sort_type = True if sort_by == 'ascending' else False
        df = df.sort_values(by=['rating'], ascending=sort_type)
        session['recommendations'] = extract_dict(df)
        session['sort-by'] = sort_by

    return redirect(url_for('view'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/verify', methods=['GET'])
def verify_token():
    token = request.args.get('token')
    try:
        decoded_jwt = decode_token(token)
        user_id = int(decoded_jwt['sub'])

        user = User.query.filter_by(id=user_id).first()
        user.status = 1
        db.session.commit()
        return jsonify({
            "response" : "success"
        })
    except Exception as e:
        print(e)
        return jsonify({
            "response" : "Invalid token"
        }
        )
    

@app.route('/edit_hospital', methods=['POST', 'GET'])
def edit_hospital():
    if not is_authenticated(User=User, session=session):
        return redirect(url_for('login'))
    
    hospital_id = int(request.form['hospital_id'])
    print(hospital_id)
    hospital = get_facility(hospital_id)

    data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    services_dict = joblib.load("./data/services_dict.pkl")
    services = data['cleaned services'].values
    services_set = extract_elements(services, True)
    
    return render_template('edit_hospital.html', hospital=hospital, services_dict = services_dict,
                            services = services_set, authenticated = True)



@app.route('/add_hospital', methods=['POST'])
def add_hospital():
    auth = is_authenticated(User,session)
    if not auth[0]:
        return render_template('show_data.html', authenticated = False, is_admin = auth[1])
    
    try:
        hospital_id = int(request.form['hospital Id'])
    except:
        hospital_id = None

    hospital_name = request.form['hospitalName']
    location = request.form['location']
    services = request.form.getlist('services')
    rating = request.form['rating']
    care_system = request.form['care system']
    operating_time = request.form['operatingTime']
    payment = request.form['payment']
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    phone = request.form['phone']
    website = request.form['website']

    temp_data = load_temp_data()
    print(services)
    
    temp_data = pd.concat(
        [temp_data, pd.DataFrame({
            "hospital Id": hospital_id,
            "facility_name": hospital_name,
            "rating": rating,
            "care_system": care_system,
            "cleaned services": ", ".join(services),
            "operating_hours": operating_time,
            "Subcounty": location,
            "mode of payment": payment,
            "latitude": latitude,
            "longitude": longitude,
            "phone_number": phone,
            "website": website
        }, index=[0])],ignore_index=True
    )

    temp_data.to_excel("data/temp_data.xlsx", index=False)
    
    return redirect(url_for('show_data'))

@app.route('/record_data', methods=['GET'])
def record_data():
    if not is_authenticated(User, session)[0]:
        return redirect(url_for('login'))
    
    data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    services_dict = joblib.load("./data/services_dict.pkl")
    services = data['cleaned services'].values
    services_set = extract_elements(services, True)
    
    return render_template('record_data.html', services_dict = services_dict,
                            services = services_set, authenticated = True)


@app.route('/review_data', methods=['GET', 'POST'])
def review_data():
    auth = is_authenticated(User, session)
    if not auth[0]:
        return render_template('contribute.html')
    
    if not auth[1]:
        return render_template('contribute.html')
    
    DATA_PATH = "data/Kampala & Wakiso.xlsx"
    TEMP_DATA = "data/temp_data.xlsx"
    
    temp_data = pd.read_excel(TEMP_DATA)

    if request.method == 'POST':
        id = int(request.form['hospital_id'])
        action = request.form['Action']

        if action == 'approve':
            hospital_data = pd.read_excel(DATA_PATH)
            temp_data = pd.read_excel(TEMP_DATA)

            hospital = temp_data.iloc[id]
            if str(hospital['hospital Id']) in [None, np.nan, 'nan', 'NaN']:
                print(hospital['hospital Id'])
                # Concatenate the data
                index = len(hospital_data) + 1
                hospital['hospital Id'] = index
                hospital_data = pd.concat([hospital_data, hospital.to_frame().T],axis = 0, ignore_index=True)
                hospital_data.to_excel(DATA_PATH, index=False)

            else:
                hospital['hospital Id'] = int(hospital['hospital Id'])
                print(hospital_data[hospital_data['hospital Id'] == hospital['hospital Id']])
                hospital_data[hospital_data['hospital Id'] == hospital['hospital Id']] = hospital
                hospital_data.to_excel(DATA_PATH, index=False)
            
            temp_data = temp_data.drop(id)
            temp_data.to_excel(TEMP_DATA, index=False)
        
        if action == 'decline':
            temp_data = pd.read_excel(TEMP_DATA)
            temp_data = temp_data.drop(id)
            temp_data.to_excel(TEMP_DATA, index=False)

        temp_data = pd.read_excel(TEMP_DATA)

    return render_template('review_data.html', hospitals=temp_data, authenticated = True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_image', methods=['POST'])
def add_image():
    auth = is_authenticated(User, session)
    if not auth[0]:
        return redirect(url_for('login'))
    
    if not auth[1]:
        return render_template('login')
    
    if request.method == 'POST':
        service_name = request.form['service_name']
        description = request.form['description']
        image = request.files['file']
        
        if image and allowed_file(image.filename):
            filename = service_name + ".png"
            image.save(os.path.join("./static/images", filename))

            save_new_service_to_dict(service_name, description)

            return redirect(url_for('review_data'))
        else:
            return redirect(url_for('review_data'))

    return render_template('upload.html')


@app.route('/get_cordinates', methods=['POST'])
def get_cordinates():
    if request.method == 'POST':
        data = request.get_json()
        address = data['address']


        location = geolocator.geocode(f"{address}, uganda")
        latitude = location.latitude
        longitude = location.longitude

        return jsonify({
            "latitude": latitude,
            "longitude": longitude
        })

with app.app_context():
    db.create_all()
if __name__ == '__main__':
    
    app.run(host="0.0.0.0", debug=True)