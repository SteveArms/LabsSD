import javax.jws.WebMethod;
import javax.jws.WebService;

@WebService(targetNamespace = "http://calculadora/")
public interface CalculadoraSOAP {
    @WebMethod
    int sumar(int a, int b);
}