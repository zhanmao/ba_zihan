import os.path
import os
import json
import logging
from .settings_manager import SettingsManager


class JsonConfigStore:
    DEFAULT_MODULES = ['examon_beginners_package', 'examon_pcep_package']

    @staticmethod
    def persist(package_manager, full_file_path: str) -> None:
        f = open(full_file_path, "w")
        json_object = json.dumps(package_manager.as_dict(), indent=4)
        f.write(json_object)
        f.close()
        logging.info(f'config saved to {full_file_path}')

    @staticmethod
    def persist_default_config(full_file_path: str) -> None:
        package_manager = SettingsManager()

        package_manager.content_mode = 'sqlite3'
        package_manager.file_mode = 'local'
        package_manager.packages = [{'name': p} for p in JsonConfigStore.DEFAULT_MODULES]
        package_manager.active_packages = JsonConfigStore.DEFAULT_MODULES

        if not os.path.isfile(full_file_path):
            JsonConfigStore.persist(package_manager, full_file_path)
