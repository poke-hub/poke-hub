# 🚀 Guía de Despliegue del Entorno POKEHUB con Vagrant

Esta guía detalla los pasos para levantar el entorno de desarrollo local utilizando **Vagrant** y **Ansible**. El proceso automatiza la instalación de MariaDB, Python 3.12, las dependencias y el despliegue de la aplicación Flask.

## 📍 Requisito Previo

Abre tu terminal y asegúrate de situarte en la carpeta de infraestructura donde está el `Vagrantfile`:

```bash
cd tuRuta/poke-hub/vagrant
````

-----

## 1️⃣ Levantar el Entorno (Primer Inicio)

Para crear la máquina virtual, descargar la imagen base y ejecutar toda la configuración, usa:

```bash
vagrant up
```

### ⏳ Tiempo de Espera

**IMPORTANTE:** La primera vez que ejecutes este comando, el proceso **tardará entre 5 y 10 minutos**.

Es normal que la terminal parezca detenida en tareas como:

  * `[Install pip and setuptools...]`
  * `[Activate the virtual environment...]`

**No cierres la terminal.** La máquina está compilando librerías y descargando paquetes necesarios.

### ⚙️ ¿Qué ocurre automáticamente?

El archivo `Vagrantfile` llama a los *playbooks* de Ansible, que realizan las siguientes acciones en orden:

1.  **Configuración Base:** Actualiza el sistema operativo y genera el archivo `.env` dentro de la máquina.
2.  **Base de Datos (MariaDB):**
      * Instala el servidor y cliente MariaDB.
      * Configura la seguridad y contraseña de `root`.
      * Crea las bases de datos (`pokehubdb`, `pokehubdb_test`) y el usuario de la aplicación.
3.  **Scripts:** Ejecuta scripts de inicialización de datos (`init-testing-db.sh`).
4.  **Entorno Python:**
      * Instala Python 3.12 y herramientas de compilación (`build-essential`).
      * Crea el entorno virtual (`venv`).
      * Instala todas las dependencias listadas en `requirements.txt`.
5.  **Ejecución:**
      * Aplica migraciones (`flask db upgrade`).
      * **Lanza la aplicación Flask** en segundo plano (puerto 5000).

-----

## 2️⃣ Solución de Problemas: Forzar Configuración (`Provision`)

Si el comando `vagrant up` se interrumpe, pierdes conexión, o ves el mensaje *"Machine already provisioned"* pero la aplicación no responde, **no es necesario borrar la máquina**.

Simplemente fuerza la re-ejecución de la configuración con:

```bash
vagrant provision
```

Este comando:

  * Vuelve a leer la configuración de Ansible.
  * Aplica solo los cambios pendientes o reparaciones.
  * Reinicia los servicios si es necesario.

-----

## 3️⃣ Acceder a la Máquina Virtual

Para entrar en la consola de la máquina virtual (Ubuntu) y ejecutar comandos manualmente:

```bash
vagrant ssh
```

Una vez dentro, para ir a la carpeta de tu proyecto (sincronizada con tu equipo local):

```bash
cd /vagrant
```

### Comandos útiles dentro de la VM:

  * **Verificar si Flask se está ejecutando:**
    ```bash
    ps aux | grep flask
    ```
  * **Ver los logs de la aplicación:**
    ```bash
    cat /vagrant/app.log
    ```

-----

## 4️⃣ Verificación Final

Si todo ha ido correctamente, la aplicación estará accesible desde el navegador de tu ordenador en:

👉 **http://localhost:5000**

-----

## 🛑 Gestión del Ciclo de Vida

Comandos rápidos para gestionar la máquina:

  * **Pausar la máquina** (guarda el estado actual en disco, inicio rápido después):
    ```bash
    vagrant suspend
    ```
  * **Apagar la máquina** (apagado completo):
    ```bash
    vagrant halt
    ```
  * **Eliminar la máquina** (borra todo para empezar de cero):
    ```bash
    vagrant destroy
    ```
