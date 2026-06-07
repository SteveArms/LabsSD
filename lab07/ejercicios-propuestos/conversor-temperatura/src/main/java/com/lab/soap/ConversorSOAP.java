package com.lab.soap;

import jakarta.jws.WebService;

@WebService(endpointInterface = "com.lab.soap.ConversorSOAPInterface")
public class ConversorSOAP implements ConversorSOAPInterface {
    
    public double cToF(double celsius) {
        return (celsius * 9/5) + 32;
    }
    
    public double fToC(double fahrenheit) {
        return (fahrenheit - 32) * 5/9;
    }
}