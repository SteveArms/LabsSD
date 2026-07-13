package com.biblioteca.controller;

import com.biblioteca.model.Libro;
import com.biblioteca.service.LibroService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/libros")
@CrossOrigin(origins = "*")
public class LibroController {

    private final LibroService libroService;

    public LibroController(LibroService libroService) {
        this.libroService = libroService;
    }

    @GetMapping
    public ResponseEntity<List<Libro>> listarLibros() {
        return ResponseEntity.ok(libroService.listarTodos());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Libro> obtenerLibro(@PathVariable Long id) {
        Libro libro = libroService.buscarPorId(id);
        if (libro != null) {
            return ResponseEntity.ok(libro);
        }
        return ResponseEntity.notFound().build();
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> agregarLibro(@RequestBody Libro libro) {
        // Validación manual simple (sin necesidad de nuevas dependencias)
        if (libro.getTitulo() == null || libro.getTitulo().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El título es obligatorio"));
        }
        if (libro.getAutor() == null || libro.getAutor().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El autor es obligatorio"));
        }

        Libro nuevoLibro = libroService.agregar(libro);
        Map<String, Object> respuesta = new HashMap<>();
        respuesta.put("mensaje", "Libro agregado exitosamente");
        respuesta.put("libro", nuevoLibro);
        return ResponseEntity.status(HttpStatus.CREATED).body(respuesta);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> actualizarLibro(
            @PathVariable Long id,
            @RequestBody Libro libro) {
        
        // Validación manual simple
        if (libro.getTitulo() == null || libro.getTitulo().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El título es obligatorio"));
        }
        if (libro.getAutor() == null || libro.getAutor().trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "El autor es obligatorio"));
        }

        Libro libroActualizado = libroService.actualizar(id, libro);
        if (libroActualizado != null) {
            Map<String, Object> respuesta = new HashMap<>();
            respuesta.put("mensaje", "Libro actualizado exitosamente");
            respuesta.put("libro", libroActualizado);
            return ResponseEntity.ok(respuesta);
        }
        return ResponseEntity.notFound().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Map<String, String>> eliminarLibro(@PathVariable Long id) {
        boolean eliminado = libroService.eliminar(id);
        if (eliminado) {
            Map<String, String> respuesta = new HashMap<>();
            respuesta.put("mensaje", "Libro eliminado exitosamente");
            return ResponseEntity.ok(respuesta);
        }
        return ResponseEntity.notFound().build();
    }
}