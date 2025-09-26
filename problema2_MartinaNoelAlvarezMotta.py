import sys
import pulp
import numpy as np
import math
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Levanto el input
def leer_archivo(nombre_archivo):
    lineas = []
    with open(nombre_archivo, "r") as f:
        for linea in f:
            linea = linea.strip()
            if linea == "0 0":   # condición de corte
                break
            lineas.append(linea)
    return lineas


def resolver_casos(lineas):
    """
    Procesa el input en casos: levanta los parametros del caso en particular y llama a resolverlo
    Devuelve una lista de lineas de output
    """
    output = []
    caso = 1

    # Para cada caso, primero obtengo los valores de los parametros
    while len(lineas)>0:
        n, m = map(int, lineas.pop(0).split())
        s = float(lineas.pop(0))

        capacidades_nodos = []
        costos_nodos = []
        cobertura = np.zeros((n, m))

        for i in range(n):
            capacidad, costo = map(float, lineas.pop(0).split())
            capacidades_nodos.append(capacidad)
            costos_nodos.append(costo)

        for i in range(n):
            cobertura_i = list(map(int, lineas.pop(0).split()))
            cubiertos = cobertura_i.pop(0)
            for j in range(cubiertos):
                cobertura[i][cobertura_i[j]] = 1
        
        capacidad_vehiculo = int(lineas.pop(0))
        costo_fijo_vehiculo, costo_var_vehiculo = map(float, lineas.pop(0).split())
        coordenadas_svc = list(map(float, lineas.pop(0).split()))

        coordenadas_nodos = [[0,0]] * n
        coordenadas_paquetes = [[0,0]] * m
        for i in range(n):
            coords = list(map(float, lineas.pop(0).split()))
            nodo = int(coords.pop(0))
            coordenadas_nodos[nodo] = coords
        for j in range(m):
            coords = list(map(float, lineas.pop(0).split()))
            paquete = int(coords.pop(0))
            coordenadas_paquetes[paquete] = coords

        #llamar al solver
        resolver(m, n, s, capacidades_nodos, costos_nodos, cobertura, capacidad_vehiculo, costo_fijo_vehiculo,
                 costo_var_vehiculo, coordenadas_svc, coordenadas_nodos, coordenadas_paquetes,
                 output, caso)
        caso = caso + 1

    return output


def resolver(m, n, s, capacidades, costos, cobertura, capacidad_vehiculo, costo_fijo_vehiculo,
             costo_var_vehiculo, coordenadas_svc, coordenadas_nodos, coordenadas_paquetes,
             output, caso):
    """
    Obtiene una solución global a través de nuestra heurística para el caso específico
    """

    # BASELINE INICIAL -----------------------------------------------------------------
    # Obtengo la asignación de costo minimo,
    # dejando todos los paquetes sin asignar y permitiendo que el optimizador los elija
    paquetes_no_asignados = [None] * m
    costo_asignacion, asignacion = optimizar_asignacion(m, n, s, capacidades, costos, cobertura, paquetes_no_asignados)
    costo_ruteo = costo_de_ruteo(m,n,capacidad_vehiculo,costo_fijo_vehiculo,costo_var_vehiculo,asignacion,coordenadas_svc,coordenadas_nodos,coordenadas_paquetes)
    costo_global = costo_asignacion + costo_ruteo

    # Búsqueda iterativa con aleatorización controlada ----------------------------------

    return costo_global


