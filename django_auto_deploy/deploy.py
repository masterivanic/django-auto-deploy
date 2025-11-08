import getpass
import logging
import subprocess
from pathlib import Path
from sys import platform
from typing import Union

import tomli_w
from django.conf import settings

logger = logging.getLogger(__name__)

CONFIG_DIR: Path = settings.BASE_DIR / "config"
PYTHON_ENV_PATH: Path = Path("/env")
SYSTEM_PATH: Path = Path("/etc/systemd/system")
UNIX_USER: str = getpass.getuser()
BASE_DIR = str(settings.BASE_DIR)


if platform not in ("linux", "linux2"):
    error_msg = "Your system is not yet supported"
    raise OSError(error_msg)


def check_deploy_settings():
    if not hasattr(settings, "DJANGO_PORT"):
        error_msg = "DJANGO_PORT must be set"
        raise ValueError(error_msg)


def get_unix_group():
    group = {}
    import grp
    import pwd

    for p in pwd.getpwall():
        group[p[0]] = grp.getgrgid(p[3])[0]
    return group


try:
    UNIX_GROUP = get_unix_group()[UNIX_USER]
except KeyError:
    UNIX_GROUP = None

try:
    DJANGO_PROJECT_NAME = settings.ROOT_URLCONF.split(".")[0]
except AttributeError:
    DJANGO_PROJECT_NAME = None


def config_hypercorn():
    config_file = CONFIG_DIR / "hypercorn.toml"
    config_toml = {
        "bind": [f"0.0.0.0:{settings.DJANGO_PORT}"],
        "workers": 2,
        "threads": 2,
        "debug": False,
        "keep_alive_timeout": 5,
        "max_app_queue_size": 100,
        "loglevel": "error",
        "use_reloader": True,
        "graceful_timeout": 30,
    }
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with Path.open(config_file, mode="w+") as file:
            tomli_w.dump(config_toml, file)
    except (OSError, PermissionError):
        raise


def create_activate_env():
    activate_script = PYTHON_ENV_PATH / "bin" / "activate"
    try:
        if not PYTHON_ENV_PATH.exists():
            python_path = str(Path("/usr/bin/python3").resolve())
            subprocess.run(
                [python_path, "-m", "venv", str(PYTHON_ENV_PATH.resolve())],
                check=True,
                cwd="/",
            )
        activate_cmd = f"{activate_script} && echo 'Environment activated 🚀'"
        activate_cmd = [
            "/bin/bash",
            "-c",
            f"source {str(activate_script.resolve())}",
        ]
        subprocess.run(
            activate_cmd,
            check=True,
            capture_output=True,
            cwd="/",
            shell=False,
        )
        logger.info("Environment activated 🚀")
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to initialize virtual environnment : %s", exc, exc_info=1)
    except BaseException as exc:
        logging.exception("Unexpected error %s", exc)


def install_requirement():
    pip_path = str(Path("/usr/bin/pip3").resolve())
    requirement_file_path = CONFIG_DIR / "requirements.txt"
    if not requirement_file_path.exists():
        error_msg = "requirements.txt file does not exist"
        raise FileNotFoundError(error_msg)
    try:
        res = subprocess.run(
            [pip_path, "install", "-r", str(requirement_file_path.resolve())],
            check=True,
        )
        if res.returncode != 0:
            error_msg = f"cmd failed: stdout={res.stdout}\nstderr={res.stderr}"
            raise RuntimeError(error_msg)
        logger.info("Package installed successfully 🚀")
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install python packages: %s", exc, exc_info=1)


def hypercorn_service(
    django_project_name: Union[str, None] = DJANGO_PROJECT_NAME,
    unix_group: str = UNIX_GROUP,
    unix_user: str = UNIX_USER,
    project_path: str = BASE_DIR,
):
    hypercorn_path = PYTHON_ENV_PATH / "bin" / "hypercorn"
    hypercorn_conf_path = SYSTEM_PATH / "hypercorn.service"
    if not hypercorn_conf_path.exists():
        logger.info("creating hypercorn config file...")
        config = f"""
        [Unit]
        Description=hypercorn server instance
        After=network.target

        [Service]
        User={unix_user}
        Group={unix_group}
        WorkingDirectory={project_path}
        ExecStart={hypercorn_path} {django_project_name}.asgi:application --config config/hypercorn.toml

        [Install]
        WantedBy=multi-user.target
        """
        with Path(hypercorn_conf_path).open("w") as file:
            file.write(config)
            logger.info("hypercorn config file created successfully...")
        logger.info("hypercorn config file detected...")


def setup_health_cron_tab():
    pass


def sanity_check():
    pass
