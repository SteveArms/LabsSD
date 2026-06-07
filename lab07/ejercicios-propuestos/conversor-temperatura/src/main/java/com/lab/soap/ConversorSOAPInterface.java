package com.lab.soap;

import jakarta.jws.WebMethod;
import jakarta.jws.WebService;

@WebService
public interface ConversorSOAPInterface {
    @WebMethod
    double cToF(double celsius);
    
    @WebMethod
    double fToC(double fahrenheit);
}