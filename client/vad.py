# -*- coding: utf-8 -*-
import numpy as np
import pyaudio

SUCCESS = 0
FAIL = 1

audio2 = ""
stream2 = ""

# 需要添加录音互斥功能能,某些功能开启的时候录音暂时关闭
def ZCR(curFrame):
	# 过零率
	tmp1 = curFrame[:-1]
	tmp2 = curFrame[1:]
	sings = (tmp1 * tmp2 <= 0)
	diffs = (tmp1 - tmp2) > 0.02
	zcr = np.sum(sings * diffs)
	return zcr


def STE(curFrame):
	# 短时能量
	amp = np.sum(np.abs(curFrame))
	return amp


class Vad(object):
	def __init__(self,CHUNK=1024):
		# 初始短时能量高门限
		self.amp1 = 30 # 15 960
		# 初始短时能量低门限
		self.amp2 = 5  # 1 120
		# 初始短时过零率高门限
		self.zcr1 = 2 # 30
		# 初始短时过零率低门限
		self.zcr2 = 1 # 2
		# 允许最大静音长度
		self.maxsilence = 45  # 允许换气的最长时间
		# 语音的最短长度
		self.minlen = 40  # 过滤小音量
		# 能量最大值
		self.max_en = 20000
		# 初始状态为静音
		self.status = 0
		self.count = 0
		self.silence = 0
		self.frame_len = CHUNK
		self.frame_inc = CHUNK / 2
		self.cur_status = 0
		
		
	def check_ontime(self, cache_frame):  # self.cache的值为空   self.cache_frames的数据长度为744
		
		wave_data = np.frombuffer(cache_frame, dtype=np.int16)  # 这里的值竟然是256
		wave_data = wave_data * 1.0 / self.max_en  # max_en  为20000
		data = wave_data[np.arange(0, self.frame_len)]  # 取前frame_len个值   这个值为256
		# 获得音频过零率
		zcr = ZCR(data)
		# 获得音频的短时能量, 平方放大
		amp = STE(data) ** 2
		# 返回当前音频数据状态
		status = self.speech_status(amp, zcr)
		return status
		
	
	def speech_status(self, amp, zcr):
		status = 0
		# 0= 静音， 1= 可能开始, 2=确定进入语音段   3语音结束
		if self.cur_status in [0, 1]:  # 如果在静音状态或可能的语音状态，则执行下面操作
			# 确定进入语音段
			if amp > self.amp1 or zcr > self.zcr1:  # 超过最大  短时能量门限了
				status = 2
				self.silence = 0
				self.count += 1
			# 可能处于语音段   能量处于浊音段，过零率在清音或浊音段
			elif amp > self.amp2 or zcr > self.zcr2:
				status = 2
				self.count += 1
			# 静音状态
			else:
				status = 0
				self.count = 0
				self.count = 0
		# 2 = 语音段
		elif self.cur_status == 2:
			# 保持在语音段    能量处于浊音段，过零率在清音或浊音段
			if amp > self.amp2 or zcr > self.zcr2:
				self.count += 1
				status = 2
			# 语音将结束
			else:
				# 静音还不够长，尚未结束
				self.silence += 1
				if self.silence < self.maxsilence:
					self.count += 1
					status = 2
				# 语音长度太短认为是噪声
				elif self.count < self.minlen:
					status = 0
					self.silence = 0
					self.count = 0
				# 语音结束
				else:
					status = 3
					self.silence = 0
					self.count = 0
		return status