import re

# Valida los datos recibidos de un estudiante y comprueba la unicidad del codigo
def validar_datos_estudiante(datos, estudiantes_db, estudiante_id=None):
    required_fields = ['nombre', 'apellido', 'carrera', 'codigo']
    
    # Validar campos obligatorios y no vacios
    for campo in required_fields:
        if campo not in datos or not str(datos[campo]).strip():
            return f"El campo '{campo}' es obligatorio."
    
    nombre = str(datos['nombre']).strip()
    apellido = str(datos['apellido']).strip()
    carrera = str(datos['carrera']).strip()
    codigo = str(datos['codigo']).strip()
    
    # Validar longitudes minimas y maximas
    if len(nombre) < 2 or len(nombre) > 50:
        return "El nombre debe tener entre 2 y 50 caracteres."
    if len(apellido) < 2 or len(apellido) > 50:
        return "El apellido debe tener entre 2 y 50 caracteres."
    if len(carrera) < 2 or len(carrera) > 50:
        return "La carrera debe tener entre 2 y 50 caracteres."
    if len(codigo) < 5 or len(codigo) > 15:
        return "El código debe tener entre 5 y 15 caracteres."
        
    # Validar formato alfanumerico del codigo
    if not codigo.isalnum():
        return "El código debe ser alfanumérico."
        
    # Validar que nombre y apellido contengan solo letras y espacios
    patron_letras = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
    if not patron_letras.match(nombre):
        return "El nombre solo debe contener letras."
    if not patron_letras.match(apellido):
        return "El apellido solo debe contener letras."
        
    # Validar unicidad del codigo de alumno
    for est_id, est in estudiantes_db.items():
        if est['codigo'].lower() == codigo.lower() and est_id != estudiante_id:
            return f"El código '{codigo}' ya está registrado."
            
    return None