def optimizar_asignacion(m, n, s, capacidades, costos, cobertura, asignados):
    """
    Realiza una optimización de asignación como un modelo de PLE con Pulp tomando los parametros:
    - m: cantidad de paquetes
    - n: cantidad de nodos
    - s: costo de asignacion del SVC
    - capacidades: de asignacion de cada nodo
    - costos: de asignacion de cada nodo
    - cobertura: matriz de que nodo puede entregar cada paquete
    - asignados: lista de paquetes ya previamente asignados

    Devuelve:
    - costo de asignación
    - lista de aginación:
    X_j = -1 si paquete j se asigna a SV
           i si paquete j se asigna al nodo i
    """

    modelo = pulp.LpProblem("Caso", pulp.LpMinimize)

    # delta_j = 1 si paquete j sale del SVC; 0 sino
    delta = pulp.LpVariable.dicts("d", range(0, m), cat="Binary")

    # x_i_j = 1 si nodo i entrega paquete j; 0 sino
    x = pulp.LpVariable.dicts("x", [(i,j) for i in range(0,n) for j in range(0,m)], cat="Binary")

    # Coeficientes F.O.
    c_j = [s] * m
    c_i_j = [[valor]*m for valor in costos]

    # Función objetivo
    modelo += pulp.lpSum(c_j[j]*delta[j] for j in range(0,m)) + \
            pulp.lpSum(c_i_j[i][j]*x[i,j] for i in range(0,n) for j in range(0,m)), "FO"

    # Restricciones de cobertura
    for i in range(n):
        for j in range(m):
            modelo += x[i,j] <= cobertura[i][j], f"cobertura_{i}_{j}"

    # Restricciones de capacidad
    for i in range(n):
        modelo += pulp.lpSum(x[i,j] for j in range(m)) <= capacidades[i], f"capacidad_{i}"

    # Restricciones de entrega de cada paquete
    for j in range(m):
        if asignados[j]==-1: # Si ya esta asignado al SVC
            modelo += delta[j] == 1, f"fijo_delta_{j}"
            for i in range(n):
                    modelo += x[i, j] == 0, f"fijo_x_{i}_{j}"
        elif (asignados[j] is not None): # Si esta asignado a un nodo
            nodo = int(asignados[j])
            modelo += delta[j] == 0, f"fijo_delta_{j}"
            for i in range(n):
                if i == nodo:
                    modelo += x[i, j] == 1, f"fijo_x_{i}_{j}"
                else:
                    modelo += x[i, j] == 0, f"fijo_x_{i}_{j}"
        else: # No asignado
            modelo += pulp.lpSum(x[i,j] for i in range(n)) + delta[j] == 1, f"paquete_{j}_es_entregado"

    # Resuelvo
    modelo.solve()

    # Devuelvo lista de asignaciones
    asignados_out = []
    for j in range(m):
        if pulp.value(delta[j]) == 1:
            asignados_out.append(-1)
        else:
            nodo_asignado = None
            for i in range(n):
                if pulp.value(x[i, j]) == 1:
                    nodo_asignado = i
                    break
            asignados_out.append(nodo_asignado)

    return pulp.value(modelo.objective), asignados_out



def distancia_euclidea(a, b):
    return int(round(np.linalg.norm(np.array(a) - np.array(b))))



# COSTO DE RUTEO
# Dada una asignación factible, calculo su costo de ruteo
def costo_de_ruteo(m,n,capacidad_vehiculo,costo_fijo_vehiculo,costo_var_vehiculo,asignacion,coordenadas_svc,coordenadas_nodos,coordenadas_paquetes):
    """
    Dada una asignación factible, calculo su costo de ruteo
    - Costo de ruteo: sumar desde el svc y cada nodo, el costo de origen
    - Costo de origen: costo_camion * cantidad_camiones + distancias recorridas * 0.5
                                        + costo_variable * cantidad_paquetes
    """
    costo_ruteo = 0
    origenes_con_ruta = 0
    rutas = []
    # Recorremos nodos y svc, y calculamos el costo de origen para cada uno
    for i in range(-1,n):
        if i not in asignacion:
            costo_origen = 0
        else:
            if i == -1:
                coordenadas_origen = coordenadas_svc
            else:
                costo_origen = costo_de_origen()
    return costo_ruteo


def costo_de_origen():
    return 0


# -------- main --------
def main():
    archivo_entrada = sys.argv[1]
    archivo_salida = sys.argv[2]

    lineas = leer_archivo(archivo_entrada)

    output = resolver_casos(lineas)

    with open(archivo_salida, "w") as f:
        f.write("\n".join(output))

# -------- entrypoint --------
if __name__ == "__main__":
    main()