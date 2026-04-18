/**
 * ICubbyHole – Interfaz para el buffer compartido.
 * * Define el contrato de comunicación entre Productor y Consumidor, 
 * permitiendo alternar entre implementaciones con y sin sincronización.
 */
public interface ICubbyHole {

    /**
     * Recupera el valor almacenado en el buffer.
     * @return Valor entero obtenido.
     */
    int get();

    /**
     * Deposita un nuevo valor en el buffer.
     * @param value Entero a almacenar.
     */
    void put(int value);
}