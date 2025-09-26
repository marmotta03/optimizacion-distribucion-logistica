## Estrategia propuesta
Para abordar el problema integrado de asignación y ruteo, se plantea la siguiente metodología:

#### Baseline inicial

- Se resuelve primero el problema de asignación con costo mínimo usando pulp.

- A partir de esa asignación se computa el costo de ruteo (con OR-Tools/pyVRP), obteniendo así un costo global inicial que sirve como referencia.

### Búsqueda iterativa con aleatorización controlada

- Se realizan 100 iteraciones.

- En cada una, se construye una asignación alternativa de la siguiente forma:

    - Se selecciona aleatoriamente una fracción de los paquetes y se los asigna de manera random a alguno de sus nodos de cobertura o al service center (respetando factibilidad).

    - Los paquetes restantes se asignan de manera óptima con pulp.

- Con esta asignación mixta se calculan las rutas y el costo global.

### Selección de la mejor solución

- En cada iteración se compara el costo global obtenido contra el mejor conocido hasta el momento.

- Se conserva la asignación y ruteo de menor costo.

------------------------------------------

### Definición de costos

#### (*) Costo de asignación
Se calcula de manera directa, según lo indicado en el enunciado.

#### (**) Costo de ruteo
Este costo contempla las distancias recorridas por los camiones y busca elegir soluciones que reduzcan el tiempo de trabajo de los mismos.  

La fórmula general es:

- **Costo de ruteo** = ∑ (nodos y service centers) **costo origen**
- **Costo de origen** =  
  - (Costo fijo por camión) × (Cantidad de camiones)  
  + (Costo variable por camión) × (Cantidad de paquetes)  
  + (Distancia total recorrida) × 0.5

---

#### Observación importante
Dado que consideramos **más relevante minimizar los gastos de contratación de camiones** (por sobre la minimización de la distancia recorrida), al optimizador de CVRP de OR-Tools se le pasa la menor cantidad de camiones que sabemos que pueden cubrir la demanda desde el origen.  

Es decir:

\[
\text{Cantidad mínima de camiones} = \left\lceil \frac{\text{Paquetes asignados al origen}}{\text{Capacidad del camión}} \right\rceil
\]
