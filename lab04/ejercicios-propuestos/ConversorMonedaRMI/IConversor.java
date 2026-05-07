import java.rmi.Remote;
import java.rmi.RemoteException;

public interface IConversor extends Remote {
    double convertirADolares(double montoSoles) throws RemoteException;
    double convertirAEuros(double montoSoles) throws RemoteException;
    double getTasaDolar() throws RemoteException;
    double getTasaEuro() throws RemoteException;
}