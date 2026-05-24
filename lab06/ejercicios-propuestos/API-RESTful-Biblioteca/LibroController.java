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
@CrossOrigin(origins = "*") // Permitir peticiones desde cualquier origen
public class LibroController {
    
    private final LibroService libroService;
    
    public LibroController(LibroService libroService) {
        this.libroService = libroService;
    }
    
    // GET /api/libros - Listar todos los libros
    @GetMapping
    public ResponseEntity<List<Libro>> listarLibros() {
        List<Libro> libros = libroService.listarTodos();
        return ResponseEntity.ok(libros);
    }
    
    // GET /api/libros/{id} - Buscar libro por ID
    @GetMapping("/{id}")
    public ResponseEntity<Libro> obtenerLibro(@PathVariable Long id) {
        Libro libro = libroService.buscarPorId(id);
        if (libro != null) {
            return ResponseEntity.ok(libro);
        }
        return ResponseEntity.notFound().build();
    }
    
    // POST /api/libros - Agregar nuevo libro
    @PostMapping
    public ResponseEntity<Map<String, Object>> agregarLibro(@RequestBody Libro libro) {
        Libro nuevoLibro = libroService.agregar(libro);
        Map<String, Object> respuesta = new HashMap<>();
        respuesta.put("mensaje", "Libro agregado exitosamente");
        respuesta.put("libro", nuevoLibro);
        return ResponseEntity.status(HttpStatus.CREATED).body(respuesta);
    }
    
    // PUT /api/libros/{id} - Actualizar libro existente
    @PutMapping("/{id}")
    public ResponseEntity<Map<String, Object>> actualizarLibro(
            @PathVariable Long id, 
            @RequestBody Libro libro) {
        Libro libroActualizado = libroService.actualizar(id, libro);
        if (libroActualizado != null) {
            Map<String, Object> respuesta = new HashMap<>();
            respuesta.put("mensaje", "Libro actualizado exitosamente");
            respuesta.put("libro", libroActualizado);
            return ResponseEntity.ok(respuesta);
        }
        return ResponseEntity.notFound().build();
    }
    
    // DELETE /api/libros/{id} - Eliminar libro
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