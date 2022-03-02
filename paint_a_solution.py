import folium
import pandas as pd
import json
import re
def paint():
    with open('mexico.json') as f:
        mexico = json.load(f)
    rutas = pd.read_excel('Rutas.xlsx')
    with open('solution.json', 'rb') as f:
        solution = json.load(f)

    rutas["id"] = [i + "->" + j for i,j in zip(rutas.Origin, rutas.Destination)]
    ids = list(solution.keys())
    #id = random.sample(ids,1)
    for id in ids:
        ruta_original = rutas[rutas.id == id]
        arco_original = [[(float(x.split(',')[0]), float(x.split(',')[1])), (float(y.split(',')[0]), float(y.split(',')[1]))] for x,y in zip(ruta_original.OriginPosition,ruta_original.DestinationPosition)]
        ruta_sol = solution[id]["ruta"]
        n = len(ruta_sol)
        data = pd.DataFrame()
        origenes = rutas[['Origin', 'OriginPosition']]
        destinos = rutas[['Destination', 'DestinationPosition']]
        origenes = origenes.rename(columns = {'Origin': 'nombre', 'OriginPosition': 'position'})
        destinos = destinos.rename(columns = {'Destination': 'nombre', 'DestinationPosition': 'position'})
        puntos = pd.concat((origenes, destinos), axis = 0).drop_duplicates()

        for i in range(n):    
            p = puntos.position[puntos.nombre == ruta_sol[i]].values[0]
            aux_df = pd.DataFrame({'latitude': p.split(',')[0], 'longitude': p.split(',')[1]}, index = [i])
            data = pd.concat((data,aux_df), axis = 0)

        arcos = []
        inds = []
        for i in range(1,n):
            id_aux = ruta_sol[i-1] + "->" + ruta_sol[i]
            if id_aux in list(rutas.id):
                ind = 'con_carga'
            else:
                ind = 'en_vacío'
            p1 = puntos.position[puntos.nombre == ruta_sol[i-1]].values[0]
            p2 = puntos.position[puntos.nombre == ruta_sol[i]].values[0]
            arco_aux = [(float(p1.split(',')[0]), float(p1.split(',')[1])), (float(p2.split(',')[0]), float(p2.split(',')[1]))]
            arcos.append(arco_aux)
            inds.append(ind)
            

        #-------------------------------------------------------------------------------------------------------
        laMap = folium.Map(location=[data.latitude[0], data.longitude[0]], tiles='Stamen Toner', zoom_start=9)

        #add the shape of Mexico to the map
        folium.GeoJson(mexico).add_to(laMap)

        #for each row in the dataset, plot the corresponding latitude and longitude on the map
        for i,row in data.iterrows():
            folium.CircleMarker((row.latitude,row.longitude), radius=3, weight=2, color='yellow', fill_color='red', fill_opacity=.5).add_to(laMap)
        folium.PolyLine(arco_original, color ="red").add_to(laMap)
        for j in range(len(arcos)):
            if inds[j] == 'en_vacio':
                folium.PolyLine(arcos[j], color = "red").add_to(laMap)
            else:
                folium.PolyLine(arcos[j], color = "green").add_to(laMap)

        #save the map as an html    
        laMap.save('mapas/' + re.sub('->','--', id) + '.html')

if __name__ == "__main__":
    paint()