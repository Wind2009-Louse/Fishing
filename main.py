import re
import datetime
import os
from functools import reduce

rin_header = "(\d+?-\d+?-\d+? \d+?:\d+?:\d+)? [^\r\n]+?\(1093578840\)\n"
saying_1 = "\@[\s\S]* 有结果啦~\n"
saying_2 = "\#[\s\S]+?稀有度([^，]*)，"
boom_str = "@可惜爆炸了！"
description = ["事件丸：在没有任何进行中的事件时使用则可立刻开始一个事件。\n",
                "人品宝箱：使用后有一定几率获得或失去铜板，也有可能获得卷轴。\n"]
AllEffect = []

rare_types = {"SSS":0, "SS":1, "S":2, "A":3, "B":4, "C":5, "D":6, "E":7, "F":8,
              "精灵石":9,"卷轴":10,"铜板":11,
              "Z":12}
# 最终结果，格式为：
# result[事件][钓竿] = {出现次数1,...,Z}
results = {}
'''
-1: not saying
0: saying (without anything)
1: 有结果！
2: sub
3: 时间
4: usage
'''
rin_stage = -1
# 稀有度
rare_index = -1
rare_type = "Z"
# 上一次读取是否为空行，用来判断新记录
last_empty = False
# 当前读取到的行数
current_lines = 0
# 当前的时间
current_time = datetime.datetime.now()
# 事件结束的时间
last_event_time = datetime.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
# 当前事件的名字
current_event_name = "无"

def add(x,y):
    return x + y
# 获取文件的总行数
def getlines(filename="file.txt"):
    count = 0
    thefile = open(filename, 'rb')
    while True:
        buffer = thefile.read(8192 * 1024)
        if not buffer:
            break
        count += buffer.count(b'\n')
    thefile.close()
    return count

