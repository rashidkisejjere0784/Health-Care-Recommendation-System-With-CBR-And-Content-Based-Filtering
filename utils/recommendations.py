import pandas as pd
import numpy as np
from .preprocess_data import *
from .recommendar_algorthims import *


def get_recommendations(services_str : str, latitude : float, longitude : float, payment_str : str, op_day_str : str , care_system : str, approach : str):
    hospital_data = pd.read_excel("./Data/Kampala & Wakiso.xlsx")
    service_matrix, service_bow = generate_Factorized_Matrix(hospital_data, 'cleaned services', is_service=True)
    payment_matrix, payment_bow = generate_Factorized_Matrix(hospital_data, 'mode of payment')
    operating_time_matrix = hospital_data['operating_hours'].apply(gen_matrix_op_time).values
    care_system_full = hospital_data['care_system'].apply(lambda x: encode_care_system(str(x)))

    care_system_rating = np.concatenate([care_system_full.values.reshape(-1, 1)], axis = 1)
    Merged_data = np.concatenate([service_matrix, np.array(list(operating_time_matrix)), payment_matrix], axis =1)
    Full_data = np.concatenate([Merged_data, care_system_rating], axis =1)

    service = get_matrix(services_str, ',', service_bow)
    latitude_longitude = np.array([[latitude, longitude]])

    op = get_opday_matrix(op_day_str)
    payment = get_matrix(payment_str.lower(), ',', payment_bow)
    care_s = np.array([encode_care_system(care_system)])

    if approach == "cbf":
      # recommendation based on Content Based Filtering
      recommendation = get_recommendation_filtered_services(service=service, lat_lng = latitude_longitude, 
                                                          op_day=op, payment=payment, care_s=care_s,Full_data=Full_data, hospital_data=hospital_data)
    else:
      data = pd.read_excel("data/CBR data.xlsx")

      query_df = pd.DataFrame(columns=data.columns)
      full_data_df = data.copy()

      query_df["services"] = [services_str]
      query_df["latitude"] = [float(latitude)]
      query_df["longitude"] = [float(longitude)]
      query_df["day"] = [op_day_str]
      query_df["mode of payment"] = [payment_str]
      query_df["care system"] = [care_system]

      indicies = get_recommendation_CBR(full_data_df, query_df)
      recommendation = hospital_data.iloc[indicies]


    return recommendation


