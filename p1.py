import matplotlib.pyplot as plt

# Configuración inicial
anio_inicio = 2024
anio_fin = 2100
generacion = 25  # Duración de una generación en años
tasa_reemplazo = 2.1  # Tasa de reemplazo necesaria para mantener la población estable

# Lista de TFRs a simular
tfr_list = [0.9, 1, 1.3, 1.6, 1.9, 2.2, 2.5, 3, 4]

# Supongamos una población inicial normalizada a 100%
poblacion_inicial = 100

# Calcular número de generaciones
num_generaciones = (anio_fin - anio_inicio) // generacion

# Crear un diccionario para almacenar los resultados
resultados = {tfr: [poblacion_inicial] for tfr in tfr_list}

# Simular para cada generación
for gen in range(1, num_generaciones + 1):
    for tfr in tfr_list:
        # Relación de reemplazo
        relacion = tfr / tasa_reemplazo
        # Población en la siguiente generación
        poblacion_anterior = resultados[tfr][-1]
        poblacion_nueva = poblacion_anterior * relacion
        resultados[tfr].append(poblacion_nueva)

# Generar lista de años para el eje X
años = [anio_inicio + gen * generacion for gen in range(num_generaciones + 1)]

# Graficar los resultados
plt.figure(figsize=(12, 8))
for tfr in tfr_list:
    plt.plot(años, resultados[tfr], marker='o', label=f'TFR = {tfr}')

plt.title('Evolución de la Población hasta el Año 2100 para Diferentes TFR')
plt.xlabel('Año')
plt.ylabel('Población (normalizada a 100%)')
plt.legend()
plt.grid(True)
plt.xticks(años, rotation=45)
plt.tight_layout()
plt.show()