if __name__ == '__main__':
    # 获取目录
    dir_name = os.path.join(os.getcwd(), "records")
    # 检查文件夹是否被创建
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    # 获取记录
    record_files = [x for x in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name,x)) and os.path.splitext(x)[1]=='.txt']
    if len(record_files) == 0:
        print("没有聊天记录，请将聊天记录的文件(txt格式)放在records文件夹中。")
        input("回车退出。")
        exit(0)
    # 打开每个文件
    for filename in record_files:
        try:
            full_filename = os.path.join(dir_name,filename)
            datas = open(full_filename,"r",encoding='utf-8')
            total_lines = getlines(full_filename)
        except:
            print("文件打开错误，请检查：%s"%filename)
            input("回车退出。")
            raise
        print("打开文件：",filename)
        # 读取
        try:
            while(1):
                # 读取当前行
                this_str = datas.readline()
                current_lines += 1
                # 读取结束，结束循环
                if this_str == '':
                    break
                # 读取到空行，重置信息
                if this_str == "\n":
                    last_empty = True
                    rin_stage = -1

                # 读取钓竿信息
                if rin_stage == 3:
                    rin_stage = -1
                    use_check = re.match("（使用([\s\S]+?)）\n", this_str)
                    if not use_check:
                        print("钓竿识别失败：%s" % this_str)
                    else:
                        # 获取钓竿名
                        fullname = use_check.group(1)
                        # 获取存储名
                        recordname = fullname
                        # 检查是否有附魔名，筛掉
                        nickcheck = re.match("^((?:\+\d+?\ )*)([^的]*的)([\s\S]*)", fullname)
                        if nickcheck:
                            # 将强化等级放在钓竿名字后
                            recordname = nickcheck.group(3)+nickcheck.group(1)
                            nickname = nickcheck.group(2)
                            # 登记附魔名
                            if nickname not in AllEffect:
                                AllEffect.append(nickname)
                        else:
                            # 将强化等级放在钓竿名字后
                            nickcheck = re.match("^((?:\+\d+?\ )*)([\s\S]*)", fullname)
                            recordname = nickcheck.group(2)+nickcheck.group(1)

                        # 检查是否为新事件
                        if current_event_name not in results:
                            results[current_event_name] = {}

                        # 检查当前钓竿是否在当前事件中有记录
                        if recordname not in results[current_event_name]:
                            results[current_event_name][recordname] = [0, 0, 0,
                                             0, 0, 0, 0, 0, 0,
                                            0, 0, 0,
                                            0]

                        # +1
                        results[current_event_name][recordname][rare_index] += 1
                        print("(%d/%d)" % (current_lines, total_lines),end='\r')
                        #print("(%d/%d)稀有度：%s， 使用：%s(%s)"%(current_lines, total_lines, rare_type, recordname, fullname))

                # 用时、物品说明
                if rin_stage == 2:
                    last_matched_time = this_str
                    # 不为物品说明，则准备读取钓竿名
                    if this_str not in description:
                        rin_stage += 1
                # 内容（得到稀有度）
                if rin_stage == 1:
                    rin_stage += 1
                    # 得到稀有度
                    rare_check = re.match(saying_2, this_str)
                    rare_type = "Z"
                    if rare_check:
                        rare_type = rare_check.group(1)
                    # 检查是否为特殊物品(类型、check说明)
                    special_part = {"卷轴":"卷轴","精灵石":"个精灵石","铜板":"个铜板"}
                    for key, value in special_part.items():
                        special_check = re.match("钓到[\s\S]+?%s！"%value, this_str)
                        if special_check:
                            rare_type = key
                    # 爆炸判断
                    boom_check = re.match(boom_str, this_str)
                    if boom_check:
                        rare_type = "Z"
                    # 根据稀有类型读取index
                    rare_index = rare_types[rare_type]
                # 提示（上钩提示、事件提示）
                if rin_stage == 0:
                    # 判断是否为钓鱼
                    first_match = re.match(saying_1, this_str)
                    if first_match:
                        # 准备读取稀有度
                        rin_stage = 1
                    else:
                        # 读取事件名、结束时间
                        event_check = re.match("【垂钓事件】开始事件 ([^，]*)，持续时间(\d+)分(\d+)秒！", this_str)
                        # 设置结束事件
                        if event_check:
                            minute = int(event_check.group(2))
                            second = int(event_check.group(3))
                            event_time = datetime.timedelta(minutes=minute, seconds=second)
                            last_event_time = current_time
                            last_event_time += event_time
                            current_event_name = event_check.group(1)
                        # 等待下次记录
                        rin_stage = -1
                # 是否为小玲的记录头
                rin_results = re.match(rin_header, this_str)
                if rin_results and last_empty:
                    # 读取本次记录的时间
                    current_time = datetime.datetime.strptime(rin_results.group(1), '%Y-%m-%d %H:%M:%S')
                    # 事件刷新
                    if current_event_name != "无" and current_time > last_event_time:
                        current_event_name = "无"
                    rin_stage = 0
        # 出错
        except:
            # 关闭文件后抛出异常
            datas.close()
            raise

        # 读取文件结束，关闭该文件
        datas.close()
        print("\n")

    # 输出文件夹生成
    output_dir = os.path.join(os.getcwd(), "output")
    # 检查文件夹是否被创建
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # 每个事件单独一个文件夹
    for event_name in results:
        event_dir = os.path.join(output_dir, event_name)
        if not os.path.exists(event_dir):
            os.mkdir(event_dir)
        # 打开三个文件，分别输出总数、各稀有度概率、以上稀有度概率
        try:
            output_total_count = open(os.path.join(event_dir,"output_total.csv"), "w")
            output_rare_cent = open(os.path.join(event_dir,"output_cent.csv"), "w")
            output_upper_rare = open(os.path.join(event_dir,"output_upper.csv"), "w")
        except:
            print("无法写记录，可能文件被占用。")
            input("回车退出。")
            raise
        # 写文件头
        output_total_count.write("钓竿,SSS,SS,S,A,B,C,D,E,F,精灵石,卷轴,铜板,失败\n")
        output_rare_cent.write("钓竿,SSS,SS,S,A,B,C,D,E,F,精灵石,卷轴,铜板,失败\n")
        output_upper_rare.write("钓竿,SSS,SS+,S+,A+,B+,C+,D+,E+,F+,精灵石,卷轴,铜板,失败\n")
        # 读取每个钓竿的数据
        for rod_name in sorted(results[event_name].keys()):
            output_total_count.write(rod_name + ',')
            output_rare_cent.write(rod_name + ',')
            output_upper_rare.write(rod_name + ',')
            # reduce算总数，用来求百分比
            total_times = reduce(add, results[event_name][rod_name])
            # 前序和(算以上稀有度)
            preorder_sum = 0
            for index,times in enumerate(results[event_name][rod_name]):
                # 计算前序和
                if index < rare_types["精灵石"]:
                    preorder_sum += times
                else:
                    preorder_sum = times
                # 写每行
                output_total_count.write(str(times) + ',')
                output_rare_cent.write("%.5%%f," % (times * 100 / total_times))
                output_upper_rare.write("%.5%%f," % (preorder_sum * 100 / total_times))
            # 换行
            output_total_count.write("\n")
            output_rare_cent.write("\n")
            output_upper_rare.write("\n")
        # 输出结束，关闭文件
        output_total_count.close()
        output_rare_cent.close()
        output_upper_rare.close()
