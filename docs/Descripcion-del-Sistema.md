# PokeHub: Descripción Técnica del Sistema

## 1. Introducción y Justificación Metodológica
El proyecto PokeHub representa una evolución estratégica del repositorio base uvlhub.io, impulsada por la necesidad de migrar de una plataforma de almacenamiento pasivo a un **Ecosistema Activo de Servicios especializado en Modelos de Variabilidad Poke**.

El desarrollo se ha llevado a cabo mediante un esfuerzo de ingeniería de software estructurado, gestionado por dos equipos paralelos (**1-poke-hub** y **2-poke-hub**), utilizando el **Feature-Driven Development (FDD)** y un riguroso enfoque de **Gestión de la Configuración (GC)**.

### 1.1. Gestión de Equipos y Estructura Organizativa
La división del trabajo en dos troncales (`1-poke-hub/trunk` y `2-poke-hub/trunk`) converge en la línea principal (`main`). Esto sigue los principios de la Organización del equipo, donde el proyecto se divide en módulos o áreas funcionales para ser desarrollados por equipos cognitivos.

> **El Equipo:** Un equipo se define como un "pequeño número de personas con habilidades complementarias que están comprometidos con un propósito común, un conjunto de objetivos de rendimiento, y un enfoque que los hace mutuamente responsables".

**Gestión de Tareas (Work Items):** El uso de backlogs (GitHub Projects 4 y 6) para listar los Work Items modela el proceso de petición de cambios (**CR**). Cada Work Item representa un Work Package (paquete de trabajo) priorizado, derivado de un Change Request (petición de cambio) que fue investigado y aprobado.

### 1.2. Gestión del Código Fuente y Ramificación
El control de versiones es crucial para gestionar la convergencia de los dos equipos. El sistema utiliza **Git** como Repositorio de Código y adhiere a una política de ramificación estricta mediante EGC Flow.

**Principios de EGC Flow:** El modelo se basa en los siguientes principios, orientados a la velocidad, la calidad y la colaboración:

* **Enfoque en CI/CD:** El flujo está optimizado para proyectos que realizan deploys frecuentes y buscan una integración constante, un enfoque más alineado con el Trunk-Based Development que con el tradicional Gitflow.

* **Rama main siempre desplegable**: La rama main (o master) debe estar siempre en un estado ejecutable/desplegable (verde).

* **Integración Frecuente**: Se requiere hacer merges frecuentes entre las ramas, idealmente cada vez que se finaliza una tarea de una característica, siguiendo el principio clave de la Integración Continua.

* **Uso de Commits Atómicos**: Los commits deben ser atómicos y seguir una guía para sistematizar el trabajo y facilitar el rastreo y la generación de changelogs.

## 2. Infraestructura: Aislamiento, Reproducibilidad e Integración Continua
Las tareas de infraestructura han sentado las bases de un entorno de desarrollo profesional, priorizando la fiabilidad y la **Integración Continua (CI)**.

### 2.1. Infraestructura Aislada (Docker & Reproducibilidad)
La modernización del stack con **Docker** y **Docker Compose** aborda el problema fundamental de la dependencia del entorno, conocido como "en mi máquina funciona".

> **Teoría de Aislamiento:** El uso de contenedores (Docker) garantiza el **Aislamiento** y la **Reproducibilidad** de los artefactos software. Esto permite que el entorno de ejecución sea idéntico en desarrollo, pruebas y producción.

### 2.2. Automatización de Pruebas
La existencia de pruebas unitarias y de integración robustas es un requisito de calidad en la GC.

**Tipos de Pruebas:** Se han aplicado distintos tipos de pruebas para detectar errores, mejorar la calidad y confiabilidad, y observar el cumplimiento de los requisitos:

* **Pruebas Unitarias:** Verificación de la lógica de negocio en módulos aislados.
* **Pruebas de Integración:** Uso de fakenodo y la base de datos para simular flujos de usuario completos.
* **Pruebas de Selenium:** Validan que la aplicación funciona correctamente desde el punto de vista del usuario.

## 3. Work Items Funcionales: La Especialización de PokeHub
Los siguientes Work Items representan las funcionalidades específicas que han transformado el sistema, agrupados por su impacto en la Arquitectura, la Calidad y la Experiencia del Usuario, utilizando el título de la Issue original.

### 3.1. Work Item: Mock Server Fakenodo (#103)
**Contexto (Mandatory):** Este Work Item fue declarado *Mandatory* para el proyecto.

**Funcionalidad:** Fakenodo es una solución avanzada de Gestión de la Configuración enfocada en la robustez de las pruebas.

**Justificación de CI:** La implementación de fakenodo (un mock del servicio Zenodo) es un pilar de la Integración Continua. Al simular el entorno externo de Zenodo, se permite la ejecución de **Builds** y **Pruebas de Integración** repetibles, rápidas y fiables, sin depender de la red o credenciales de terceros.

