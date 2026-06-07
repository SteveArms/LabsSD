package com.lab.soap;

import java.net.URL;
import java.util.Scanner;

import javax.xml.namespace.QName;

import jakarta.xml.ws.Service;

public class ClienteSOAP {
    public static void main(String[] args) throws Exception {
        URL url = new URL("http://localhost:8080/conversor?wsdl");
        QName qname = new QName("http://soap.lab.com/", "ConversorSOAPService");
        Service service = Service.create(url, qname);
        ConversorSOAPInterface conv = service.getPort(ConversorSOAPInterface.class);

        Scanner scanner = new Scanner(System.in);
        int opcion;
        double valor;

        System.out.println("CONVERSOR DE TEMPERATURAS - SOAP");

        do {
            System.out.println("\n1. Celsius -> Fahrenheit");
            System.out.println("2. Fahrenheit -> Celsius");
            System.out.println("0. Salir");
            System.out.print("Opción: ");
            opcion = scanner.nextInt();

            switch (opcion) {
                case 1:
                    System.out.print("Grados Celsius: ");
                    valor = scanner.nextDouble();
                    System.out.printf("%.2f °C = %.2f °F\n", valor, conv.cToF(valor));
                    break;
                case 2:
                    System.out.print("Grados Fahrenheit: ");
                    valor = scanner.nextDouble();
                    System.out.printf("%.2f °F = %.2f °C\n", valor, conv.fToC(valor));
                    break;
                case 0:
                    System.out.println("Programa terminado.");
                    break;
                default:
                    System.out.println("Opción inválida.");
            }
        } while (opcion != 0);

        scanner.close();
    }
}