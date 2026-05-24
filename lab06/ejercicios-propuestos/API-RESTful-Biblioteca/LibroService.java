package com.biblioteca.service;

import com.biblioteca.model.Libro;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class LibroService {

    private final List<Libro> libros = new ArrayList<>();
    private final AtomicLong contadorId = new AtomicLong(1);

    public LibroService() {

        // Datos de ejemplo
        Libro libro1 = new Libro(
                "Cien años de soledad",
                "Gabriel García Márquez",
                "978-84-376-0494-7",
                1967,
                true
        );
        libro1.setId(contadorId.getAndIncrement());

        Libro libro2 = new Libro(
                "El Quijote",
                "Miguel de Cervantes",
                "978-84-670-4509-3",
                1605,
                true
        );
        libro2.setId(contadorId.getAndIncrement());

        Libro libro3 = new Libro(
                "La sombra del viento",
                "Carlos Ruiz Zafón",
                "978-84-08-05535-0",
                2001,
                true
        );
        libro3.setId(contadorId.getAndIncrement());

        libros.add(libro1);
        libros.add(libro2);
        libros.add(libro3);
    }

    public List<Libro> listarTodos() {
        return new ArrayList<>(libros);
    }

    public Libro buscarPorId(Long id) {
        return libros.stream()
                .filter(libro -> libro.getId().equals(id))
                .findFirst()
                .orElse(null);
    }

    public Libro agregar(Libro libro) {

        libro.setId(contadorId.getAndIncrement());
        libro.setDisponible(true);

        libros.add(libro);

        return libro;
    }

    public Libro actualizar(Long id, Libro libroActualizado) {

        Libro libroExistente = buscarPorId(id);

        if (libroExistente != null) {

            libroExistente.setTitulo(libroActualizado.getTitulo());
            libroExistente.setAutor(libroActualizado.getAutor());
            libroExistente.setIsbn(libroActualizado.getIsbn());
            libroExistente.setAnioPublicacion(
                    libroActualizado.getAnioPublicacion()
            );
            libroExistente.setDisponible(
                    libroActualizado.getDisponible()
            );

            return libroExistente;
        }

        return null;
    }

    public boolean eliminar(Long id) {
        return libros.removeIf(
                libro -> libro.getId().equals(id)
        );
    }
}