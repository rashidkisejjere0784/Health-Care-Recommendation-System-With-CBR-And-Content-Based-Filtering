import re
import numpy as np

def generate_Factorized_Matrix(data, column, is_service = False):
  bow = list()
  for i, element in enumerate(data[column].values):
    element = re.sub('\.', ',', str(element))
    values = element.split(',')
    for value in values:
        if value == '':
            continue
        value = value.strip().lower()
        bow.append(value)
    

  bow = sorted(set(bow))

  Matrix = np.zeros((len(data), len(bow)))
  for i, element in enumerate(data[column].values):
    element = str(element)
    element = re.sub('\.', ',', element)
    words = element.split(',')
    for word in words:
      try:
        word = word.strip().lower()
        index = list(bow).index(word)
        Matrix[i, index] = 1
      except:
        continue

  return Matrix, bow

def get_matrix(value, split_by, bow, is_op = False):
    matrix = np.zeros(len(bow))
    elements =[element.strip() for element in value]

    for i, word in enumerate(bow):
        if word in elements:
            matrix[i] = 1

    return matrix