import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class Server {

    public static void main(String[] args) {

        try {

            LocateRegistry.createRegistry(1099);

            CalculatorImpl calculator = new CalculatorImpl();

            Naming.rebind("rmi://localhost/CalculatorService", calculator);

            System.out.println("Servidor RMI activo");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
