import java.rmi.Naming;
import java.util.Scanner;

public class TarjetaClient {
    public static void main(String[] args) {
        try {
            TarjetaInterface tarjeta = (TarjetaInterface) Naming.lookup("rmi://localhost/TarjetaService");
            Scanner sc = new Scanner(System.in);
            int opcion;

            System.out.println("Conectado al servicio de tarjeta de crédito");
            System.out.println("Titular: " + tarjeta.obtenerTitular());

            do {
                System.out.println("\n--- Sistema de Tarjeta de Crédito ---");
                System.out.println("Saldo actual: $" + tarjeta.consultarSaldo());
                System.out.println("1. Realizar pago");
                System.out.println("2. Cargar saldo");
                System.out.println("3. Salir");
                System.out.print("Opción: ");
                opcion = sc.nextInt();

                switch (opcion) {
                    case 1:
                        System.out.print("Monto a pagar: $");
                        double pago = sc.nextDouble();
                        tarjeta.pagar(pago);
                        System.out.println("Pago exitoso. Nuevo saldo: $" + tarjeta.consultarSaldo());
                        break;
                    case 2:
                        System.out.print("Monto a cargar: $");
                        double carga = sc.nextDouble();
                        tarjeta.cargar(carga);
                        System.out.println("Carga exitosa. Nuevo saldo: $" + tarjeta.consultarSaldo());
                        break;
                    case 3:
                        System.out.println("Saliendo del sistema...");
                        break;
                    default:
                        System.out.println("Opción inválida. Intente nuevamente.");
                }
            } while (opcion != 3);
            sc.close();
        } catch (Exception e) {
            System.err.println("Error en cliente: " + e);
            e.printStackTrace();
        }
    }
}