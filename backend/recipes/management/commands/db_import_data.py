import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from tqdm import tqdm

from recipes.constans import PATH_DB_IMPORT_DATA_ING, PATH_DB_IMPORT_DATA_TAG
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """
    Django-команда для импорта CSV-файлов в базу данных.
    """
    help = 'Загрузка CSV-файлов в базу данных.'

    def import_ingredient(self):
        if Ingredient.objects.all().exists():
            self.stdout.write(self.style.WARNING(
                'Данные ингредиентов уже загружены.'
            ))
        else:
            with open(
                settings.BASE_DIR / PATH_DB_IMPORT_DATA_ING,
                'r',
                encoding='utf8',
                newline=''
            ) as file:
                reader = csv.DictReader(file)
                next(reader)
                total_rows = sum(1 for _ in reader)
                file.seek(0)
                with tqdm(total=total_rows, desc='Ингредиенты') as pbar:
                    file.seek(0)
                    next(reader)
                    for row in reader:
                        Ingredient.objects.create(
                            name=row['name'],
                            measurement_unit=row['measurement unit']
                        )
                        pbar.update(1)
                self.stdout.write(self.style.SUCCESS(
                    'Данные ингредиентов успешно загружены!'
                ))

    def import_tags(self):
        if Tag.objects.all().exists():
            self.stdout.write(self.style.WARNING(
                'Данные тэгов уже загружены.'
            ))
        else:
            with open(
                settings.BASE_DIR / PATH_DB_IMPORT_DATA_TAG,
                'r',
                encoding='utf8',
                newline=''
            ) as file:
                reader = csv.DictReader(file)
                next(reader)
                total_rows = sum(1 for _ in reader)
                file.seek(0)
                with tqdm(total=total_rows, desc='Тэги') as pbar:
                    file.seek(0)
                    next(reader)
                    for row in reader:
                        Tag.objects.create(
                            name=row['name'],
                            color=row['color'],
                            slug=row['slug']
                        )
                        pbar.update(1)
                self.stdout.write(self.style.SUCCESS(
                    'Данные тэгов успешно загружены!'
                ))

    def handle(self, *args, **kwargs):
        self.import_ingredient()
        self.import_tags()
