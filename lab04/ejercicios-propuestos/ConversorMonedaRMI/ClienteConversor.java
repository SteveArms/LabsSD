import java.rmi.Naming;
import java.util.InputMismatchException;
import java.util.Scanner;

public class ClienteConversor {
    private static IConversor conversor;
    private static Scanner scanner = new Scanner(System.in);

    public static void main(String[] args) {
        try {
            conversor = (IConversor) Naming.lookup("//localhost/ConversorService");
            System.out.println("=== CONVERSOR DE MONEDA (RMI) ===");
            System.out.println("Conectado al servidor remoto.");
            System.out.println("Tasa actual: 1 sol = " + conversor.getTasaDolar() + " USD");
            System.out.println("Tasa actual: 1 sol = " + conversor.getTasaEuro() + " EUR");
            System.out.println("-----------------------------------");
            
            while (true) {
                mostrarMenu();
                int opcion = leerEntero("Opción: ");
                if (opcion == 3) {
                    System.out.println("¡Hasta luego!");
                    break;
                }
                
                double monto = leerMontoPositivo("Ingrese cantidad en soles (S/): ");
                if (monto < 0) continue; 
                
                try {
                    switch (opcion) {
                        case 1:
                            double usd = conversor.convertirADolares(monto);
                            System.out.printf("S/ %.2f = %.2f USD%n", monto, usd);
                            break;
                        case 2:
                            double eur = conversor.convertirAEuros(monto);
                            System.out.printf("S/ %.2f = %.2f EUR%n", monto, eur);
                            break;
                        default:
                            System.out.println("Opción inválida. Intente de nuevo.");
                    }
                } catch (Exception e) {
                    System.err.println("Error en la conversión remota: " + e.getMessage());
                }
                System.out.println();
            }
        } catch (Exception e) {
            System.err.println("No se pudo conectar al servidor RMI: " + e.getMessage());
            e.printStackTrace();
        } finally {
            scanner.close();
        }
    }
    
    private static void mostrarMenu() {
        System.out.println("--- Menú ---");
        System.out.println("1. Convertir Soles a Dólares");
        System.out.println("2. Convertir Soles a Euros");
        System.out.println("3. Salir");
    }
    
    private static int leerEntero(String mensaje) {
        while (true) {
            System.out.print(mensaje);
            try {
                int valor = scanner.nextInt();
                scanner.nextLine();
                return valor;
            } catch (InputMismatchException e) {
                System.out.println("Error: debe ingresar un número entero.");
                scanner.nextLine(); 
            }
        }
    }
    
    private static double leerMontoPositivo(String mensaje) {
        while (true) {
            System.out.print(mensaje);
            try {
                double monto = scanner.nextDouble();
                scanner.nextLine();
                if (monto < 0) {
                    System.out.println("El monto no puede ser negativo. Intente de nuevo.");
                    continue;
                }
                return monto;
            } catch (InputMismatchException e) {
                System.out.println("Error: debe ingresar un número válido (ej. 100.50).");
                scanner.nextLine();
            }
        }
    }
}