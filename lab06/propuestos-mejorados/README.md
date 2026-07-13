# Laboratorio 06 – REST vs RESTful
## Implementación de APIs distribuidas con Spring Boot y Flask

**Integrantes:**
- Choquehuanca Zapana Hernan Andy
- Cuno Cahuari Armando Steven
- Portugal Portugal Eduardo Sebastian Stephan
- Quispe Marca Edysson Darwin

---

## Descripción general

Este repositorio contiene la implementación de dos APIs RESTful que cumplen con los principios de REST (interfaz uniforme, stateless, uso correcto de verbos HTTP y códigos de estado HTTP). Ambas incluyen un cliente web para interactuar con los servicios.

| Proyecto | Tecnología | Puerto | Cliente web |
|----------|------------|--------|-------------|
| **API Biblioteca** | Spring Boot (Java) | 8080 | `/cliente.html` |
| **API Estudiantes** | Flask (Python) | 5000 | `/` (raíz) |

---

## Requisitos previos

Antes de ejecutar los proyectos, asegúrate de tener instalado:

- Java 17 o superior
- Maven (opcional, si se desea compilar el proyecto)
- Python 3.8 o superior
- pip
- Postman (opcional, recomendado para pruebas)
- Un navegador web moderno

---

## Estructura del proyecto

```text
propuestos-mejorados/
├── API-RESTful-Biblioteca/
│   ├── pom.xml
│   ├── src/
│   │   └── main/
│   │       ├── java/com/biblioteca/
│   │       │   ├── BibliotecaApplication.java
│   │       │   ├── controller/
│   │       │   │   └── LibroController.java
│   │       │   ├── service/
│   │       │   │   └── LibroService.java
│   │       │   ├── model/
│   │       │   │   └── Libro.java
│   │       │   └── exception/
│   │       │       └── GlobalExceptionHandler.java
│   │       └── resources/
│   │           ├── application.properties
│   │           └── static/
│   │               └── cliente.html
│   └── target/
│
└── API-RESTful-Estudiantes/
    ├── app.py
    ├── validador.py
    ├── requirements.txt
    ├── index.html
    ├── style.css
    └── venv/
```

---

# 1. API RESTful Biblioteca (Spring Boot)

## Ejecución

### Paso 1

Abrir una terminal en la carpeta del proyecto.

```bash
cd propuestos-mejorados/API-RESTful-Biblioteca
```

### Opción A – Ejecutar el JAR ya compilado (recomendado)

```bash
java -jar target/biblioteca-api-0.0.1-SNAPSHOT.jar
```

### Opción B – Compilar y ejecutar con Maven

```bash
mvn clean install
mvn spring-boot:run
```

### Acceso

API:

```
http://localhost:8080
```

Cliente web:

```
http://localhost:8080/cliente.html
```

---

## Endpoints

| Método | Endpoint | Descripción |
|---------|----------|-------------|
| GET | `/api/libros` | Listar todos los libros |
| GET | `/api/libros/{id}` | Obtener un libro por ID |
| POST | `/api/libros` | Registrar un libro |
| PUT | `/api/libros/{id}` | Actualizar un libro |
| DELETE | `/api/libros/{id}` | Eliminar un libro |

### Ejemplo JSON para POST y PUT

```json
{
  "titulo": "El principito",
  "autor": "Antoine de Saint-Exupéry",
  "isbn": "978-84-376-0494-7",
  "anioPublicacion": 1943,
  "disponible": true
}
```

---

## Validaciones

- El título es obligatorio.
- El autor es obligatorio.
- Si falta alguno de estos campos, la API responde con:

```
400 Bad Request
```

---

## Ejemplo de respuesta exitosa

```json
{
  "mensaje": "Libro agregado exitosamente",
  "libro": {
    "id": 4,
    "titulo": "El principito",
    "autor": "Antoine de Saint-Exupéry",
    "isbn": "978-84-376-0494-7",
    "anioPublicacion": 1943,
    "disponible": true
  }
}
```

---

# 2. API RESTful Estudiantes (Flask)

