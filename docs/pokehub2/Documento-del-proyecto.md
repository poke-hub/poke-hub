# Índice

1. [Indicadores del proyecto](#indicadores-del-proyecto-poke-hub-2)
2. [Integración con otros equipos](#integración-con-otros-equipos)
3. [Resumen Ejecutivo](#resumen-ejecutivo-pokehubio)

4. [Arquitectura del Sistema y Tecnologías Clave](#1-arquitectura-del-sistema-y-tecnologías-clave)
   - 4.1. [Backend y Frameworks](#backend-y-frameworks)
   - 4.2. [Base de Datos](#base-de-datos)
   - 4.3. [Contenedorización](#contenedorización)
   - 4.4. [Búsqueda y Análisis](#búsqueda-y-análisis)

5. [Modelo de Dominio y Gestión de Datos](#2-modelo-de-dominio-y-gestión-de-datos)
   - 5.1. [La Entidad PokeModel y el Formato `.poke`](#la-entidad-pokemodel-y-el-formato-poke)
   - 5.2. [Datasets y Metadatos](#datasets-y-metadatos)
   - 5.3. [Autoría y Métricas](#autoría-y-métricas)

6. [Integración con Repositorios Externos](#3-integración-con-repositorios-externos)

7. [Ingeniería de Software y Herramientas DevOps](#4-ingeniería-de-software-y-herramientas-devops)
   - 7.1. [Rosemary CLI](#rosemary-cli)
   - 7.2. [Testing Automatizado](#testing-automatizado)

8. [Descripción del Sistema](#descripción-del-sistema-1500-palábras-aproximadamente)
   - 8.1. [Introducción y Justificación Metodológica](#1-introducción-y-justificación-metodológica)
     - 8.1.1. [Gestión de Equipos y Estructura Organizativa](#11-gestión-de-equipos-y-estructura-organizativa)
     - 8.1.2. [Gestión del Código Fuente y Ramificación](#12-gestión-del-código-fuente-y-ramificación)
   - 8.2. [Infraestructura e Integración Continua](#2-infraestructura-aislamiento-reproducibilidad-e-integración-continua)
     - 8.2.1. [Infraestructura Aislada](#21-infraestructura-aislada-docker--reproducibilidad)
     - 8.2.2. [Automatización de Pruebas](#22-automatización-de-pruebas)
   - 8.3. [Cambios Desarrollados y Arquitectura del Sistema](#3-cambios-desarrollados-y-arquitectura-del-sistema)
     - 8.3.1. [Evolución del Núcleo y Arquitectura de Datos](#31-evolución-del-núcleo-y-arquitectura-de-datos)
     - 8.3.2. [Gestión de Datasets y Flujos de Trabajo](#32-subsistema-de-gestión-de-datasets-y-flujos-de-trabajo)
     - 8.3.3. [Subsistema Social y de Comunidad](#33-subsistema-social-y-de-comunidad)
     - 8.3.4. [Subsistema de Seguridad y Sesión](#34-subsistema-de-seguridad-y-sesión)
   - 8.4. [Conclusión](#4-conclusión)

9. [Visión Global del Proceso de Desarrollo](#visión-global-del-proceso-de-desarrollo)
   - 9.1. [Planificación y Gestión de Tareas](#1-planificación-y-gestión-de-tareas)
   - 9.2. [Estrategia de Ramificación: EGC Flow](#2-estrategia-de-ramificación-egc-flow)
   - 9.3. [Ciclo de Vida de una Funcionalidad](#3-ciclo-de-vida-de-una-funcionalidad-trabajo-en-parejas)
     - 9.3.1. [Desarrollo Colaborativo](#31-desarrollo-colaborativo-pair-programming)
     - 9.3.2. [Integración Continua](#32-integración-continua-ci)
     - 9.3.3. [Integración en Trunk](#33-integración-en-trunk-sin-pull-request)
   - 9.4. [Integración Global y Despliegue a Producción](#4-integración-global-y-despliegue-a-producción)
     - 9.4.1. [Sincronización hacia `main`](#41-sincronización-coordinada-hacia-main)
     - 9.4.2. [Despliegue Continuo](#42-despliegue-continuo-cd)
   - 9.5. [Caso Práctico: Cambio Trending Datasets](#5-caso-práctico-flujo-completo-de-un-cambio)

10. [Entorno de Desarrollo](#entorno-de-desarrollo-pokehub)
    - 10.1. [Stack Tecnológico y Versiones](#stack-tecnológico-y-versiones)
    - 10.2. [Arquitectura de Servicios](#arquitectura-de-servicios)
    - 10.3. [Herramienta de Gestión: Rosemary](#herramienta-de-gestión-rosemary)
    - 10.4. [Estrategia de Calidad](#estrategia-de-calidad-testing)
    - 10.5. [Guía de Instalación y Despliegue](#guía-de-instalación-y-despliegue)
    - 10.6. [Consideraciones Técnicas Adicionales](#consideraciones-técnicas-adicionales)

11. [Ejercicio: Cambio Trending Datasets](#ejercicio-cambio-trending-datasets-3-a-5-poke-hub-2)
    - 11.1. [Flujo de Trabajo Paso a Paso](#flujo-de-trabajo-paso-a-paso)

12. [Conclusiones y Trabajo Futuro](#conclusiones-y-trabajo-futuro)

## Indicadores del proyecto (poke-hub-2)

Miembro del equipo  | Horas | Commits | LoC | Test | Issues | Work Item| Dificultad
------------- | ------------- | ------------- | ------------- | ------------- | ------------- |  ------------- |  ------------- | 
[Amador Calzadilla, Kevin](https://github.com/kevamacal) | 26 | 8 | 717 | 15 | 7 | Trending Datasets, Active session management | M, H |
[Bermúdez Imaz, Pablo](https://github.com/Pablobi) | 28 | 17 | 1469 | 5 | 8 | Draft dataset, Communities | M, L |
[Cruz Ramírez, Carlos Javier](https://github.com/carcruram) | 26 | 17 | 1196 | 5 | 9 | Download Zip/Github, Comments | H, L |
[Guerra Prada, Héctor](https://github.com/HectorGuePra) | 40 | 42 | 843 | 6 | 11 | Fakenodo, Trending Datasets, Active session management | Mandatory, M, H |
[Padilla Gómez, Marcos](https://github.com/maarcoopg) | 21 | 34 | 1037 | 7 | 11 | Draft dataset, Communities | M, L |
[Zurita Fernández, Manuel](https://github.com/manzurfer) | 26 | 19 | 471 | 5 | 8 | Download Zip/Github, Comments | H, L |
**TOTAL** | 167  | 137 | 5505 | 43 | 54 | Trending Datasets, Active session, Draft dataset, Communities,Download Zip/Github, Comments  | H (2)/M(2)/L(2) |

La tabla contiene la información de cada miembro del proyecto y el total de la siguiente forma:

- Horas: número de horas empleadas en el proyecto
- Commits: solo contar los commits hechos por miembros del equipo, no lo commits previos
- LoC (líneas de código): solo contar las líneas producidas por el equipo y no las que ya existían o las que se producen al incluir código de terceros
- Test: solo contar los test realizados por el equipo nuevos
- Issues: solo contar las issues gestionadas dentro del proyecto y que hayan sido gestionadas por el equipo
- Work Item: principal WI del que se ha hecho cargo el miembro del proyecto
- Dificultad: señalar el grado de dificultad en cada caso. Además, en los totales, poner cuántos se han hecho de cada grado de dificultad entre paréntesis.


## Integración con otros equipos
Equipos con los que se ha integrado y los motivos por lo que lo ha hecho y lugar en el que se ha dado la integración: 
* [poke-hub-1](https://github.com/poke-hub): La colaboración entre ambos equipos ha potenciado el desarrollo de Poke-hub mucho más que el trabajo individual. Aunque ambos pertenecen a la misma organización, comparten un único repositorio de forma eficiente. Esto es posible gracias a una estrategia de ramificación que utiliza una rama main central y dos ramas de integración (trunks) independientes, una asignada a cada equipo.

# Resumen Ejecutivo Pokehub.io

Pokehub es una plataforma web desarrollada por el siguiente grupo: **Héctor Guerra Prada, Carlos Javier Cruz Ramírez, Kevin Amador Calzadilla, Manuel Zurita Fernández, Pablo Bermúdez, Imaz, Marco Padilla Gómez**; diseñada como un repositorio científico abierto para la gestión, almacenamiento y análisis de modelos de Pokémon en formato `.poke`.

El proyecto no es simplemente una base de datos de juegos, sino una adaptación de principios de ciencia abierta aplicados a este dominio específico, permitiendo la trazabilidad, citación y preservación de datasets. Arquitectónicamente, es una evolución del sistema **UVLHub**, adaptado para procesar ficheros de configuración de Pokémon en lugar de modelos de características puras, aunque mantiene integración con herramientas de análisis de variabilidad como **Flamapy**.

El sistema está construido sobre un *stack* tecnológico robusto y moderno, utilizando **Python** con el framework **Flask** para el backend, **MariaDB** como motor de persistencia relacional, y contenedores **Docker** para la orquestación de servicios en entornos de desarrollo y producción.

---

## 1. Arquitectura del Sistema y Tecnologías Clave

La arquitectura del proyecto sigue un patrón **modular monolítico**, donde la aplicación Flask se divide en módulos funcionales independientes gestionados por un núcleo común.

### Backend y Frameworks
El núcleo de la aplicación utiliza **Flask 3.1.1** junto con **SQLAlchemy** como ORM para la interacción con la base de datos. La gestión de usuarios y autenticación se maneja a través de **Flask-Login** y **Flask-WTF** para la seguridad en formularios.

### Base de Datos
Se emplea **MariaDB** para almacenar la información relacional de usuarios, metadatos de datasets y modelos. El esquema de la base de datos se gestiona y evoluciona mediante **Flask-Migrate** y **Alembic**, evidenciado por la presencia de scripts de migración versionados.

### Contenedorización
El despliegue está totalmente dockerizado. El archivo `docker-compose.prod.yml` define servicios orquestados que incluyen la aplicación web, la base de datos, un servidor **Nginx** como proxy inverso y servidor web, y **Watchtower** para la actualización automática de contenedores.

### Búsqueda y Análisis
Se integra **Elasticsearch** para capacidades de búsqueda avanzada y **Flamapy** para el análisis de modelos de características, lo que sugiere que los equipos de Pokémon se tratan como configuraciones de productos validables.

---

## 2. Modelo de Dominio y Gestión de Datos

El corazón funcional de Pokehub reside en su capacidad para analizar y estructurar información compleja contenida en archivos de texto plano.

### La Entidad PokeModel y el Formato `.poke`
El sistema define una clase **PokeModel** que vincula un archivo físico con sus metadatos. El proyecto incluye un *parser* específico (`parse_poke`) diseñado para leer archivos de texto `.poke`.

Este *parser* utiliza expresiones regulares para extraer atributos detallados de cada Pokémon: nombre, objeto (*item*), habilidad (*ability*), tipo Tera (*tera_type*), estadísticas de esfuerzo (*EVs*), valores individuales (*IVs*) y lista de movimientos (*moves*). Esto demuestra que la plataforma entiende semánticamente el contenido de los archivos subidos, no solo los almacena como binarios opacos.

### Datasets y Metadatos
Los modelos se agrupan en **DataSets**. Cada dataset posee metadatos ricos que incluyen título, descripción, etiquetas, tipo de publicación e identificadores persistentes como **DOI (Digital Object Identifier)** tanto para la publicación asociada como para el propio dataset.

### Autoría y Métricas
El modelo de datos contempla la gestión de autores con afiliación y **ORCID**, vinculando la propiedad intelectual a los datasets. Además, se registran métricas de uso como descargas y vistas, asociando estos eventos a cookies y usuarios para evitar duplicidades y garantizar estadísticas fiables.

---

## 3. Integración con Repositorios Externos

Una característica distintiva es su integración con **Zenodo**, un repositorio de investigación generalista.

El servicio **ZenodoService** está diseñado para depositar datasets y archivos automáticamente, obteniendo DOIs reales.

Sin embargo, el sistema implementa una capa de abstracción o simulación llamada **Fakenodo** (visible en las variables de entorno y rutas), lo que permite realizar pruebas de integración completas del ciclo de vida de publicación científica sin generar residuos en el servidor real de Zenodo durante el desarrollo o las pruebas.

---

## 4. Ingeniería de Software y Herramientas DevOps

El proyecto destaca por un alto nivel de madurez en ingeniería de software, evidenciado por la creación de una herramienta CLI propia llamada **Rosemary**.

### Rosemary CLI
Ubicada en `rosemary/cli.py`, esta herramienta de línea de comandos facilita tareas de desarrollo y mantenimiento. Permite a los desarrolladores limpiar cachés, resetear la base de datos, sembrar datos de prueba, ejecutar *linters*, *tests* y generar estructuras de nuevos módulos mediante plantillas **Jinja2**. Esto estandariza el desarrollo y acelera la incorporación de nuevos colaboradores.

### Testing Automatizado
El proyecto incluye una suite de pruebas exhaustiva. Se utilizan **Pytest** para pruebas unitarias y de integración, **Selenium** para pruebas *end-to-end* simulando la interacción del usuario en el navegador, y **Locust** para pruebas de carga y rendimiento, asegurando que la plataforma escale adecuadamente bajo demanda.

# Descripción del Sistema (1.500 palábras aproximadamente)

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

# Visión global del proceso de desarrollo

El ciclo de vida del desarrollo de software (SDLC) en el proyecto **Poke-Hub** está fundamentado en principios ágiles, priorizando la calidad del código, la entrega continua de valor y, sobre todo, la colaboración estrecha. Dada la estructura del proyecto, dividido en sub-equipos que trabajan sobre un repositorio común, el equipo **poke-hub-2** ha adoptado una metodología de trabajo colaborativa basada en la **Programación por Pares (Pair Programming)**.

Este enfoque no solo equilibra la autonomía del equipo con la estabilidad de la rama principal (`main`), sino que garantiza la calidad del software desde el momento de su escritura, eliminando la necesidad de burocracia excesiva en la fase de integración.

---

## 1. Planificación y Gestión de Tareas

La unidad fundamental de trabajo es el **Work Item (WI)**. Sin embargo, la gran diferencia en nuestra gestión radica en la asignación y ejecución de estos ítems.

### Gestión del Backlog
Todo el trabajo se desglosa en WIs detallados. Cada WI define claramente los requisitos y criterios de aceptación.

### Asignación por Parejas
Al inicio de cada ciclo, el líder del equipo (**Héctor**, en el caso de *poke-hub-2*) planifica el trabajo agrupando los WIs y asignándolos a **parejas de desarrolladores**. No se asignan tareas a individuos aislados.

### Roles y Rotación (Equilibrio de Carga)
Para asegurar que todos los miembros dominen tanto el aseguramiento de la calidad como la implementación, se establece una **rotación de roles por WI**:

- En un WI determinado, un miembro de la pareja asume el rol de **Tester** (responsable del diseño y escritura de pruebas) y el otro el de **Implementador** (responsable de la funcionalidad).
- En el siguiente WI asignado a la misma pareja, los roles se invierten.

> **Nota:** Aunque existen roles definidos para equilibrar la carga, el trabajo se realiza de manera conjunta y síncrona. Ambos desarrolladores son conscientes y responsables tanto de los tests como del código de producción.

---

## 2. Estrategia de Ramificación: EGC Flow

Utilizamos una estrategia de ramificación jerárquica adaptada al trabajo en equipo paralelo.

- **`main`**  
  Rama principal estable con el código integrado de todos los equipos.

- **`2-poke-hub/trunk`**  
  Rama de integración del equipo. Consolida todas las funcionalidades completadas y validadas del equipo *poke-hub-2*. Debe mantenerse siempre estable.

- **`2-poke-hub/feat/<descripcion-corta>`**  
  Ramas de característica. Cada pareja crea una de estas ramas a partir de `2-poke-hub/trunk` para trabajar en su WI. El aislamiento permite trabajar sin romper la rama del equipo.

---

## 3. Ciclo de Vida de una Funcionalidad: Trabajo en Parejas

Dado que no utilizamos **Pull Requests (PR)** como barrera de entrada, la calidad y la corrección del código se delegan en la dinámica de la pareja durante el desarrollo. El "visto bueno" es implícito y continuo gracias al trabajo a cuatro manos.

### 3.1. Desarrollo Colaborativo (Pair Programming)

Una vez asignado un WI, la pareja crea su rama de característica (`2-poke-hub/feat/...`).

**Ejecución Conjunta**
- Ambos revisan el código del otro en tiempo real, discuten la arquitectura y refactorizan juntos, implementando test y funcionalidad.

**Validación Interna**  
Al trabajar en pareja, la revisión de código es constante. No se espera al final para corregir errores; se previenen durante la escritura. La pareja actúa como su propio control de calidad (**QA**).

---

### 3.2. Integración Continua (CI)

Cuando la pareja considera que la tarea está lista (criterios de aceptación cumplidos y tests pasando en local), suben los cambios al repositorio remoto.

Esto dispara el pipeline de **Integración Continua (CI)** en **GitHub Actions**, que actúa como árbitro imparcial:

- **Linting:** verificación de estilo.
- **Testing:** ejecución automática de la suite de pruebas.
- **Build:** verificación de compilación.

---

### 3.3. Integración en Trunk (Sin Pull Request)

Aquí radica la agilidad del proceso. Al no haber Pull Request, la responsabilidad recae totalmente en la pareja.

Si el pipeline de CI es exitoso (**verde**) y dado que el código ya ha sido revisado por dos personas durante su construcción, se procede directamente a la **fusión (merge)** de la rama `feat` en `2-poke-hub/trunk`.

Esta fusión directa agiliza el desarrollo y demuestra la confianza en la metodología de pares como mecanismo de validación.

---

## 4. Integración Global y Despliegue a Producción

La integración del trabajo de *poke-hub-2* con el resto del proyecto en `main` sigue siendo un proceso coordinado.

### 4.1. Sincronización Coordinada hacia `main`

La fusión desde `trunk` hacia `main` se realiza periódicamente:

- **Reunión de sincronización:** Héctor (líder de *poke-hub-2*) se coordina con el líder del otro equipo (Jesús).
- **Resolución de conflictos:** revisan los cambios acumulados y resuelven conjuntamente cualquier conflicto entre los subsistemas.
- **Fusión:** se integran los cambios en `main`, asegurando la estabilidad global.

---

### 4.2. Despliegue Continuo (CD)

Una vez en `main`, el pipeline de **Despliegue Continuo (CD)** se activa automáticamente: empaqueta la aplicación, ejecuta pruebas **E2E** finales y despliega la nueva versión en el entorno de producción.

### 5. Caso Práctico: Flujo Completo de un Cambio
Para ilustrar el proceso real bajo nuestra metodología, sigamos el ciclo de vida de una tarea de mantenimiento: "Cambiar Trending Datasets de 3 a 5".

1.  **Fase de Planificación:** Héctor, líder del equipo 2, asigna el WI correspondiente a la pareja formada por "Dev A" y "Dev B". Acuerdan el reparto de carga para este ticket: "Dev A" se centrará en los tests y controles de calidad (rosemary test, flake8), mientras que "Dev B" liderará la implementación del cambio.

2.  **Fase de Desarrollo:** La pareja actualiza su repositorio local y crea la rama 2-poke-hub/fix/Cambio-trending-datasets. Trabajan de manera conjunta: modifican el código para mostrar 5 elementos y ejecutan las pruebas locales y linters para asegurar el formato. Al terminar y validar que todo funciona en local, realizan el push con los cambios.

3.  **Fase de Integración de Equipo:**

*   **CI Automático:** GitHub Actions se activa, ejecuta linting, tests y build. El resultado es exitoso (verde).

*   **Validación por Pares (Sin PR):** Dado que el código ha sido construido y revisado a cuatro manos durante el desarrollo, no se requiere una Pull Request formal. La validación es implícita al trabajo en pareja.

*   **Merge:** La pareja fusiona directamente su rama fix en 2-poke-hub/trunk. La funcionalidad actualizada de los trending datasets ya forma parte de la rama estable del equipo.

4.  **Fase de Integración Global:** Cuando se realizan cambios suficientes o finaliza el sprint, Héctor y Jesús coordinan la integración.

*   Realizan una fusión de 2-poke-hub/trunk a main.

*   Revisan que no haya conflictos con el trabajo del equipo 1.

*   Tras confirmar la compatibilidad, suben la fusión a main.

5.  **Fase de Despliegue:** La fusión en main dispara el pipeline de CD. La aplicación se empaqueta, pasa las pruebas finales y se despliega automáticamente en producción.

**Resultado:** Los usuarios finales ahora ven automáticamente 5 datasets en la sección de tendencias. Este ciclo ágil asegura que el cambio llega a producción rápidamente, respaldado por la calidad que otorga la programación en pareja y la verificación automática del CI.

# Entorno de Desarrollo: PokeHub

## Visión General del Entorno

El entorno de desarrollo de **PokeHub** no es simplemente una colección de herramientas, sino un ecosistema diseñado bajo los principios de **modularidad, reproducibilidad y aislamiento**. El objetivo principal ha sido eliminar el clásico problema de *"funciona en mi máquina"*, proporcionando una infraestructura estandarizada.

El núcleo del sistema opera sobre **Python 3.12**, aprovechando la ligereza y flexibilidad del framework **Flask** para el backend. Para la orquestación, se ha adoptado un enfoque híbrido:

* **Docker (Estándar)**: Utilizado para el desarrollo diario ágil. Garantiza que cada servicio (base de datos, web, pruebas) viva en su propio contenedor ligero.
* **Vagrant (Aislamiento Completo)**: Ofrece una virtualización a nivel de sistema operativo para escenarios que requieren una paridad estricta con servidores de producción basados en Linux o configuraciones de red complejas que Docker no puede simular nativamente.

---

## Stack Tecnológico y Versiones

Para asegurar la compatibilidad y estabilidad del sistema, se han fijado versiones específicas de las librerías y herramientas críticas. A continuación, se detallan los componentes principales identificados en la configuración del proyecto:

* **Lenguaje de programación**: Python 3.12
* **Framework Web**: Flask 3.11
* **Base de datos**: MariaDB
* **Servidor Web**: Nginx 1.29.1, utilizado para gestionar las peticiones entrantes y servir archivos estáticos
* **Línea de comandos**: Rosemary 1.0.0, una herramienta propia desarrollada para facilitar tareas de gestión del proyecto

### Testing y QA

* **Pytest 8.4.1** para pruebas unitarias
* **Selenium 4.34.2** para pruebas de interfaz y end-to-end
* **Locust 2.37.14** para pruebas de carga
* **Flamapy 2.0.1** y sus plugins asociados para análisis de modelos de características

---

## Arquitectura de Servicios

El entorno de desarrollo se orquesta mediante el archivo `docker-compose.dev.yml`. Este define una arquitectura de microservicios interconectados a través de una red interna denominada `uvlhub_network`. Los subsistemas son los siguientes:

* **Servicio web (web)**: Contenedor principal que aloja la aplicación con Flask. Expone el puerto **5000** y se construye a partir del `Dockerfile.dev`. Este servicio monta el directorio raíz del proyecto como un volumen (`../:/app`), permitiendo que los cambios en el código se reflejen inmediatamente sin necesidad de reconstruir la imagen.

* **Base de datos (db)**: Contenedor persistente que ejecuta MariaDB. Utiliza un volumen llamado `db_data` para asegurar que los datos sobrevivan al reinicio de los contenedores. Se expone en el puerto **3306**.

* **Proxy inverso (nginx)**: Actúa como punto de entrada al sistema por el puerto **80**. Redirige el tráfico al servicio web y gestiona la entrega de contenido estático, emulando un entorno de producción.

### Infraestructura de Pruebas Selenium

Se despliega un **Selenium Grid** compuesto por:

* **selenium-hub**: Nodo de orquestación (puertos **4442–4444**)
* **selenium-chrome** y **selenium-firefox**: Nodos trabajadores que permiten ejecutar pruebas automatizadas en navegadores Chrome y Firefox respectivamente. Estos contenedores exponen puertos **VNC (5900, 5901)** para visualización remota de las pruebas.

---

## Herramienta de Gestión: Rosemary

Uno de los mayores activos de este entorno es **Rosemary 1.0.0**, la Interfaz de Línea de Comandos (CLI) propietaria del proyecto. Construida sobre la librería **click** de Python, Rosemary actúa como una capa de abstracción sobre tareas complejas.

En lugar de escribir comandos SQL manuales o scripts de shell largos, los desarrolladores interactúan con el sistema de forma semántica. Rosemary se inyecta en el contenedor mediante `pip install -e ./` (modo editable), permitiendo actualizaciones del CLI en tiempo real.

### Capacidades de Rosemary

* **Ciclo de vida de la BD**:

  * `rosemary db:reset`: Borra y recrea la base de datos
  * `rosemary db:seed`: Puebla la base de datos con datos ficticios para pruebas

* **Generación de Código**:

  * `rosemary make:module`: Crea la estructura de carpetas estándar para nuevos módulos, asegurando una arquitectura uniforme

* **Auditoría**:

  * Centraliza la ejecución de linters, tests y análisis de cobertura

---

## Estrategia de Calidad (Testing)

El entorno preconfigura tres niveles de pruebas para asegurar la robustez del sistema:

* **Unitarias (Pytest 8.4.1)**: Pruebas rápidas y aisladas para la lógica de negocio pura y funciones de utilidad.

* **End-to-End (Selenium 4.34.2)**: Validan flujos completos de usuario (por ejemplo: *un usuario se registra, sube un modelo y cierra sesión*). Gracias al contenedor Nginx, estas pruebas se ejecutan contra un entorno idéntico al real.

* **Carga y Estrés (Locust 2.37.14)**: Permite simular cientos de usuarios concurrentes accediendo al sistema, ayudando a identificar cuellos de botella en la base de datos o en el código Python antes de llegar a producción.

---

## Guía de Instalación y Despliegue

### Opción A: Despliegue con Docker

Este método es el estándar para el desarrollo diario debido a su rapidez y menor consumo de recursos.

**Pre-requisitos**:

* Docker Engine
* Docker Compose

**Configuración del entorno**:

1. Duplicar el archivo `.env.docker.example` y renombrarlo a `.env`
2. Configurar las variables de entorno necesarias

**Construcción y ejecución**:

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

Esto iniciará todos los servicios descritos anteriormente. El script de entrada `development_entrypoint.sh` se encargará de las inicializaciones finales dentro del contenedor.

---

### Opción B: Entorno Virtualizado con Vagrant

Para casos donde se requiera una máquina virtual completa, se proporciona una configuración de **Vagrant**.

* **Configuración**: El `Vagrantfile` utiliza una imagen base `ubuntu/jammy64`
* **Aprovisionamiento**: Se utiliza **Ansible** (`00_main.yml`) para instalar automáticamente todas las dependencias del sistema, configurar MariaDB y desplegar la aplicación
* **Red**: La máquina virtual redirige el puerto **5000** (aplicación) y el **8089** (posiblemente para Locust u otro servicio auxiliar) al host local
* **Variables de entorno**: El sistema carga automáticamente las variables desde el archivo `.env` del host y las inyecta en el perfil de usuario de la máquina virtual, asegurando una configuración transparente

---

## Consideraciones Técnicas Adicionales

Para optimizar la experiencia del desarrollador, se han tomado decisiones específicas en la construcción de las imágenes:

* **Docker-in-Docker (Client)**: El `Dockerfile.dev` instala la CLI de Docker dentro del contenedor web. Esto permite que la aplicación pueda invocar otros contenedores o inspeccionar el estado del sistema, una capacidad útil para herramientas de administración interna.

* **Limpieza de Caché**: Se han configurado scripts para eliminar archivos `.pyc` y directorios `__pycache__` residuales, que a menudo causan conflictos al mover código entre el sistema anfitrión (Windows/Mac) y el contenedor (Linux).

* **Inyección de Variables**: Tanto en Docker como en Vagrant, las variables de entorno se inyectan dinámicamente. Cambiar la configuración en el archivo `.env` propaga el cambio a la aplicación, a los scripts de migración y a los tests sin modificar el código Python.

---

Este entorno robusto asegura que el equipo de **PokeHub** pueda centrarse en desarrollar funcionalidades de valor, confiando en una infraestructura subyacente **predecible y resiliente**.

# Ejercicio: Cambio Trending Datasets (3 a 5) (Poke-hub-2)

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

# Conclusiones y Trabajo Futuro

### Conclusiones

* La automatización es clave: La implementación de procesos automáticos de integración y despliegue continuo (CI/CD) se ha demostrado esencial para garantizar la calidad del software, reducir errores humanos y mantener un flujo de trabajo estable.

* Organización sobre velocidad: La planificación inicial, la definición de estándares (como el formato de los commits o el uso de plantillas) y la coordinación del equipo suponen una inversión de tiempo que se traduce en un desarrollo más profesional, ordenado y eficiente a largo plazo.

* Consistencia del entorno: La correcta gestión de la configuración del proyecto (versiones, dependencias y uso de contenedores) ha sido fundamental para asegurar que la aplicación funcione de manera consistente en todos los entornos de desarrollo.

### Trabajo Futuro

* Finalización del módulo de Comunidades: Completar el desarrollo de esta funcionalidad mediante el cierre de los sub-issues pendientes, permitiendo una interacción completa entre los usuarios dentro de sus grupos.

* Implementación de pruebas de extremo a extremo (E2E): Incorporar tests que simulen la navegación real del usuario, por ejemplo mediante Selenium, como complemento a los tests unitarios existentes.
