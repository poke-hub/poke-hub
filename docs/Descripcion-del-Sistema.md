# PokeHub: Descripción Técnica del Sistema

## 1. Introducción y Justificación Metodológica
El proyecto PokeHub representa una evolución estratégica del repositorio base uvlhub.io, impulsada por la necesidad de migrar de una plataforma de almacenamiento pasivo a un **Ecosistema Activo de Servicios especializado en Modelos de Variabilidad Poke**.

El desarrollo se ha llevado a cabo mediante un esfuerzo de ingeniería de software estructurado, gestionado por dos equipos paralelos (**1-poke-hub** y **2-poke-hub**), utilizando el **Feature-Driven Development (FDD)** y un riguroso enfoque de **Gestión de la Configuración (GC)**.

### 1.1. Gestión de Equipos y Estructura Organizativa
La división del trabajo en dos troncales (`1-poke-hub/trunk` y `2-poke-hub/trunk`) converge en la línea principal (`main`). Esto sigue los principios de la Organización del equipo, donde el proyecto se divide en módulos o áreas funcionales para ser desarrollados por equipos cognitivos.

> **El Equipo:** Un equipo se define como un "pequeño número de personas con habilidades complementarias que están comprometidos con un propósito común, un conjunto de objetivos de rendimiento, y un enfoque que los hace mutuamente responsables".

**Gestión de Tareas (Work Items):** El uso de backlogs para listar los Work Items modela el proceso de petición de cambios. Cada Work Item representa un paquete de trabajo.

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
* **Pruebas de carga:** Validan la estabilidad y rendimiento del sistema bajo una carga de usuarios controlada.

## 3. Cambios Desarrollados y Arquitectura del Sistema
Esta sección detalla explícitamente los cambios funcionales y arquitectónicos implementados en el proyecto (Work Items). El sistema ha evolucionado desde un repositorio genérico a una plataforma especializada (**PokeHub**), integrando nuevos subsistemas de búsqueda, gestión social y seguridad.

A continuación, se enumeran los componentes desarrollados y su impacto en el sistema global:

### 3.1. Evolución del Núcleo y Arquitectura de Datos
El cambio fundamental del sistema reside en la redefinición de su modelo de datos y su integración con servicios externos simulados.

*   **Transformación a PokeHub (Especialización del Dominio):**
    *   *Descripción:* Se ha reestructurado la lógica central de `uvlhub` para abandonar el enfoque genérico en conjuntos de datos UVL y centrarse en modelos de variabilidad "Poke".
    *   *Impacto Técnico:* Esto implicó la modificación de los modelos de base de datos (ORM), las validaciones de entrada y la interfaz de usuario para reflejar la nueva terminología y estructura de datos específica del dominio Poke, evitando la duplicidad de la plataforma para diferentes dominios.

*   **Integración de Mock Server (Fakenodo):**
    *   *Descripción:* Desarrollo e integración de un servicio contenedorizado que simula la API de Zenodo.
    *   *Impacto Arquitectónico:* Este componente es crítico para la arquitectura de pruebas. Desacopla el entorno de desarrollo y CI de la disponibilidad de servicios externos, permitiendo la ejecución de pruebas de integración deterministas y rápidas sin necesidad de credenciales reales ni conexión a internet.

*   **Motor de Búsqueda Avanzada (ElasticSearch):**
    *   *Descripción:* Integración de un clúster de ElasticSearch para reemplazar o aumentar las capacidades de búsqueda nativas de la base de datos relacional.
    *   *Impacto Funcional:* Permite la indexación y búsqueda eficiente de conjuntos de datos, modelos y usuarios, ofreciendo resultados más relevantes y rápidos que las consultas SQL tradicionales, escalando mejor con el volumen de datos.

### 3.2. Subsistema de Gestión de Datasets y Flujos de Trabajo
Se han desarrollado nuevas vías para la ingestión, gestión y descarga de información, flexibilizando cómo los usuarios interactúan con los datos.

*   **Carga desde Fuentes Externas (GitHub / Zip):**
    *   *Funcionalidad:* Se implementaron adaptadores para permitir la ingesta de datasets directamente desde archivos `.zip` o mediante la vinculación de repositorios de GitHub.
    *   *Beneficio:* Facilita la migración de datos existentes y la integración con flujos de trabajo de desarrollo de software externos.

