from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd
import numpy as np
import joblib
from utils.recommendations import get_recommendations
import json
from utils.format_date import format_date

app = Flask(__name__)
app.secret_key = "This is the secret key"

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
    Services = df['services'].values.tolist()
    Subcounty = df['Subcounty'].values.tolist()
    care_system = df['care_system'].values.tolist()
    rating = df['rating'].values.tolist()
    Operation_Time = df['operating_hours'].apply(format_date).values.tolist()
    Latitude = df['latitude'].values.tolist()
    Longitude = df['longitude'].values.tolist()
    Payment = df['mode of payment'].values.tolist()
    contact = df['phone_number'].values.tolist()

    data_json =  {'hospital Id' : hospital_ids, 'facility_name' : hospital_names, 'mode of payment' : Payment,
                        'services' : Services, 'Subcounty' : Subcounty, 'rating' : rating, 'care_system' : care_system,
                        'operating_hours' : Operation_Time, 'latitude' : Latitude, 'longitude' : Longitude, 'phone_number' : contact}
    
    return data_json


@app.route('/get_recommendations', methods=['POST'])

def get_recommendation():
    if request.method == 'POST':
        data = request.get_json()
        services = data.get('services', [])
        latitude = data.get('latitude', 0.0)
        longitude = data.get('longitude', 0.0)

        recommendation = get_recommendations(services, latitude, longitude)
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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)