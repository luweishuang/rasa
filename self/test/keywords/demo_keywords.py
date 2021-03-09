import yaml
import re
import os
import jieba


class KeywordIntentClassifier():
    # Intent classifier using keyword matching.
    def __init__(self):
        self.intent_keyword_map = {}

    def load_data(self, intents_file):
        with open(intents_file, 'r') as fr:
            src_data = yaml.load(fr, Loader=yaml.FullLoader)

        for cur_data in src_data["nlu"]:
            if cur_data["intent"] not in self.intent_keyword_map:
                keywords_list = [cur_str.replace("- ", "") for cur_str in cur_data["examples"].strip().split("\n")]
                self.intent_keyword_map[cur_data["intent"]] = keywords_list

    def _validate_keyword_map(self):
        re_flag = 0
        ambiguous_mappings = []
        for intent1, keyword1 in self.intent_keyword_map.items():
            for intent2, keyword2 in self.intent_keyword_map.items():
                if (
                    re.search(r"\b" + keyword1 + r"\b", keyword2, flags=re_flag)
                    and intent1 != intent2
                ):
                    ambiguous_mappings.append((intent1, keyword1))
                    print(
                        f"Keyword '{keyword1}' is a keyword of intent '{intent1}', "
                        f"but also a substring of '{keyword2}', which is a "
                        f"keyword of intent '{intent2}."
                        f" '{keyword1}' will be removed from the list of keywords.\n"
                        f"Remove (one of) the conflicting keywords from the"
                        f" training data.",
                    )
        for intent, keyword in ambiguous_mappings:
            self.intent_keyword_map.pop(keyword)
            print(
                f"Removed keyword '{keyword}' from intent '{intent}' because it matched a "
                "keyword of another intent."
            )

    def _map_keyword_to_intent(self, word_list):
        for cur_word in word_list:
            for intent, keywords_list in self.intent_keyword_map.items():
                if cur_word in keywords_list:
                    print(
                        f"KeywordClassifier matched keyword '{cur_word}' to intent '{intent}'."
                    )
                    return intent
        print("KeywordClassifier did not find any keywords in the message.")
        return None

    def process(self, input_strlist):
        intent_name = self._map_keyword_to_intent(input_strlist)

        confidence = 0.0 if intent_name is None else 1.0
        cur_intent = {"name": intent_name, "confidence": confidence}
        return cur_intent


stopwords = ["啊", "哈哈", "了", "呃", "呦"]


def preprocess_txt(txt_in):
    sentence_depart = jieba.cut(txt_in.strip())
    out_list = []
    # 去停用词
    for word in sentence_depart:
        if word not in stopwords:
            out_list.append(word)
    return out_list


myKeywordIntentClassifier = KeywordIntentClassifier()
intents_file = "intents.yml"
myKeywordIntentClassifier.load_data(intents_file)

my_userdict_file = os.path.abspath("self_usrdict.txt")
if os.path.exists(my_userdict_file):
    os.remove(my_userdict_file)
with open(my_userdict_file, "w+") as fw:
    for intent, keywords_list in myKeywordIntentClassifier.intent_keyword_map.items():
        for cur_keyword in keywords_list:
            fw.write(cur_keyword + "\n")

#导入自定义词典
jieba.load_userdict(my_userdict_file)

txt_list = ["滚", "你好啊", "哪位", "安庆站信息", "安各庄4月11号的负荷情况"]
for cur_line in txt_list:
    cur_txtlist = preprocess_txt(cur_line)
    cur_intent = myKeywordIntentClassifier.process(cur_txtlist)
    print(cur_intent)
    print("--------------------")

# 由于没有做实体识别，所以"查询厂站信息"和"打开应用"这两个意图的关键字写的不好，正确的应该是"{厂站名}信息" 和 "打开{应用名称}",
# 当然实际使用中确实有可能存在 意图匹配不上的情况，这要具体情况具体分析。总体上应该是比 "编辑距离" 更好的匹配准则，对现有系统的改动也比较小。


