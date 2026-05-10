import java.rmi.Remote;
import java.rmi.RemoteException;

public interface TarjetaInterface extends Remote {
    double consultarSaldo() throws RemoteException;
    void pagar(double monto) throws RemoteException;
    void cargar(double monto) throws RemoteException;
    String obtenerTitular() throws RemoteException;
}