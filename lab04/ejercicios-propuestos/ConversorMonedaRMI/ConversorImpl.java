import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.rmi.server.RemoteServer;
import java.rmi.server.ServerNotActiveException;
import java.util.logging.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class ConversorImpl extends UnicastRemoteObject implements IConversor {
    private static final double TASA_DOLAR = 0.27;
    private static final double TASA_EURO = 0.25;
    private static final Logger logger = Logger.getLogger("ConversorServer");
    private static final DateTimeFormatter dtf = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    static {
        ConsoleHandler handler = new ConsoleHandler();
        handler.setFormatter(new SimpleFormatter());
        logger.addHandler(handler);
        logger.setLevel(Level.INFO);
    }

    protected ConversorImpl() throws RemoteException {
        super();
    }

    private void log(String msg) {
        String timestamp = LocalDateTime.now().format(dtf);
        logger.info("[" + timestamp + "] " + msg);
    }

    private String obtenerClienteIp() {
        try {
            return RemoteServer.getClientHost();
        } catch (ServerNotActiveException e) {
            return "desconocido";
        }
    }

    @Override
    public double convertirADolares(double montoSoles) throws RemoteException {
        String cliente = obtenerClienteIp();
        if (montoSoles < 0) {
            log("Cliente " + cliente + " intentó monto negativo: " + montoSoles);
            throw new RemoteException("El monto no puede ser negativo");
        }
        double resultado = montoSoles * TASA_DOLAR;
        log("Cliente " + cliente + " convirtió " + montoSoles + " soles -> " + resultado + " USD");
        return resultado;
    }

    @Override
    public double convertirAEuros(double montoSoles) throws RemoteException {
        String cliente = obtenerClienteIp();
        if (montoSoles < 0) {
            log("Cliente " + cliente + " intentó monto negativo: " + montoSoles);
            throw new RemoteException("El monto no puede ser negativo");
        }
        double resultado = montoSoles * TASA_EURO;
        log("Cliente " + cliente + " convirtió " + montoSoles + " soles -> " + resultado + " EUR");
        return resultado;
    }

    @Override
    public double getTasaDolar() throws RemoteException {
        return TASA_DOLAR;
    }

    @Override
    public double getTasaEuro() throws RemoteException {
        return TASA_EURO;
    }
}