package com.biblioteca;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;

@SpringBootApplication
public class BibliotecaApplication {
    public static void main(String[] args) {
        SpringApplication.run(BibliotecaApplication.class, args);
        System.out.println("📚 API Biblioteca RESTful ejecutándose en http://localhost:8080");
        System.out.println("📖 Cliente web: http://localhost:8080/cliente.html");
        System.out.println("🔗 Endpoints disponibles:");
        System.out.println("   GET    /api/libros");
        System.out.println("   GET    /api/libros/{id}");
        System.out.println("   POST   /api/libros");
        System.out.println("   PUT    /api/libros/{id}");
        System.out.println("   DELETE /api/libros/{id}");
    }
}