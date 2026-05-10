public interface Calculator extends java.rmi.Remote {
    public int add(int a, int b) throws java.rmi.RemoteException;
    public int sub(int a, int b) throws java.rmi.RemoteException;
    public int mul(int a, int b) throws java.rmi.RemoteException;
    public int div(int a, int b) throws java.rmi.RemoteException;
}