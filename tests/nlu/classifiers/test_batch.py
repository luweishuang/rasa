from rasa.nlu.components import ComponentBuilder
from rasa.nlu.model import Interpreter

component_builder = ComponentBuilder()



def test_single(txt_in, model_path):
    loaded = Interpreter.load(model_path, component_builder)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    cur_rst = loaded.parse(txt_in)
    return  cur_rst


if __name__ == '__main__':
    test_lists = [
        "明天天气",
        "看下安顺站一号母线的负荷情况",
        "打开知乎",
        "打电话给李建明",
        "你谁啊",
        "看一下李鸿章的个人信息",
        "查一下安庄站一号风机的电压曲线",
        "看下南京3月2号的电压曲线",
        "看一下56风机的日发电量报表",
        "看下南京3月2号的负荷损失风险",
        "看下南京3月2号的日发电量报表",
    ]
    model_path = "models/nlu_20210304-144659"   # intent classify
    # model_path = "models/intent_entity_20210303-163327"   # intent + entity
    for cur_txt in test_lists:
        cur_rst = test_single(cur_txt, model_path)
        print(cur_rst)