### 3.2. Work Item: Evolving uvlhub into pokehub (#104)
**Contexto (Mandatory):** Este Work Item fue declarado *Mandatory* para el proyecto.

**Funcionalidad:** Reestructurar uvlhub para que ya no se centre en conjuntos de datos UVL, sino en otro tipo de datos específicos.

**Justificación:** El objetivo es transformarlo en un pokehub, donde diferentes dominios de dpatos puedan tener su propia lógica sin duplicar la plataforma.

### 3.3. Work Item: Trending datasets (#100)
**Funcionalidad:** Ver una clasificación de los conjuntos de datos más vistos o descargados recientemente.

**Justificación:** Descubrir qué es popular en la plataforma.

### 3.4. Work Item: ElasticSearch (#93)
**Funcionalidad:** Integrar ElasticSearch en la búsqueda

**Justificación:** La búsqueda original es limitada. Queremos usar **Elasticsearch** para indexar conjuntos de datos, modelos y usuarios.

### 3.5. Work Item: Dataset Feedback (#79)
**Funcionalidad:** Posibilidad del usuario para poder comentar un conjunto de datos, dar feedback o resolver preguntas.

### 3.6. Work Item: Create communities (#74)
**Funcionalidad:** Poder crear comunidades. Cada comunidad tiene un nombre, una descripción, curadores y una identidad visual, lo que permite a usuarios e instituciones organizar y dar visibilidad a sus contribuciones. Se pueden proponer conjuntos de datos para su incorporación a una comunidad, y su inclusión está sujeta a la aceptación de los curadores, lo que garantiza la coherencia y la calidad del contenido compartido.

**Justificación:** En el contexto de uvlhub, una comunidad es un espacio temático o institucional que agrupa conjuntos de datos relacionados bajo el mismo paraguas, similar a Zenodo.

### 3.7. Work Item: Download Own Dataset (#72)
**Funcionalidad:** Poder crear mi propio “carrito de compras” para descargar mi propio conjunto de datos.

**Justificación:** Poder seleccionar los modelos que me interesan en la plataforma y añadirlos al carrito para, cuando llegue el momento, poder descargar mi propio conjunto de datos haciendo clic en el botón "Descargar modelos".

### 3.8. Work Item: Upload from GitHub / Zip (#70)
**Funcionalidad:** Subir datasets desde un archivo `.zip` o desde un enlace a un repositorio de GitHub.

**Justificación:** Tener varias opciones para subir archivos `.poke` a la plataforma de pokehub.

### 3.9. Work Item: Draft dataset (#68)
**Funcionalidad:** Implementación de la lógica necesaria para que un usuario pueda guardar un dataset como borrador.

**Justificación:** Tener la posibilidad de dejar un dataset como borrador y seguir trabajando en él sin tener que publicarlo en tus datasets.

### 3.10. Work Item: Add download counter for datasets (#105)
**Funcionalidad:** Permite realizar un seguimiento de cuántas veces se ha descargado un conjunto de datos incrementando un contador cada vez que se solicita una descarga.

**Justificación:** Esto ofrece a los autores y usuarios una forma sencilla de medir la popularidad del conjunto de datos.

### 3.11. Work Item: Active session management (#91)
**Funcionalidad:** Poder ver y cerrar sesiones abiertas en otros dispositivos.

**Justificación:** Que el usuario pueda mantener el control sobre la seguridad con respecto a su cuenta.

### 3.12. Work Item: Build my own dataset (#71)
**Funcionalidad:** Implementación de la lógica que permite a un usuario crear su propio conjunto de datos.

**Justificación:** Poder seleccionar los modelos que me interesan en la plataforma y añadirlos al carrito para, cuando llegue el momento, poder crear mi propio conjunto de datos haciendo clic en el botón "Crear mi propio conjunto de datos".

### 3.13. Work Item: View user profile (#69)
**Funcionalidad:** Poder hacer clic en el perfil de un usuario para ver sus conjuntos de datos subidos.

### 3.14. Work Item: Two-factor-authentication (#89)
**Funcionalidad:** Poder habilitar un doble factor de autenticación.

**Justificación:** Ofrecer al usuario una opción para proteger mejor su cuenta.

## 4. Conclusión
El proyecto PokeHub demuestra una aplicación sólida de los principios de Evolución y Gestión de la Configuración. Cada Work Item aporta valor concreto y está alineado con un marco metodológico de madurez, garantizando un desarrollo escalable y confiable.

La migración desde uvlhub.io a PokeHub no solo amplía la funcionalidad, sino que transforma la arquitectura en un **ecosistema activo de servicios** con validación, análisis, autenticación avanzada y flujos centrados en el usuario. La coordinación de los equipos, el uso de ramas sandbox y la integración continua aseguran que cada feature se integre de manera coherente y controlada.

El resultado es una plataforma modular, reproducible y lista para evolucionar hacia nuevos dominios, ofreciendo una base sólida para futuras extensiones en la gestión de modelos Poke y líneas de productos software.