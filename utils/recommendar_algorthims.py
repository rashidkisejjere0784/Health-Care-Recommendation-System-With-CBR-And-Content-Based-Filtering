import numpy as np
from numpy.linalg import norm
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
import intellikit as ik

def calculate_cosine_similarity(point, Full_data ,hospital_data, n=3):
    cosine_similarities = np.dot(Full_data, point.T) / (norm(Full_data, axis=1)[:, np.newaxis] * norm(point))
    top_choices = np.argsort(cosine_similarities.flatten())[-n:][::-1]
    top_names = hospital_data.iloc[top_choices]
    return top_names, top_names.index


def get_recommendation_filtered_services(service, lat_lng, op_day, care_s, payment, Full_data, hospital_data):
    print(service)
    full_data_services = Full_data[:, :len(service)]
    
    top_choices = calculate_cosine_similarity(np.array([service]),full_data_services, hospital_data=hospital_data, n = 20)[1]
    print(top_choices)
    filtered_data = Full_data[top_choices]
    print(hospital_data.iloc[top_choices])

    final_vector  = np.concatenate([
        [op_day], [payment], care_s.reshape(-1, 1)
    ], axis = 1)

    final_vector = final_vector.astype(np.float64)

    Final_choices = calculate_cosine_similarity(final_vector, filtered_data[:, len(service):], hospital_data=hospital_data, n = 10)[1]
    print(Final_choices)
    print(lat_lng)
    top_choices = top_choices[Final_choices]

    top_choices_df = hospital_data.loc[top_choices]
    latitude_logitude_full = top_choices_df[['latitude', 'longitude']].fillna(0).values

    distance = euclidean_distances(latitude_logitude_full, lat_lng)
    top = np.argsort(distance.flatten())[:8]
    print(distance)
    print(top)
    top_choices = top_choices[top]
    print(top_choices)
    print(hospital_data.iloc[21])

    return hospital_data.iloc[top_choices]

def clean_recommendation(top_recommendation : pd.DataFrame):
    indicies = top_recommendation['facility_names'].drop_duplicates().index
    print(top_recommendation.loc[indicies])
    return top_recommendation.loc[indicies]

def get_recommendation_CBR(full_data_df : pd.DataFrame, query_df : pd.DataFrame, n = 30):
    columns = full_data_df.columns
    measure_lat = ik.sim_difference
    measure_day = ik.sim_levenshtein
    measure_service = ik.sim_levenshtein
    measure_payment = ik.sim_stringEM

    # Convert Location, Operating Time, Payment, Care system and services in the full_data_df to str
    print(full_data_df.head())
    for col in ['day', 'mode of payment', 'care system', 'services']:
        full_data_df[col] = full_data_df[col].fillna("UNKNOWN")

    # Assign Functions
    similarity_functions = {
        'latitude': measure_lat,
        'longitude': measure_lat,
        'day': measure_day,
        'services': measure_service,
        'mode of payment': measure_payment,
        'care system': measure_payment
    }

    #Assign Weights
    feature_weights = {
        'latitude': 0.2,
        'longitude': 0.2,
        'day': 0.3,
        'services': 0.5,
        'mode of payment': 0.1,
        'care system': 0.1
    }

    return clean_recommendation(ik.linearRetriever(full_data_df, query_df, similarity_functions, feature_weights, n))['hospital Id']
