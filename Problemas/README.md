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

(*) Costo de asignación:
De manera directa, según el enunciado
(**) Costo de ruteo
Para tener en cuenta las distancias recorridas por los camiones y elegir opciones que requieran tener a los camiones menos tiempo trabajando, consideramos:
- Costo de ruteo = sumatoria(nodos y service center) costo origen
- Costo de origen = Costo de camion * cantidad de camiones + costo variable de camion * cantidad de paquetes + distancias recorridas * 0.5

Una observación importante es que como consideramos más importante la baja en gastos de contratación de camiones (que hacer menos distancia), vamos a pasarle al optimizador de CVRP de OR-Tools, la menor cantidad de camiones que sabemos que pueden cubrir la demanda desde el origen. Esto es: roof(cantidad de paquetes asignados al origen / capacidad del camion)