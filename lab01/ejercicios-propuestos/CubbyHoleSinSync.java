/**
 * CubbyHoleSinSync – Buffer compartido SIN sincronización.
 *
 * PROPÓSITO DIDÁCTICO: Esta clase reproduce deliberadamente
 * las condiciones de carrera descritas en la guía de laboratorio.
 * NO debe usarse en código de producción.
 *
 * Problemas esperados:
 *  - El Consumidor puede leer el mismo valor más de una vez.
 *  - El Productor puede sobreescribir un valor antes de que
 *    el Consumidor lo haya leído.
 */
public class CubbyHoleSinSync implements ICubbyHole {

    // Valor almacenado en el buffer (capacidad = 1)
    // volatile: fuerza que cada escritura sea inmediatamente visible
    // a todos los hilos (sin caché de CPU de por medio).
    private volatile int contents;

    // volatile es el mínimo necesario para que los hilos se "vean"
    // mutuamente. SIN volatile el JIT puede optimizar el bucle
    // while(available==false) a un loop infinito porque asume que
    // ningún otro hilo modifica la variable (hoisting de la lectura).
    //
    // IMPORTANTE: volatile NO resuelve la condición de carrera
    // (números saltados/duplicados siguen siendo posibles), solo
    // evita el congelamiento por invisibilidad de memoria.
    private volatile boolean available = false;

    /**
     * get() sin sincronización.
     * El Consumidor intenta leer, pero no espera formalmente a que
     * haya un dato disponible → puede leer el mismo dato dos veces.
     */
    public int get() {
        // Sin wait(): si available == false simplemente continúa
        // o entra en un bucle activo (busy-wait) que consume CPU
        while (available == false) {
            // Espera activa (spin-lock) — ineficiente y sin garantías
        }
        available = false;          // Marca como consumido
        
        // Imprime el valor consumido
        int value = contents;
        System.out.println("Consumidor obtiene: " + value);

        // PROBLEMA: entre estas dos líneas otro hilo puede interferir
        return contents;
    }

    /**
     * put() sin sincronización.
     * El Productor escribe sin garantizar que el Consumidor
     * ya leyó el valor anterior → puede sobrescribir datos.
     */
    public void put(int value) {
        while (available == true) {
            // Espera activa — no libera el procesador
        }
        contents = value;              // Escribe el nuevo valor
        available = true;            // Señala que hay dato disponible
        // PROBLEMA: el compilador JIT o la CPU pueden reordenar
        // estas instrucciones sin la barrera de memoria que
        // synchronized provee implícitamente.

        // Imprime confirmación de producción
        System.out.println("Productor pone: " + value);
    }
}