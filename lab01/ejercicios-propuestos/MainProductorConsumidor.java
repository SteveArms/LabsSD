/**
 * MainProductorConsumidor – Punto de entrada del programa.
 *
 * Para probar AMBAS versiones:
 *
 *   Versión SIN sincronización → usar CubbyHoleSinSync
 *   (requiere que Productor y Consumidor usen CubbyHoleSinSync)
 *
 *   Versión CON sincronización → usar CubbyHoleConSync
 *   (requiere que Productor y Consumidor usen CubbyHoleConSync)
 *
 * En este archivo se muestra la versión CON sincronización.
 * Para la versión SIN sync, cambiar CubbyHoleConSync → CubbyHoleSinSync
 * en Productor.java y Consumidor.java, y usar CubbyHoleSinSync abajo.
 */
public class MainProductorConsumidor {

    public static void main(String[] args) {

        // ─── Paso 1: Crear el buffer compartido ────────────────────────
        // Este es el recurso compartido entre Productor y Consumidor.
        // Ambos hilos recibirán una referencia al MISMO objeto.
        //
        // Para versión SIN sincronización:
        //   ICubbyHole cub = new CubbyHoleSinSync();
        //
        // Para versión CON sincronización (activa ahora):
        ICubbyHole cub = new CubbyHoleConSync();

        // ─── Paso 2: Crear los hilos ────────────────────────────────────
        // Se pasa la misma instancia 'cub' a ambos hilos.
        // Número 1 identifica a cada hilo en las impresiones.
        Consumidor cons = new Consumidor(cub, 1);
        Productor  prod = new Productor(cub,  1);

        // ─── Paso 3: Iniciar los hilos ──────────────────────────────────
        // start() NO llama directamente a run().
        // Registra el hilo en el scheduler de la JVM y éste decide
        // cuándo ejecutarlo. El orden de start() no garantiza el
        // orden de ejecución.
        prod.start();   // Arranca el Productor en un hilo separado
        cons.start();   // Arranca el Consumidor en otro hilo separado

        // ─── Paso 4 (opcional): Esperar a que ambos terminen ────────────
        // join() bloquea el hilo main hasta que prod y cons finalicen.
        // Útil para medir el tiempo total de ejecución.
        try {
            long inicio = System.currentTimeMillis();
            prod.join();
            cons.join();
            long fin = System.currentTimeMillis();
            System.out.println("\n─── Programa finalizado en "
                + (fin - inicio) + " ms ───");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}