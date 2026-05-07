import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class ServidorConversor {
    public static void main(String[] args) {
        try {
            LocateRegistry.createRegistry(1099);
            System.out.println("Registro RMI iniciado en puerto 1099");
            IConversor conversor = new ConversorImpl();
            Naming.rebind("//localhost/ConversorService", conversor);
            System.out.println("Servicio de conversor listo. Esperando clientes...");
        } catch (Exception e) {
            System.err.println("Error en servidor: " + e.getMessage());
            e.printStackTrace();
        }
    }
}