## Ejecución

### Paso 1

Abrir una terminal.

```bash
cd propuestos-mejorados/API-RESTful-Estudiantes
```

### Paso 2 (opcional)

Crear un entorno virtual.

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Paso 3

Instalar dependencias.

```bash
pip install -r requirements.txt
```

### Paso 4

Ejecutar la aplicación.

```bash
python app.py
```

### Acceso

API:

```
http://localhost:5000
```

Cliente web:

```
http://localhost:5000
```

---

## Endpoints

| Método | Endpoint | Descripción |
|---------|----------|-------------|
| GET | `/estudiantes` | Listar estudiantes (admite filtros `search` y `carrera`) |
| GET | `/estudiantes/{id}` | Obtener estudiante por ID |
| POST | `/estudiantes` | Registrar estudiante |
| PUT | `/estudiantes/{id}` | Actualizar estudiante |
| DELETE | `/estudiantes/{id}` | Eliminar estudiante |

### Ejemplo JSON para POST y PUT

```json
{
  "nombre": "María",
  "apellido": "González",
  "carrera": "Ingeniería de Sistemas",
  "codigo": "20238183"
}
```

---

## Validaciones

### Código Universitario (CUI)

El campo `codigo` debe cumplir lo siguiente:

- Debe contener exactamente 8 dígitos.
- Solo se aceptan números.
- Los primeros cuatro dígitos representan el año de ingreso.
- El año debe estar entre 2000 y 2030.
- El código debe ser único.

Además:

- Nombre obligatorio.
- Apellido obligatorio.
- Carrera obligatoria.
- Cada uno debe tener entre 2 y 50 caracteres.

Si alguna validación falla, la API responde con:

```
400 Bad Request
```

---

## Ejemplo de respuesta exitosa

```json
{
  "id": 1,
  "nombre": "María",
  "apellido": "González",
  "carrera": "Ingeniería de Sistemas",
  "codigo": "20238183"
}
```

---

# Pruebas con Postman

Para probar ambas APIs:

1. Seleccionar el método HTTP correspondiente.
2. Configurar:

```
Content-Type: application/json
```

3. Enviar el cuerpo en formato JSON cuando corresponda.

### Códigos de respuesta esperados

| Código | Significado |
|---------|-------------|
| 200 OK | Consulta, actualización o eliminación exitosa |
| 201 Created | Registro creado correctamente |
| 400 Bad Request | Error de validación |
| 404 Not Found | Recurso no encontrado |

---

# Manejo de errores

Las dos APIs responden con mensajes JSON.

### Spring Boot

```json
{
  "timestamp": "2026-07-12T19:27:00",
  "status": 400,
  "error": "El título es obligatorio"
}
```

### Flask

```json
{
  "error": "El CUI debe tener exactamente 8 dígitos."
}
```

---

# Características REST implementadas

Ambos proyectos cumplen con las características principales de una API RESTful:

- Arquitectura cliente-servidor.
- Comunicación stateless.
- Uso correcto de los verbos HTTP.
- Recursos identificados mediante URI.
- Respuestas en formato JSON.
- Uso adecuado de códigos de estado HTTP.
- Interfaz uniforme.
- Operaciones CRUD completas.

---

# Notas

- La API Biblioteca almacena la información en memoria mediante una lista.
- La API Estudiantes utiliza un diccionario en memoria.
- No se requiere base de datos para ejecutar el laboratorio.
- Ambos clientes web utilizan `fetch()` para consumir las APIs.
- Las interfaces actualizan la información dinámicamente sin recargar la página.

---

# Tecnologías utilizadas

## API Biblioteca

- Java 17
- Spring Boot
- Maven

## API Estudiantes

- Python 3
- Flask

## Cliente Web

- HTML5
- CSS3
- JavaScript
- Fetch API

---

# Enlaces de interés

- Documentación Spring Boot: https://spring.io/projects/spring-boot
- Documentación Flask: https://flask.palletsprojects.com/
- Postman Learning Center: https://learning.postman.com/
- REST Architectural Style (Roy Fielding): https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm