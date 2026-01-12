# TODO
import sys
import traceback
from subprocess import CalledProcessError

from django.core.management.base import BaseCommand

from django_auto_deploy.deploy import (
    check_deploy_settings,
    check_python_installation,
    install_requirement,
)


class Command(BaseCommand):
    help = "Auto deploy your django application"

    def add_arguments(self, parser):
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("...Checking configuration requirement ⚙️ ... "),
        )
        check_deploy_settings()
        check_python_installation()
        try:
            self.stdout.write(
                "1. creating virtual environment and install dependencies.......",
            )
            install_requirement()
        except (FileNotFoundError, RuntimeError, CalledProcessError):
            tb = sys.exc_info()[-1]
            stk = traceback.extract_tb(tb, 1)
            self.stdout.write(
                self.style.ERROR(stk[0][2]),
            )

        return super().handle(*args, **options)
