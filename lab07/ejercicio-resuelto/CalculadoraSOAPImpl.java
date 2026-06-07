import javax.jws.WebService;

@WebService(endpointInterface = "CalculadoraSOAP", targetNamespace = "http://calculadora/")
public class CalculadoraSOAPImpl implements CalculadoraSOAP {
    @Override
    public int sumar(int a, int b) {
        return a + b;
    }
}