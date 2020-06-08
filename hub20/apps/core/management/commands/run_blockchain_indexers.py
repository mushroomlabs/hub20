from multiprocessing import Pool

from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from hub20.apps.core.settings import app_settings


class Command(BaseCommand):
    help = "Runs all the blockchain indexing policies"

    def handle(self, *args, **options):
        pool = Pool(len(app_settings.Web3.indexers))

        try:
            for indexer_dotted_name in app_settings.Web3.indexers:
                indexer_class = import_string(indexer_dotted_name)
                indexer = indexer_class()

                pool.apply_async(indexer)

            pool.close()
            pool.join()
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
