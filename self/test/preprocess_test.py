# -*- coding: utf-8 -*-
import jieba

# jieba.load_userdict("user_dict.txt")
jieba.load_userdict("self_usrdict.txt")

line_list = ["查询安顺站一号风机的电压曲线",
             "查询安各庄1母线的故障信息",
             "开始进行南京站设备状态核实"]
for cur_line in line_list:
    seg_list = jieba.cut(cur_line.strip())
    print("jieba rst: " + "/ ".join(seg_list))
