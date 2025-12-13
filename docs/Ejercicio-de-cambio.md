# Ejercicio: Cambio Trending Datasets (3 a 5)

Documento descriptivo del proceso seguido para cambiar la funcionalidad de *Trending Datasets* de mostrar 3 elementos a mostrar 5.

---

## Flujo de Trabajo Paso a Paso

### 1. Gestión del Issue

* Crear un issue utilizando la plantilla correspondiente con el objetivo: **Cambiar top 3 a top 5**.
* Revisar la correcta estructura del issue según las buenas prácticas.
* Mover el issue al estado *In Progress*.

### 2. Creación de Rama de Trabajo

Situarse en la rama principal de desarrollo (*trunk*) y crear una nueva rama para la corrección:

```bash
git checkout 2-poke-hub/trunk
git pull
git checkout -b 2-poke-hub/fix/Cambio-trending-datasets
```

### 3. Desarrollo y Control de Calidad

* Modificar el código para que el sistema muestre **5 datasets** en lugar de 3.
* Verificar que el cambio cumple los requisitos funcionales.
* Ejecutar comprobaciones de formato y pruebas automáticas:

```bash
flake8 app rosemary core                 #Run flake8 for PEP8 linting
black --check app rosemary core          #Verify code formatting with Black
isort --check-only app rosemary core     #Verify import ordering with isort
rosemary test
```

### 4. Commit y Push

Registrar los cambios y subirlos al repositorio remoto:

```bash
git add .
git commit -m "fix: Cambio trending datasets" -m "Actualización de la funcionalidad para mostrar 5 datasets en lugar de 3"
git push origin 2-poke-hub/fix/Cambio-trending-datasets
```

### 5. Revisión y Merge

* Revisar la rama de trabajo y comprobar que la funcionalidad es correcta.
* Integrar los cambios en la rama *trunk*:

```bash
git checkout 2-poke-hub/trunk
git pull
git merge 2-poke-hub/fix/Cambio-trending-datasets
git push
```

### 6. Cierre y Limpieza

* Mover el issue al estado *Done*.
* Eliminar la rama de trabajo tanto en local como en remoto:

```bash
git push origin --delete 2-poke-hub/fix/Cambio-trending-datasets
git branch -d 2-poke-hub/fix/Cambio-trending-datasets
```

---

> **Nota final:** Para desplegar los cambios en la rama `main` (producción), se coordina una fusión conjunta con el responsable correspondiente para evitar conflictos.
