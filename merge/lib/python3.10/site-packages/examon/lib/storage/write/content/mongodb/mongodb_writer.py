from examon_core.examon_serializer import ExamonSerializer
from examon_core.models.question import BaseQuestion
import datetime

from ...protocols import ContentWriter

LANGUAGE = 'python'


class MongoDbWriter(ContentWriter):
    def __init__(self, client=None, filename_strategy=None,
                 collection_name=None, database_name=None,
                 models: list[BaseQuestion] = None) -> None:
        self.client = client
        self.models = models
        self.collection_name = collection_name
        self.database_name = database_name
        self.filename_strategy = filename_strategy

    def create_all(self) -> None:
        for model in self.models:
            model.version_number = 1
            # timestring = datetime.datetime.now().time().isoformat()
            # datetime.datetime.strptime(timestring, "%H:%M:%S.%f").time()
            # model.created_at = datetime.datetime.strptime(timestring, "%H:%M:%S.%f").time()
            model.src_filename = self.filename_strategy.name(model)
            model.correct_answer
            if model.repository is None:
                model.repository = 'default'
            collection = self.client[self.database_name][self.collection_name]

            if collection.find_one({'unique_id': model.unique_id}) is None:
                collection.insert_one(ExamonSerializer.serialize(model))

    def db(self):
        db = self.client[self.database]
        return db

    def delete_all(self) -> None:
        pass

    def truncate(self) -> None:
        pass