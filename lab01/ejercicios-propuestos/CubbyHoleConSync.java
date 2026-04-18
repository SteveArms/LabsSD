/**
 * CubbyHoleConSync – Buffer compartido CON sincronización completa.
 *
 * Implementa el patrón Monitor de Java:
 *  - synchronized  → garantiza exclusión mutua (un hilo a la vez).
 *  - wait()        → libera el monitor y suspende el hilo hasta
 *                    recibir una notificación.
 *  - notifyAll()   → despierta todos los hilos en espera para que
 *                    compitan de nuevo por el monitor.
 *
 * Invariante garantizada:
 *  Cada valor producido por el Productor es leído exactamente
 *  una vez por el Consumidor.
 */
public class CubbyHoleConSync implements ICubbyHole {

    // Valor almacenado en el buffer (capacidad = 1 elemento)
    private int contents;

    // Estado del buffer:
    //   false → vacío  (el Productor puede escribir)
    //   true  → lleno  (el Consumidor puede leer)
    private boolean available = false;

    // ──────────────────────────────────────────────────────────────
    // get() — Llamado por el Consumidor
    // ──────────────────────────────────────────────────────────────
    public synchronized int get() {

        // ① El Consumidor adquiere el monitor de este objeto.
        //    Ningún otro hilo puede entrar a get() o put() mientras
        //    el Consumidor esté dentro.

        // ② Si el buffer está vacío, espera activamente hasta
        //    que el Productor notifique que hay un dato nuevo.
        while (available == false) {
            try {
                // wait() hace DOS cosas atómicamente:
                //  a) Libera el monitor (permite que put() entre).
                //  b) Suspende el hilo Consumidor hasta recibir notify.
                wait();
            } catch (InterruptedException e) {
                // Restablece el flag de interrupción y sale
                Thread.currentThread().interrupt();
            }
        }

        // ③ Hay un dato disponible: lo marca como consumido.
        available = false;

        // Imprime el valor consumido
        int value = contents;
        System.out.println("Consumidor obtiene: " + value);

        // ④ Notifica al Productor que el buffer está libre.
        //    notifyAll() despierta todos los hilos en espera
        //    (más seguro que notify() cuando hay varios hilos).
        notifyAll();

        // ⑤ Devuelve el valor y libera el monitor.
        return contents;
    }

    // ──────────────────────────────────────────────────────────────
    // put() — Llamado por el Productor
    // ──────────────────────────────────────────────────────────────
    public synchronized void put(int value) {

        // ① El Productor adquiere el monitor de este objeto.

        // ② Si el buffer ya tiene un dato no consumido, espera.
        while (available == true) {
            try {
                // wait() libera el monitor y suspende el Productor.
                // El Consumidor puede ahora entrar a get().
                wait();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        // ③ El buffer está libre: escribe el nuevo valor.
        contents = value;

        // ④ Señala que hay un dato listo para consumir.
        available = true;

        // Imprime confirmación de producción
        System.out.println("Productor pone: " + value);

        // ⑤ Notifica al Consumidor que hay un dato nuevo disponible.
        notifyAll();

        // ⑥ Al salir del método, el monitor se libera automáticamente.
    }
}