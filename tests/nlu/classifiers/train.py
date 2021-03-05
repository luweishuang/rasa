from rasa.nlu import train
from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.components import ComponentBuilder
from rasa.nlu.model import Interpreter
import asyncio

EPOCHS = "epochs"
RANDOM_SEED = "random_seed"
BILOU_FLAG = "BILOU_flag"


def as_pipeline(*components):
    return [{"name": c} for c in components]


async def train_persist_load_with_composite_entities(component_builder, model_path):
    # 实体提取 + 意图分类
    # classifier_params = {RANDOM_SEED: 1, EPOCHS: 1, BILOU_FLAG: False}
    # pipeline = as_pipeline("MitieNLP", "JiebaTokenizer", "MitieEntityExtractor",
    #                             "MitieFeaturizer", "SklearnIntentClassifier")
    # 意图分类
    # pipeline = as_pipeline("MitieNLP", "JiebaTokenizer", "MitieFeaturizer", "SklearnIntentClassifier")
    # assert pipeline[3]["name"] == "SklearnIntentClassifier"
    # pipeline[3].update(classifier_params)

    pipeline = as_pipeline("MitieNLP", "JiebaTokenizer", "CountVectorsFeaturizer", "DIETClassifier")
    # CountVectors_params = {"analyzer": "char_wb", "min_ngram": 1, "max_ngram": 4}
    # pipeline[2].update(CountVectors_params)
    # DIETClassifier_params = {"entity_recognition": False, "epochs": 3}
    # pipeline[3].update(DIETClassifier_params)

    _config = RasaNLUModelConfig({"pipeline": pipeline, "language": "zh"})

    (trainer, trained, persisted_path) = await train(
        _config,
        path=model_path,
        data="/Users/psc/code/rasa/tests/nlu/classifiers/intents.yml",
        component_builder=component_builder,
    )

    assert trainer.pipeline
    assert trained.pipeline
    loaded = Interpreter.load(persisted_path, component_builder)
    assert loaded.pipeline
    text = "南京明天天气如何"
    print("--------------------------------------------------")
    print(trained.parse(text))
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(loaded.parse(text))
    print("--------------------------------------------------")
    assert loaded.parse(text) == trained.parse(text)


if __name__ == '__main__':
    # test_train_model_checkpointing_peter()
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(
        train_persist_load_with_composite_entities(ComponentBuilder(), "models"))
    loop.close()