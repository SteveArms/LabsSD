/**
 * Productor – Hilo que genera enteros del 0 al 9 y los deposita
 * en el buffer compartido CubbyHoleConSync.
 *
 * Hereda de Thread para poder ejecutarse como un hilo independiente.
 * El método run() contiene la lógica que se ejecuta cuando se
 * invoca start() desde la clase principal.
 */
public class Productor extends Thread {

    // Referencia al buffer compartido
    private ICubbyHole cubbyhole;

    // Identificador numérico del productor (útil con múltiples productores)
    private int numero;

    /**
     * Constructor.
     * @param c      Buffer compartido CubbyHoleConSync
     * @param numero Identificador de este productor
     */
    public Productor(ICubbyHole c, int numero) {
        cubbyhole = c;
        this.numero = numero;
    }

    /**
     * run() – Lógica del hilo Productor.
     *
     * Produce los enteros 0..9 en orden:
     *  1. Llama a cubbyhole.put(i) → deposita el valor (bloqueante
     *     si el buffer está lleno en la versión sincronizada).
     *  2. Imprime el valor producido.
     *  3. Duerme un tiempo aleatorio entre 0 y 100 ms para simular
     *     que la producción no es instantánea ni uniforme.
     *
     * La variabilidad en el sleep() hace que la intercalación con
     * el Consumidor sea impredecible, lo que hace visible la
     * condición de carrera en la versión sin sincronización.
     */
    @Override
    public void run() {
        for (int i = 0; i < 10; i++) {

            // Deposita el valor en el buffer compartido
            cubbyhole.put(i);

            // Imprime confirmación de producción
            // System.out.println("Productor #" + this.numero + " pone: " + i);

            try {
                // Pausa aleatoria: simula que producir un ítem toma tiempo
                // Math.random() devuelve [0.0, 1.0) → sleep de 0..99 ms
                sleep((int)(Math.random() * 100));
            } catch (InterruptedException e) {
                // El hilo fue interrumpido externamente; terminamos limpiamente
                Thread.currentThread().interrupt();
                break;
            }
        }
        System.out.println("[Productor #" + numero + "] Terminó de producir.");
    }
}