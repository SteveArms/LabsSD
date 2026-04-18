/**
 * Consumidor – Hilo que retira enteros del buffer compartido
 * y los "procesa" (en este caso, simplemente los imprime).
 *
 * El Consumidor está diseñado para ser "hambriento": intenta leer
 * tan pronto como hay un dato disponible, sin pausa deliberada.
 * Esto maximiza la probabilidad de condición de carrera en la
 * versión sin sincronización.
 */
public class Consumidor extends Thread {

    // Referencia al buffer compartido (el mismo objeto que usa el Productor)
    private ICubbyHole cubbyhole;

    // Identificador numérico del consumidor
    private int numero;

    /**
     * Constructor.
     * @param c      Buffer compartido CubbyHoleConSync
     * @param numero Identificador de este consumidor
     */
    public Consumidor(ICubbyHole c, int numero) {
        cubbyhole = c;
        this.numero = numero;
    }

    /**
     * run() – Lógica del hilo Consumidor.
     *
     * Lee 10 valores del buffer en orden:
     *  1. Llama a cubbyhole.get() → obtiene el próximo valor
     *     (bloqueante si el buffer está vacío en la versión sync).
     *  2. Imprime el valor obtenido.
     *
     * No hay sleep(): el Consumidor es intencionalmente más rápido
     * que el Productor para exponer condiciones de carrera.
     */
    @Override
    public void run() {
        int value = 0;

        for (int i = 0; i < 10; i++) {

            // Obtiene el siguiente valor del buffer compartido
            value = cubbyhole.get();

            // Imprime el valor consumido
            // System.out.println("Consumidor #" + this.numero + " obtiene: " + value);
        }
        System.out.println("[Consumidor #" + numero + "] Terminó de consumir.");
    }
}