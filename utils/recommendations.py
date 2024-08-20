import pandas as pd
import numpy as np
from .preprocess_data import generate_Factorized_Matrix, get_matrix
from .recommendar_algorthims import get_recommendation_filtered_services


def get_recommendations(services : list, latitude : float, longitude : float, approach : str = "Content Based Filtering"):
    hospital_data = pd.read_excel("./Data/Kampala & Wakiso.xlsx")
    service_matrix, service_bow = generate_Factorized_Matrix(hospital_data, 'cleaned services', is_service=True)
    latitude_longitude = np.array([[latitude, longitude]])

    Full_data = np.concatenate([service_matrix, np.array(hospital_data['latitude'].values).reshape(-1, 1), np.array(hospital_data['longitude'].values).reshape(-1, 1)], axis =1)

    service = get_matrix(services, ',', service_bow)
    latitude_longitude = np.array([[latitude, longitude]])

    if approach == "Content Based Filtering":
      # recommendation based on Content Based Filtering
      recommendation = get_recommendation_filtered_services(service=service, lat_lng = latitude_longitude, 
                                                          Full_data=Full_data, hospital_data=hospital_data)
    else:
       pass


    return recommendation


