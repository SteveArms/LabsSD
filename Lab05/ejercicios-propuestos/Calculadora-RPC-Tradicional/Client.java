import java.rmi.Naming;
import java.util.Scanner;

public class Client {

    public static void main(String[] args) {

        try {

            Calculator calculator =
                    (Calculator) Naming.lookup("rmi://localhost/CalculatorService");

            Scanner sc = new Scanner(System.in);

            System.out.print("Ingrese primer numero: ");
            double a = sc.nextDouble();

            System.out.print("Ingrese segundo numero: ");
            double b = sc.nextDouble();

            // MEMORIA ANTES
            Runtime runtime = Runtime.getRuntime();

            long memoriaAntes =
                    runtime.totalMemory() - runtime.freeMemory();

            // TIEMPO INICIO
            long inicio = System.nanoTime();

            // LLAMADAS RPC
            double mult = calculator.multiply(a, b);
            double div = calculator.divide(a, b);
            double pot = calculator.power(a, b);

            // TIEMPO FIN
            long fin = System.nanoTime();

            // MEMORIA DESPUES
            long memoriaDespues =
                    runtime.totalMemory() - runtime.freeMemory();

            // RESULTADOS
            System.out.println("Multiplicacion: " + mult);
            System.out.println("Division: " + div);
            System.out.println("Potencia: " + pot);

            // METRICAS
            System.out.println("\n===== METRICAS =====");

            System.out.println("Tiempo RPC: "
                    + (fin - inicio) + " ns");

            System.out.println("Tiempo RPC: "
                    + ((fin - inicio)/1_000_000.0) + " ms");

            System.out.println("Memoria usada: "
                    + (memoriaDespues - memoriaAntes) + " bytes");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
