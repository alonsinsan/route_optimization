import pandas as pd
import numpy as np
import threading
import os
from math import radians, sin, cos, acos
import random
from itertools import product
import json
from geopy.distance import geodesic
#import csv
from numpyencoder import NumpyEncoder

class myThread (threading.Thread):
    def __init__(self, threadID, name, action, values):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.action = action
        self.values = values
        self.result = None
        self.threadLock = threading.Lock()

    def run(self):
        print("Starting " + self.name)
        # Get lock to synchronize threads
        self.threadLock.acquire()
        result = self.action(**self.values)
        # Free lock to release next thread
        self.threadLock.release()
        self.result = result

def init_threads(action, values):
    # Create new threads
    
    results = []
    nums_ths = os.cpu_count() if len(values) > os.cpu_count() else len(values)
    for i in range(0, len(values), nums_ths):
        nums_sub_ths = len(values) if i + nums_ths > len(values) else i + nums_ths
        threads = [myThread(1, 'Thread-{}'.format(x), action, values[x]) for x in range(i, nums_sub_ths)]
        for th in threads:
            th.start()
        # Wait for all threads to complete
        for t in threads:
            t.join()
            results.append(t.result)
    return results


def distance(l1, l2):

    lat1 = float(l1.split(',')[0])
    lon1 = float(l1.split(',')[1])
    lat2 = float(l2.split(',')[0])
    lon2 = float(l2.split(',')[1]) 

    coords_1 = (float(l1[0]), float(l1[1]))
    coords_2 = (float(l2[0]), float(l2[1]))

    resp = geodesic(coords_1, coords_2).km
    return resp

def to_dict(dm, id, ids):
    n_dict = {id: {"nodos": list(ids), "costo": list(dm)}}
    #pd.DataFrame(dm, columns = ids, index = ids).to_csv('out.csv') 
    return n_dict

def get_cost(i,j,df, id, p1, p2):
    filtered_df = df[df.id != id]
    if (i == id.split('->')[0] and j in list(filtered_df.Origin)) or (i in list(filtered_df.Destination) and j == id.split('->')[1]) or (i in list(filtered_df.Destination) and j in list(filtered_df.Origin)): # or (i == id.split('->')[0] and j == id.split('->')[1]):
        cost = distance(p1, p2)
    else:
        if str(i) + "->" + str(j) in list(filtered_df.id):
            cost = 0
        else:
            cost = 6351
    if i == j or (i == id.split('->')[0] and j == id.split('->')[1]):
        cost = 6351
    return cost

def crea_dm(id, df):
    origen = id.split('->')[1]
    destino = id.split('->')[0]
    ruta = df[df.id == id]
    ruta_origen = ruta[['Origin', 'OriginPosition']]
    ruta_destino = ruta[['Destination', 'DestinationPosition']]
    ruta_origen = ruta_origen.rename(columns = {'Origin': 'nombre', 'OriginPosition': 'position'})
    ruta_destino = ruta_destino.rename(columns = {'Destination': 'nombre', 'DestinationPosition': 'position'})
    origenes = df[['Origin', 'OriginPosition']].drop_duplicates()
    destinos = df[['Destination', 'DestinationPosition']].drop_duplicates()
    index1 = [False if i in [origen, destino] else True for i in origenes.Origin]
    index2 = [False if i in [origen, destino] else True for i in destinos.Destination]
    origenes = origenes[index1]
    destinos = destinos[index2]
    origenes = origenes.rename(columns = {'Origin': 'nombre', 'OriginPosition': 'position'})
    destinos = destinos.rename(columns = {'Destination': 'nombre', 'DestinationPosition': 'position'})
    locations = pd.concat((origenes, destinos), axis = 0)
    locations = pd.concat((ruta_origen, locations), axis = 0)
    locations = pd.concat((locations, ruta_destino), axis = 0)
    locations = locations.drop_duplicates()
    all_costs = [get_cost(i,j, df, id, locations.position[locations.nombre == i].values[0], locations.position[locations.nombre == j].values[0]) for i,j in product(locations.nombre, locations.nombre)]
    n = locations.shape[0]
    d_mat = [all_costs[i:i+n] for i in range(0,n*n,n)]
    n_dict = to_dict(d_mat, id, locations.nombre)
    return n_dict

def save_dict(res):
    n = len(res)
    r_dict = {}
    for i in range(n):
        r_dict.update(res[i])
    with open("input.json", "w") as outfile:
        json.dump(r_dict, outfile, indent=4, sort_keys=False, separators=(', ', ': '), ensure_ascii=False, cls=NumpyEncoder)

def read_data():
    df = pd.read_excel('Rutas.xlsx')
    df["id"] = df[['Origin', 'Destination']].apply(lambda row: '->'.join(row.values.astype(str)), axis=1)
    return df

def main():
    rutas = read_data()
    ids = list(rutas.id)
    Prueba = random.sample(ids,5)
    params = [{"id":x, "df": rutas} for x in Prueba]
    resultados = init_threads(crea_dm, params)
    save_dict(resultados)

if __name__== "__main__":
    main()