import contextlib
import getpass
import logging
import pwd
import subprocess
from pathlib import Path
from subprocess import CalledProcessError, check_call
from sys import platform
from typing import Union

import tomli_w
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

CONFIG_DIR: Path = settings.BASE_DIR / "config"
SYSTEM_PATH: Path = Path("/etc/systemd/system")
UNIX_USER: str = getpass.getuser()
BASE_DIR = str(settings.BASE_DIR)


class AutoDeploySettingsException(Exception):
    pass


if platform not in ("linux", "linux2"):
    error_msg = "Your system is not yet supported"
    raise OSError(error_msg)


def check_deploy_settings():
    if not hasattr(settings, "DJANGO_PORT"):
        error_msg = "Auto deploy exception: DJANGO_PORT must be set"
        raise AutoDeploySettingsException(error_msg)


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


def install_requirement():
    requirement_file_path = CONFIG_DIR / "requirements.txt"
    if not requirement_file_path.exists():
        error_msg = "requirements.txt file does not exist"
        raise FileNotFoundError(error_msg)
    try:
        command = f"cd {BASE_DIR} && python3 -m venv venv && ./venv/bin/pip install -r {CONFIG_DIR}".split(
            " ",
        )
        res = subprocess.run(command, check=True)
        if res.returncode != 0:
            error_msg = f"cmd failed: stdout={res.stdout}\nstderr={res.stderr}"
            raise RuntimeError(error_msg)
        logger.info("Package installed successfully 🚀")
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install python packages: %s", exc, exc_info=1)


def check_python_installation():
    try:
        check_call("/usr/bin/python3 --version")
    except CalledProcessError:
        command = [
            "apt",
            "update",
            "&&",
            "sudo",
            "apt",
            "install",
            "-y",
            "python3",
            "python3-venv",
        ]
        subprocess.run(command, check=True)


def create_user(user: str = "app") -> str | None:
    try:
        pwd.getpwnam(user)
        return user
    except KeyError:
        command = f"sudo useradd -m -s /bin/bash {user} && sudo chown -R {user}:{user} {BASE_DIR}".split(
            " ",
        )
        with contextlib.suppress(CalledProcessError):
            subprocess.run(command, check=True)
            return user


def hypercorn_service(
    django_project_name: Union[str, None] = DJANGO_PROJECT_NAME,
    unix_group: str = UNIX_GROUP,
    unix_user: str = UNIX_USER,
    project_path: str = BASE_DIR,
):
    hypercorn_path = BASE_DIR / "venv/bin/hypercorn"
    hypercorn_conf_path = SYSTEM_PATH / "hypercorn.service"

    if hypercorn_conf_path.exists():
        logger.info("hypercorn config file detected...")
    else:
        user_group = create_user() or unix_group
        user = create_user() or unix_user
        logger.info("creating hypercorn config file...")
        config = f"""
            [Unit]
            Description=hypercorn server instance
            After=network.target

            [Service]
            User={user}
            Group={user_group}
            WorkingDirectory={project_path}
            ExecStart={hypercorn_path} {django_project_name}.asgi:application --config config/hypercorn.toml
            Restart=always

            [Install]
            WantedBy=multi-user.target
            """

        with Path(hypercorn_conf_path).open("w+") as file:
            file.write(config)
            logger.info("hypercorn config file created successfully...")


def setup_health_cron_tab():
    # TO DO
    pass


def sanity_check():
    import requests

    if len(settings.ALLOWED_HOSTS) == 0:
        error_msg = "Your system is not yet supported"
        raise ImproperlyConfigured(error_msg)
    for url in settings.ALLOWED_HOSTS:
        response = requests.options(url, timeout=10)
        if response.ok:
            return 1
    return 0
