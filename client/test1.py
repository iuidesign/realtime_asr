import threading
import time

import pyaudio
import wave
from vad import Vad
import numpy as np
import matplotlib.pyplot as plt
from decoder.recognize import Recognize
import os


class Recognize_server():
	def __init__(self, CHUNK=1024,
	             FORMAT=pyaudio.paInt16,
	             CHANNELS=1,
	             SAMPALE_RATE=16000):
		self.CHUNK = CHUNK
		self.FORMAT = FORMAT
		self.CHANNELS = CHANNELS
		self.SAMPALE_RATE = SAMPALE_RATE  # 默认是 44100 保真度最高，识别的时候使用16000
		self.temp_save_path = "../cache/"
		# 保存录音
		self.audio = pyaudio.PyAudio()
		for i in range(self.audio.get_device_count()):
			print(i, self.audio.get_device_info_by_index(i)['name'])
		self.stream = self.audio.open(format=FORMAT,
		                              channels=CHANNELS,
		                              rate=SAMPALE_RATE,
		                              input=True,
		                              frames_per_buffer=CHUNK,
		                              input_device_index=0)
		
		# self.model=Recognize()
		
		self.vad = Vad(CHUNK)
		self.frames = []
		self.long_frames = []
		self.max_size = 2
		#
		self.silence_len=0
		self.max_silence_len = 5
		self.new_chache=False
		self.cache_flag="../cache/flag"
		self.is_silence = False
		self.is_clear_temp = False
	
	# 保存麦克风数据，到时候会替换成向服务器传递的数据的功能
	def save_wav(self, path):
		wf = wave.open(path, 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
		wf.setframerate(self.SAMPALE_RATE)
		wf.writeframes(b''.join(self.long_frames))
		wf.close()
		print('\033[93m' + "已录入缓冲区" + '\033[0m')
		self.new_chache = True
		self.frames = []
		# print('\033[93m' + "已清空入缓冲区" + '\033[0m')
	
	# 获取麦克风数据
	def recording(self):
		
		# 读取音频
		chech_data = self.stream.read(self.CHUNK)
		# 状态检测
		status = self.vad.check_ontime(chech_data)
		if status == 2:
			self.silence_len = 0
			self.is_silence = False
			print('\033[93m' + "正在说话..." + '\033[0m')
			print("------")
			stream_data = self.stream.read(self.CHUNK)
			# 增加音量
			wave_data = np.frombuffer(stream_data, dtype=np.int16)
			self.frames.append(wave_data)
			if len(self.frames) >= self.max_size:
				self.long_frames.extend(self.frames)
				if len(self.long_frames) > self.max_size * 50:
					self.long_frames = self.long_frames[-self.max_size * 6:]
				# 缓存
				if len(self.long_frames)>0:
					self.save_wav(self.temp_save_path  + "temp.wav")
					# 产生缓存
					self.is_clear_temp = False
				
		# 静音中，清空最后一句话的缓存
		if status==0:
			self.silence_len+=1
			if self.silence_len >= self.max_silence_len:
				if not self.is_silence:
					self.is_silence = True
				# 最后一句话是否有缓存
				if len(self.long_frames)>self.max_size:
					print("===========")
					self.save_wav(self.temp_save_path + "temp.wav")
					# 清空最后一句话数据
					self.long_frames = []
					
				# 清空最后一句话的缓存，判断是否已经清空本句话
				if self.is_silence and not self.is_clear_temp:
					print(not self.is_clear_temp)
					self.is_clear_temp = True
					self.new_chache = False
					print("静音中。。。")
		

def recoding():
	serve = Recognize_server()
	print('\033[93m' + "recording" + '\033[0m')
	num = 0
	# 缓冲区大小
	while True:
		serve.recording()
		# file = open(serve.cache_flag, 'a', encoding='utf-8')
		# if serve.new_chache:
		# 	file.writelines("0")
		# 	serve.new_chache = False
		# 	num += 1
		# 	if num == 50:
		# 		file = open(serve.cache_flag, 'w', encoding='utf-8')
		# 		num = 0
		# file.close()
		time.sleep(0.1)
		

def recognizing(model,path):
	while True:
		# 上锁
		mutex.acquire()
		result1 = model.get_recognize(path + "temp.wav")
		print(result1)
		# 释放锁
		mutex.release()
		time.sleep(0.1)
	

if __name__ == '__main__':
	path = "../cache/"
	# 加载模型
	model = Recognize()
	# 创建锁
	mutex = threading.Lock()
	recoding_thread = threading.Thread(target=recoding)
	recognzing_thread = threading.Thread(target=recognizing,kwargs={"model":model,"path":path})
	recoding_thread.start()
	recognzing_thread.start()
	