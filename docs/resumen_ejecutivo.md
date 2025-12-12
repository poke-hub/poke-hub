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
