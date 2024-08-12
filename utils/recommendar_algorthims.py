import numpy as np
from numpy.linalg import norm
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances

def calculate_cosine_similarity(point, Full_data ,hospital_data, n=3):
    cosine_similarities = np.dot(Full_data, point.T) / (norm(Full_data, axis=1)[:, np.newaxis] * norm(point))
    top_choices = np.argsort(cosine_similarities.flatten())[-n:][::-1]
    top_names = hospital_data.iloc[top_choices]
    return top_names, top_names.index

def get_recommendation_filtered_services(service, lat_lng, Full_data, hospital_data : pd.DataFrame):
    print(service)
    full_data_services = Full_data[:, :len(service)]
    
    top_choices = calculate_cosine_similarity(np.array([service]),full_data_services, hospital_data=hospital_data, n = 20)[1]
    print(top_choices)
    filtered_data = Full_data[top_choices]
    print(hospital_data.iloc[top_choices])

    # final_vector  = np.concatenate([
    #     [op_day], [payment], care_s.reshape(-1, 1), np.array([rating]).reshape(-1, 1)
    # ], axis = 1)

    # final_vector = final_vector.astype(np.float64)

    # Final_choices = calculate_cosine_similarity(final_vector, filtered_data[:, len(service):], hospital_data=hospital_data, n = 10)[1]
    # print(Final_choices)
    # print(lat_lng)
    # top_choices = top_choices[Final_choices]

    top_choices_df = hospital_data.loc[top_choices]
    print(top_choices_df['cleaned services'])
    latitude_logitude_full = top_choices_df[['latitude', 'longitude']].fillna(0).values

    distance = euclidean_distances(latitude_logitude_full, lat_lng)
    top = np.argsort(distance.flatten())[:10]
    print(distance)
    print(top)
    top_choices = top_choices[top]

    return hospital_data.iloc[top_choices]
