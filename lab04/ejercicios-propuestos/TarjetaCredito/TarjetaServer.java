import java.rmi.Naming;

public class TarjetaServer {
    public static void main(String[] args) {
        try {
            TarjetaInterface tarjeta = new TarjetaImpl("María Gómez", 5000.0);
            Naming.rebind("rmi://localhost/TarjetaService", tarjeta);
            System.out.println("Servidor de tarjeta de crédito listo");
            System.out.println("Objeto remoto registrado como: TarjetaService");
        } catch (Exception e) {
            System.err.println("Error en servidor: " + e);
            e.printStackTrace();
        }
    }
}