*   **Sistema de Borradores (Draft Dataset):**
    *   *Funcionalidad:* Implementación de un estado intermedio en el ciclo de vida del dataset. Los usuarios pueden guardar su progreso sin publicar, permitiendo la edición asíncrona y la revisión antes de hacer públicos los datos.

*   **Creación y Descarga de Datasets Personalizados:**
    *   *Funcionalidad:* Se ha desarrollado una lógica de "carrito de compras" para modelos.
        *   *Build my own dataset:* Permite seleccionar modelos individuales de diferentes fuentes para componer un nuevo dataset derivado.
        *   *Download Own Dataset:* Permite la descarga empaquetada de esta selección personalizada.
    *   *Impacto:* Transforma la plataforma de un repositorio de lectura a una herramienta de composición de datos.

### 3.3. Subsistema Social y de Comunidad
Para fomentar la colaboración, se han añadido capas sociales sobre la gestión de datos pura.

*   **Gestión de Comunidades:**
    *   *Descripción:* Creación de espacios temáticos o institucionales con identidad visual propia, descripción y roles de administración (curadores).
    *   *Flujo:* Los usuarios pueden proponer datasets para su inclusión en comunidades, y los curadores actúan como filtro de calidad, aceptando o rechazando las propuestas. Esto introduce un flujo de moderación distribuida.
    *   *Funcionalidades Adicionales:*
        *   **Notificaciones de Comunidad:** El sistema notifica por correo electrónico al usuario cuando su dataset ha sido aceptado en una comunidad, manteniéndolo informado sobre el estado de su contribución.
        *   **Revisión de Solicitudes:** Los curadores disponen de herramientas para revisar y moderar las peticiones de inclusión de datasets, asegurando la consistencia y calidad del contenido de la comunidad.
        *   **Seguir Comunidades:** Los usuarios pueden seguir comunidades específicas para recibir notificaciones por correo electrónico cada vez que se añade un nuevo dataset a ellas, facilitando el seguimiento de la actividad sin revisiones manuales constantes.

*   **Feedback (Dataset Feedback):**
    *   *Descripción:* Sistema de comentarios asociado a cada dataset.
    *   *Beneficio:* Habilita la comunicación bidireccional entre autores y consumidores, facilitando la resolución de dudas y la mejora continua de los modelos.

*   **Métricas de Popularidad (Trending & Counters):**
    *   *Descripción:* Implementación de contadores de descargas atómicos y algoritmos para clasificar los datasets "Trending" (tendencia).
    *   *Impacto:* Proporciona heurísticas de calidad y relevancia a los usuarios, destacando el contenido más valioso de la plataforma.

*   **Perfiles de Usuario Públicos (View user profile):**
    *   *Descripción:* Vistas dedicadas para visualizar todas las contribuciones de un usuario específico, fomentando la reputación dentro de la plataforma.

### 3.4. Subsistema de Seguridad y Sesión
Se ha robustecido la capa de autenticación y autorización para cumplir con estándares de seguridad modernos.

*   **Autenticación de Doble Factor (2FA):**
    *   *Descripción:* Integración de un segundo paso de verificación en el proceso de login, aumentando significativamente la seguridad de las cuentas de usuario frente a compromisos de contraseñas.

*   **Gestión Activa de Sesiones:**
    *   *Descripción:* Panel de control que permite al usuario visualizar todas las sesiones activas en diferentes dispositivos y revocar el acceso remotamente.
    *   *Impacto:* Otorga al usuario control total sobre la seguridad de su acceso, fundamental en entornos distribuidos.

## 4. Conclusión
El proyecto PokeHub demuestra una aplicación sólida de los principios de Evolución y Gestión de la Configuración. Cada cambio desarrollado aporta valor concreto y está alineado con un marco metodológico de madurez, garantizando un desarrollo escalable y confiable.

La migración desde uvlhub.io a PokeHub no solo amplía la funcionalidad, sino que transforma la arquitectura en un **ecosistema activo de servicios** con validación, análisis, autenticación avanzada y flujos centrados en el usuario. La coordinación de los equipos, el uso de ramas sandbox y la integración continua aseguran que cada feature se integre de manera coherente y controlada.

El resultado es una plataforma modular, reproducible y lista para evolucionar hacia nuevos dominios, ofreciendo una base sólida para futuras extensiones en la gestión de modelos Poke y líneas de productos software.