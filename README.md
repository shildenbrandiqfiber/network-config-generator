Network Configuration Generator
===============================

This Web application is a simple configuration generator for network equipment like Routers and Switches.

It is based on python3 and the [Flask microframework](https://flask.palletsprojects.com). If you like to know more about the Use Case and development of this Web service, take a look on the associated blog series "[How to build your own configuration generator](https://codingnetworker.com/2015/12/network-configuration-generator/)".

The following images shows an example configuration template and the associated variable definition.

![example template](/app/static/images/example_template.png)

## Requirements

  * Python 3.10 or newer (tested with 3.10, 3.12, 3.13 and 3.14)
  * a redis-server and a celery worker for asynchronous tasks like the export to the local FTP/TFTP directory (optional for local use)

The main dependencies are Flask 3, SQLAlchemy 2, Celery 5 and Mako. All versions are pinned in the `requirements.txt` (and `requirements_test.txt` for the test suite).

## Install the application

**Please Note: All setup scripts assume that this Web service and the associated services like TFTP are the only service running on the server.**

There are multiple ways to run this Web service:

  * on a Linux server (recommended is Ubuntu 22.04)
  * as a Vagrant VM (see Vagrantfile)
  * on Raspberry PI

The configuration of the Web service depends on the `APP_SETTINGS` environment variable. The following values are possible.

| Configuration value           | used for                                                 |
| ----------------------------- | -------------------------------------------------------- |
| `config.DefaultConfig`        | default configuration                                    |
| `config.ProductionConfig`     | configuration for a production environment (recommended) |
| `config.TestConfig`           | configuration for unit-tests                             |
| `config.LiveServerTestConfig` | configuration for selenium-tests                         |

If the `APP_SETTINGS` variable is not set, the `DefaultConfig` is used. Within the `ProductionConfig`, the `APP_SECRET_KEY` environment variable defines the key for the CSRF protection. Within a production environment, this key is dynamically created by the setup script.

### on Ubuntu Linux (22.04)

To setup the Web service on a Ubuntu machine, use the following commands:

```Shell
$ git clone https://github.com/hoelsner/network-config-generator.git network_config_generator
$ cd network_config_generator
$ ./setup_ubuntu.sh
```

Follow the instructions from the setup script. It installs Ansible from the Ubuntu repositories and runs the `deploy/setup.yaml` playbook (you're asked for your sudo password), which

  * creates the user `ncg` that runs the service and copies the application to `/var/www/network_config_generator`
  * creates a Python virtual environment in `/var/www/network_config_generator/venv` and installs the dependencies
  * generates the secret key (`network_config_generator.key`)
  * installs and configures nginx, gunicorn, redis, the celery worker and Shell in a Box
  * creates or updates the database schema (`deploy/scripts/update_database.sh`)
  * optionally installs a FTP (vsftpd) and TFTP (atftpd) server, the FTP user is `ftpuser` and the password is stored in the `ftp_user.key` file (also shown on the Appliance Status page)

After the setup, the Web service is available at `http://<server>/ncg/`.

All services are managed by systemd:

| Service                              | Description                       |
| ------------------------------------ | --------------------------------- |
| `gunicorn-network_config_generator`  | the Web service (behind nginx)    |
| `worker-network_config_generator`    | celery worker for background jobs |
| `nginx`, `redis-server`              | Web server and task queue broker  |
| `shellinabox`                        | Web based shell at `/shell`       |
| `vsftpd`, `atftpd`                   | FTP and TFTP server (optional)    |

```Shell
$ sudo systemctl status gunicorn-network_config_generator worker-network_config_generator
```

The log files are located at `/var/www/network_config_generator/log` (`application.log`, `gunicorn_access.log`, `gunicorn_error.log` and `celery_worker.log`).

#### update an existing installation

To update the Web service, pull the latest version of the repository and run the setup script again. It copies the source files, installs the dependencies, applies the database changes and restarts the services. Existing key files and the database are kept.

```Shell
$ cd network_config_generator
$ git pull
$ ./setup_ubuntu.sh
```

#### move an existing installation to a new server

The older releases of this application were deployed on Ubuntu 14.04/16.04 using Python 3.5. To move the data to a new Ubuntu 22.04 server, copy the following files from `/var/www/network_config_generator` on the old server to the same directory on the new server before running the `setup_ubuntu.sh` script:

  * `app.db` (the database)
  * the `migrations` directory (if it exists)
  * `network_config_generator.key` and `ftp_user.key` (optional, otherwise new keys are generated)

Don't copy the `venv` directory, the setup script creates a new one for the current Python version. The generated variable names and export directory names are unchanged in the current version, existing templates and value sets work without changes.

#### Vagrant

Within the repository, you'll also find a Vagrantfile. To setup the Web service using [Vagrant](https://www.vagrantup.com), use the following commands:

```Shell
$ git clone https://github.com/hoelsner/network-config-generator.git network_config_generator
$ cd network_config_generator
$ vagrant up ncg
```

The setup script that is used in this case works totally unattended and will create a VM based on Ubuntu 22.04. It will also setup the FTP and TFTP service on the server. The Web service is available at `http://localhost:10000/ncg/`. A Debian 12 (bookworm) based VM is available as `ncg_debian`.

### on a Raspberry PI

During the development, I wrote a post about the [use of a Raspberry PI as a Provisioning Appliance](https://codingnetworker.com/2016/02/using-a-raspberry-pi-as-a-configuration-generator/). At this point, I include a FTP and TFTP server to provide the configurations to the outside world. Furthermore, I add the Shell in a Box service and the Appliance Status view.

Use the `setup_raspberrypi.sh` script to setup the Web service on a Raspberry PI (requires a Raspberry Pi OS release with Python 3.10 or newer). The current version was not tested on a Raspberry PI.

![Appliance Status view](/app/static/images/how_to/appliance_status.png)

### on your local machine

To run an instance on your local machine (for demo or testing), you need to execute the following steps:

#### 1. clone the repository

```Shell
$ git clone https://github.com/hoelsner/network-config-generator.git network_config_generator
$ cd network_config_generator
```

#### 2. create a virtualenv and install python dependencies

```Shell
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

#### 3. run the local server

```Shell
(venv) $ python3 run_local.py
Initialize database...
Start the Network Configuration Generator on port 5000...
```

After this step, the Network Configuration Generator is running at `http://localhost:5000/ncg/` without any external service (no TFTP, no integration options).

If you like to use the "export to TFTP/FTP directory" (or any asynchronous action), you need to run a redis-server and celery worker on your local system. After installing the redis-server, execute the following command in another terminal window to start the celery worker:

```Shell
(venv) $ export APP_SETTINGS=config.DefaultConfig
(venv) $ celery -A app.celery worker --loglevel=info
```

On macOS, start the celery worker with the `--pool=solo` option (the default worker pool doesn't work on macOS).

## management commands

The `manage.py` script provides the [Flask command line interface](https://flask.palletsprojects.com/en/stable/cli/) including the database migration commands from [Flask-Migrate](https://flask-migrate.readthedocs.io). It's equivalent to the `flask --app app <command>` command.

```Shell
(venv) $ python3 manage.py db upgrade                       # apply database changes
(venv) $ python3 manage.py run --host 0.0.0.0 --port 5000   # run the development server
(venv) $ python3 manage.py --help                           # list all commands
```

Please note: the former `runserver` command is replaced by the `run` command.

## license

See the [license](LICENSE.md) file for license rights and limitations (MIT).

## development and testing

To enable the debug mode of the Web service, set the `DEBUG_MODE` environment variable to `1`. This will also enable the logging to the console.

The `tests` directory contains all unit and functional test-cases for the Web service. Install the test dependencies within your virtualenv first:

```Shell
(venv) $ pip install -r requirements.txt -r requirements_test.txt
```

The unit tests require a running redis-server and celery worker (used by the export tests). Start the celery worker in another terminal window (on macOS with the `--pool=solo` option):

```Shell
(venv) $ export APP_SETTINGS=config.TestConfig
(venv) $ celery -A app.celery worker --loglevel=debug
```

Then use one of the following commands to run the test cases:

```Shell
(venv) $ python3 -m unittest tests.run_tests_unit         # unit tests
(venv) $ python3 -m unittest tests.run_tests_functional   # functional tests (Selenium)
(venv) $ python3 -m unittest tests.run_tests_all          # all test cases
```

The functional tests use Selenium with Firefox, therefore Firefox must be installed on the system (the matching driver is downloaded automatically by Selenium).
