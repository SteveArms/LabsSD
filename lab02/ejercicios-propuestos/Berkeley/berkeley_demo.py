import time
import random
from berkeley_node import BerkeleyNode

NUM_NODES = 4
MASTER_ID = 0

base = int(time.time() * 1000) # tiempo base en ms (simula el tiempo real del sistema)
nodes = []

# crear nodos con deriva aleatoria entre -1500 y +1500 ms
for i in range(NUM_NODES):
    offset = random.randint(-1500, 1500)
    node = BerkeleyNode(i, base, offset, MASTER_ID)
    nodes.append(node)
    node.start()

time.sleep(1.5)   # esperar a que todos los hilos estén listos

# el maestro inicia la sincronización
master = nodes[MASTER_ID]
print("\n===== Iniciando sincronización de Berkeley =====\n")
master.synchronize(nodes)
print("\n===== Fin de la sincronización =====\n")