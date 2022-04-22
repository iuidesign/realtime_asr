# -*- I Love Python!!! And You? -*-
# @Time    : 2022/4/9 21:18
# @Author  : sunao
# @Email   : 939419697@qq.com
# @File    : test.py
# @Software: PyCharm

import os
import sys
# curPath = os.path.abspath(os.path.dirname(__file__))
# rootPath = os.path.split(curPath)[0]
# print(rootPath)
sys.path.append("../decoder/")
from recognize import Recognize

path = "../cache/temp1.wav"
model = Recognize()
result = model.get_recognize(path)
print(result)