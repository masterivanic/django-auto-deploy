import logging
import subprocess
from pathlib import Path
from sys import platform

import tomli_w
from django.conf import settings

logger = logging.getLogger(__name__)

CONFIG_DIR: Path = settings.BASE_DIR / "config"

if platform not in ("linux", "linux2"):
    error_msg = "Your system is not yet supported"
    raise OSError(error_msg)


def check_deploy_settings():
    if not hasattr(settings, "DJANGO_PORT"):
        error_msg = "DJANGO_PORT must be set"
        raise ValueError(error_msg)


def config_hypercorn():
    config_file = CONFIG_DIR / "hypercorn.toml"
    config_toml = {
        "bind": [f"0.0.0.0:{settings.DJANGO_PORT}"],
        "workers": 2,
        "threads": 2,
        "keep_alive_timeout": 5,
        "max_app_queue_size": 100,
        "loglevel": "error",
        "use_reloader": False,
        "graceful_timeout": 30,
    }
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with Path.open(config_file, mode="w+") as file:
            tomli_w.dump(config_toml, file)
    except (OSError, PermissionError):
        raise


def create_activate_env():
    env_path = Path("/env")
    activate_script = env_path / "bin" / "activate"
    try:
        if not env_path.exists():
            python_path = str(Path("/usr/bin/python3").resolve())
            subprocess.run(
                [python_path, "-m", "venv", str(env_path.resolve())],
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
        subprocess.run(
            [pip_path, "install", "-r", str(requirement_file_path.resolve())],
            check=True,
        )
        logger.info("Package installed successfully 🚀")
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to install python packages: %s", exc, exc_info=1)


def setup_apache_config():
    pass


def hypercorn_service():
    pass


def setup_health_cron_tab():
    pass
