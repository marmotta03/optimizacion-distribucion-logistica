import sys
import pulp
import numpy as np

def leer_archivo(nombre_archivo):# Levanto el input
  lineas = []
  with open(nombre_archivo, "r") as f:
    for linea in f:
        linea = linea.strip()
        if linea == "0 0":   # condición de corte
            break
        lineas.append(linea)
  return lineas

def resolver(m, n, s, capacidades, costos, cobertura, output, caso):
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

  # Restricciones
  for i in range(n):
    for j in range(m):
        modelo += x[i,j] <= cobertura[i][j], f"cobertura_{i}_{j}"

  for i in range(n):
    modelo += pulp.lpSum(x[i,j] for j in range(m)) <= capacidades[i], f"capacidad_{i}"

  for j in range(m):
    modelo += pulp.lpSum(x[i,j] for i in range(n)) + delta[j] == 1, f"paquete_{j}_es_entregado"

  # Resuelvo
  modelo.solve()

  output.append(f"Caso {caso}")
  output.append(f"{pulp.value(modelo.objective)}")
  for j in range(m):
    if delta[j].varValue == 1:
      id_ubicacion = -1
    else:
      id_ubicacion = next(i for i in range(n) if x[i,j].varValue == 1)
    output.append(f"{j} {id_ubicacion}")

  return

def resolver_casos(lineas):
  output = []
  caso = 1

  while len(lineas)>0:
    n, m = map(int, lineas.pop(0).split())
    s = float(lineas.pop(0))

    capacidades = []
    costos = []
    cobertura = np.zeros((n, m))

    for i in range(n):
      capacidad, costo = map(float, lineas.pop(0).split())
      capacidades.append(capacidad)
      costos.append(costo)

    for i in range(n):
      cobertura_i = list(map(int, lineas.pop(0).split()))
      cubiertos = cobertura_i.pop(0)
      for j in range(cubiertos):
        cobertura[i][cobertura_i[j]] = 1

    #llamar al solver
    resolver(m, n, s, capacidades, costos, cobertura, output, caso)
    caso = caso + 1

  return output

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
