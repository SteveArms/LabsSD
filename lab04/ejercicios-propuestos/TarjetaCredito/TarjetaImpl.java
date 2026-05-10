import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

public class TarjetaImpl extends UnicastRemoteObject implements TarjetaInterface {
    private String titular;
    private double saldo;

    public TarjetaImpl(String titular, double saldoInicial) throws RemoteException {
        super();
        this.titular = titular;
        this.saldo = saldoInicial;
    }

    @Override
    public double consultarSaldo() throws RemoteException {
        return saldo;
    }

    @Override
    public void pagar(double monto) throws RemoteException {
        if (monto > saldo) {
            throw new RemoteException("Saldo insuficiente. Saldo actual: $" + saldo);
        }
        saldo -= monto;
        System.out.println("[SERVER] Pago realizado: $" + monto);
    }

    @Override
    public void cargar(double monto) throws RemoteException {
        if (monto <= 0) {
            throw new RemoteException("Monto inválido. Debe ser mayor a 0");
        }
        saldo += monto;
        System.out.println("[SERVER] Carga realizada: $" + monto);
    }

    @Override
    public String obtenerTitular() throws RemoteException {
        return titular;
    }
}