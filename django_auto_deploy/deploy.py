import logging
import subprocess
from pathlib import Path
from sys import platform

import tomli_w
from django.conf import settings

logger = logging.getLogger(__name__)

CONFIG_DIR: Path = settings.BASE_DIR / "config"
PYTHON_ENV_PATH = Path("/env")
SYSTEM_PATH = Path("/etc/systemd/system")

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
    project_path: str,
    application_name: str,
    unix_user: str,
    unix_group: str,
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
        ExecStart={hypercorn_path} {application_name}.asgi:application --config config/hypercorn.toml

        [Install]
        WantedBy=multi-user.target
        """
        with Path(hypercorn_conf_path).open("w") as file:
            file.write(config)
            logger.info("hypercorn config file created successfully...")
        logger.info("hypercorn config file detected...")


def setup_health_cron_tab():
    pass
