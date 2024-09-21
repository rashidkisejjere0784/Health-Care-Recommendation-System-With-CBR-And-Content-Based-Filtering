import pandas as pd
import joblib

def get_data(start_index : int, end_index : int) -> list:
    hospital_data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    data_len = len(hospital_data)
    hospital_data = hospital_data.loc[start_index : end_index]
    hospitals = []

    for id, hospital in hospital_data.iterrows():
        hospitals.append(hospital)

    return hospitals, data_len

def get_facility(id : int):
    print(id)
    hospital_data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    return hospital_data.iloc[id]

def load_data():
    data = pd.read_excel("data/Kampala & Wakiso.xlsx")
    services_dict = joblib.load("./data/services_dict.pkl")
    services = data['cleaned services'].values

    return services_dict, services

def load_temp_data():
    try:
        temp = pd.read_excel("data/temp_data.xlsx")
    
    except FileNotFoundError:
        data = pd.read_excel("data/Kampala & Wakiso.xlsx")
        temp = pd.DataFrame(columns=data.columns)
    
    return temp

def save_new_service_to_dict(service, description):
    services_dict = joblib.load("./data/services_dict.pkl")
    services_dict[service] = {
        'services' : [service],
        'desc' : description
    }
    
    joblib.dump(services_dict, "./data/services_dict.pkl")