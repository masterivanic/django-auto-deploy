# TODO
from django.core.management.base import BaseCommand

from django_auto_deploy.deploy import check_deploy_settings


class Command(BaseCommand):
    help = "Auto deploy your django application"

    def add_arguments(self, parser):
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.NOTICE("...Checking configuration requirement ⚙️ ... "),
        )
        check_deploy_settings()
        return super().handle(*args, **options)
