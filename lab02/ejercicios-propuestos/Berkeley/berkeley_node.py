import threading
import time
# import random

class BerkeleyNode(threading.Thread):
    def __init__(self, node_id, base_time, initial_offset, master_id):
        threading.Thread.__init__(self)
        self.id = node_id
        self.clock = base_time + initial_offset # reloj físico
        self.master_id = master_id
        self.is_master = (node_id == master_id)
        self.network_delay = 10 + node_id * 5   # latencia simulada en ms
        self.lock = threading.Lock()

    def run(self):
        # solo mostrar estado inicial
        role = "MAESTRO" if self.is_master else "ESCLAVO"
        print(f"{role} Node-{self.id}  reloj inicial: {self.clock}")

    def get_clock(self):
        with self.lock:
            return self.clock

    def update_clock(self, new_value):
        with self.lock:
            self.clock = new_value
            print(f"ESCLAVO Node-{self.id}  reloj actualizado a {self.clock}")

    def request_time_from_slave(self, slave):
        # simula el tiempo de ida y vuelta
        request_sent = time.time() * 1000
        slave_time = slave.get_clock()
        request_received = time.time() * 1000
        rtt = request_received - request_sent
        estimated_time = slave_time + (rtt / 2)
        delay = rtt / 2
        return estimated_time, delay

    def synchronize(self, all_nodes):
        if not self.is_master:
            print("ERROR: este nodo no es maestro")
            return

        reported_times = [] # para almacenar las horas reportadas por cada nodo
        delays = [] # para almacenar los retrasos estimados de cada nodo

        # recolectar horas de todos los nodos (incluyéndose a sí mismo)
        for node in all_nodes:
            if node.id == self.id:
                reported_times.append(self.clock)
                delays.append(0)
            else:
                slave_time, delay = self.request_time_from_slave(node)
                reported_times.append(slave_time)
                delays.append(delay)
                print(f"MAESTRO MSG Node-{node.id}  hora estimada: {int(slave_time)}  (delay {int(delay)} ms)")

        # calcular promedio
        avg_time = sum(reported_times) // len(reported_times)
        print(f"\nMAESTRO CALC  Hora objetivo (promedio): {avg_time}")

        # enviar órdenes de ajuste
        for i, node in enumerate(all_nodes):
            diff = avg_time - reported_times[i]
            # En el caso del maestro, ajusta su propio reloj
            if node.id == self.id:
                with self.lock:
                    self.clock = avg_time
                print(f"MAESTRO ACT  Node-{self.id}  ajusta su reloj a {avg_time}  (diff {diff})")
            else:
                # Enviar orden de ajuste al esclavo (simulado por llamada directa)
                new_clock = node.get_clock() + diff
                node.update_clock(new_clock)
                print(f"MAESTRO ORDEN Node-{node.id}  debe ajustar en {diff} ms")