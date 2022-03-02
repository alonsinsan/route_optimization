# Script para resolver el problema de la ruta más corta.
# Problema: para una flotilla de camiones y una ubicación de destino_final y origen para cada camión; con una lista de posibles rutas,
# se busca la ruta que minimice la distancia recorrida en vacío.
# Teóricamente, la ruta destino_final - origen es la ruta con la distancia en vacío más grande.
# En términos coloquiales, buscamos regresar el camión a su origen, intentando aprovechar sub-rutas de camino.
import numpy as np
import json
from pulp import LpMinimize, LpProblem, lpSum, LpVariable, LpBinary, value
import threading
import os
from numpyencoder import NumpyEncoder
#------------------------------------------------------------------------------
# Clases
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
        result = self.action(self.values)
        # Free lock to release next thread
        self.threadLock.release()
        self.result = result
#---------------------------------------------------------------------------------------
# Funciones
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

def read_input(id):
    # INPUT: matriz de costos y matriz de tiempo asociado a los arcos para la ruta id
    # OUTPUT: diccionario con llaves 'nodos', 'costo' y 'tiempo' con diccionarios como values
    with open('input.json', 'r') as f:
        d = json.loads(f.read())
    return d[id]

def problem(d):
    # Función para construir el problema dado un diccionario de restricciones y resolver el problema
    # INPUT: diccionario con matrices de costo y tiempo
    # OUTPUT: solución al problema
    # Problema: 
    # minimizar sum(sum(x_ij*C_ij for i in nodos) for j in nodos)
    # s.t. 
    # sum(x_1j for j in nodos_de_1) == 1 (del nodo destino sólo puedes escoger una ruta de salida)
    # sum(x_in for i in nodos_hacia_n) == 1 (sólo puedes llegar al nodo origen desde una ruta)
    # sum(x_ih for i in nodos_hacia_h) == sum(x_hj for j in nodos_desde_h); para cada nodo h (lo que llega a un nodo, debe salir)
    n = len(d['nodos'])
    nodos = [i for i in range(n)]
    #nodos = np.array(d['nodos'])
    costos = np.array(d['costo'])
    model = LpProblem(name = 'route', sense = LpMinimize) #
    route_vars = LpVariable.dicts('arcs', [(i,j) for i in nodos for j in nodos], 0,1, LpBinary)
    # función objetivo
    model += lpSum(route_vars[i,j]*costos[i,j] for i in nodos for j in nodos)
    # restricción de oferta
    model += lpSum(route_vars[0,j] for j in nodos) == 1
    # restricción de demanda
    model += lpSum(route_vars[i,n-1] for i in nodos) == 1
    # balance
    for h in nodos[1:-1]:
        model += lpSum(route_vars[i,h] for i in nodos) == lpSum(route_vars[h,j] for j in nodos)
    model.solve()
    sol = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            sol[i,j] = route_vars[i,j].varValue
    return sol, value(model.objective)



def get_route(M):
    # Function to get the route given the solution matrix
    # INPUT: solution matrix
    # OUTPUT: permutation_matrix
    n = len(M[0])
    node = np.where(M[0] == 1)[0][0]
    route = [0]
    route.append(node)
    resp = False if node != (n-1) else True
    while not resp:
        node = np.where(M[node] == 1)[0][0]
        route.append(node)
        if node == (n-1):
            resp = True
    return route
    
def resuelve(id):
    # Resolver el problema de la ruta más corta para la ruta "id"
    d = read_input(id)
    solution, obj_val = problem(d)
    route = get_route(solution)
    n_dict = {"ruta": route, "value": obj_val}
    return n_dict

def create_dict(results, ids, d):
    dict_sols = {}
    n = len(ids)
    for i in range(n):
        aux = d[ids[i]]["nodos"]
        aux_sol = [aux[i] for i in results[i]["ruta"]]
        d_aux = {ids[i]: {"nodos": results[i]["ruta"], "ruta": aux_sol, "value": results[i]["value"]}}
        dict_sols.update(d_aux)
    return dict_sols

#-------------------------------------------------------------------------------------
# main
def resuelve_rutas():
    # Función para resolver todas las líneas
    with open('input.json', 'r') as f:
        d = json.loads(f.read())
    ids = list(d.keys())
    itera = False
    if itera:
        sols = {}
        counter = 1
        for id in ids:
            print(counter)
            res = resuelve(id)
            aux = {id: res}
            sols.update(aux)
            counter += 1
    else:
        results = init_threads(resuelve, ids)
    sols = create_dict(results, ids, d)
    with open("solution.json", "w") as outfile:
        json.dump(sols, outfile, indent=4, sort_keys=True, separators=(', ', ': '), ensure_ascii=False, cls=NumpyEncoder)


#---------------------------------------------------------------------------------------
if __name__ == "__main__":
    resuelve_rutas()