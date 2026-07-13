import re

def validar_datos_estudiante(datos, estudiantes_db, estudiante_id=None):
    required_fields = ['nombre', 'apellido', 'carrera', 'cui']
    
    for campo in required_fields:
        if campo not in datos or not str(datos[campo]).strip():
            return f"El campo '{campo}' es obligatorio."
    
    nombre = str(datos['nombre']).strip()
    apellido = str(datos['apellido']).strip()
    carrera = str(datos['carrera']).strip()
    cui = str(datos['cui']).strip()
    
    if len(nombre) < 2 or len(nombre) > 50:
        return "El nombre debe tener entre 2 y 50 caracteres."
    if len(apellido) < 2 or len(apellido) > 50:
        return "El apellido debe tener entre 2 y 50 caracteres."
    if len(carrera) < 2 or len(carrera) > 50:
        return "La carrera debe tener entre 2 y 50 caracteres."
    if len(cui) != 8:
        return "El CUI debe tener exactamente 8 dígitos."
    if not cui.isdigit():
        return "El CUI debe contener solo números."
    
    patron_letras = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$")
    if not patron_letras.match(nombre):
        return "El nombre solo debe contener letras."
    if not patron_letras.match(apellido):
        return "El apellido solo debe contener letras."
    
    for est_id, est in estudiantes_db.items():
        if est['cui'].lower() == cui.lower() and est_id != estudiante_id:
            return f"El CUI '{cui}' ya está registrado."
            
    return None