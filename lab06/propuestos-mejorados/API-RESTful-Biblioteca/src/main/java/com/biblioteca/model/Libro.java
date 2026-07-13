package com.biblioteca.model;

public class Libro {

    private Long id;
    private String titulo;
    private String autor;
    private String isbn;
    private Integer anioPublicacion;
    private Boolean disponible;

    public Libro() {
    }

    public Libro(Long id, String titulo, String autor,
                  String isbn, Integer anioPublicacion,
                  Boolean disponible) {

        this.id = id;
        this.titulo = titulo;
        this.autor = autor;
        this.isbn = isbn;
        this.anioPublicacion = anioPublicacion;
        this.disponible = disponible;
    }

    public Libro(String titulo, String autor,
                  String isbn, Integer anioPublicacion,
                  Boolean disponible) {

        this.titulo = titulo;
        this.autor = autor;
        this.isbn = isbn;
        this.anioPublicacion = anioPublicacion;
        this.disponible = disponible;
    }

    // GETTERS Y SETTERS

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTitulo() {
        return titulo;
    }

    public void setTitulo(String titulo) {
        this.titulo = titulo;
    }

    public String getAutor() {
        return autor;
    }

    public void setAutor(String autor) {
        this.autor = autor;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public Integer getAnioPublicacion() {
        return anioPublicacion;
    }

    public void setAnioPublicacion(Integer anioPublicacion) {
        this.anioPublicacion = anioPublicacion;
    }

    public Boolean getDisponible() {
        return disponible;
    }

    public void setDisponible(Boolean disponible) {
        this.disponible = disponible;
    }
}