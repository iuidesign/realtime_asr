from email.policy import default
import time

import pyaudio
import wave
import sys
import os
# curPath = os.path.abspath(os.path.dirname(__file__))
# rootPath = os.path.split(curPath)[0]
# sys.path.append(rootPath)
sys.path.append("../decoder/")
from recognize import Recognize
import numpy as np
from vad import Vad

class RecognizeService():
	def __init__(self):
		self.CHUNK = 1024
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.SAMPALE_RATE = 16000  # 默认是 44100 保真度最高，识别的时候使用16000
		self.temp_save_path = "../cache/temp1.wav"
		self.p = pyaudio.PyAudio()
		# self.p.terminate()
		self.model = Recognize()
		self.stream = self.p.open(format=self.FORMAT,
		                channels=self.CHANNELS,
		                rate=self.SAMPALE_RATE,
		                input=True,
		                frames_per_buffer=self.CHUNK)
		self.v = Vad(self.CHUNK)
		
		
	# 保存麦克风数据
	def save_wav(self,frames, save_path):
		wf = wave.open(save_path, 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
		wf.setframerate(self.SAMPALE_RATE)
		wf.writeframes(b''.join(frames))
		wf.close()
	
	# print('\033[93m' + "已录入缓冲区" + '\033[0m')
	
	# 获取麦克风数据
	def recording(self,save_path):
		
		print('\033[93m' + "recording" + '\033[0m')
		
		# 缓冲区大小
		frames = []
		max_size = 5
		long_frames = []
		next=""
		num=0
		is_speak=False
		result=""
		while True:
			stream_data = self.stream.read(self.CHUNK,exception_on_overflow=False)
			status = self.v.check_ontime(stream_data)
			if status==2:
				is_speak=True
				# 增加音量
				wave_data = np.frombuffer(stream_data, dtype=np.int16)
				frames.append(wave_data)
				if len(frames) >= max_size:
					long_frames.extend(frames)
					# if len(long_frames) > max_size * 10:
					# 	long_frames = long_frames[-max_size * 10:]
						# 缓存
						# self.save_wav(long_frames, self.temp_save_path)
						# result = self.model.get_recognize(self.temp_save_path)
						# # 清空缓冲区
						# frames = []
						# long_frames = []
						# if next == result:
						# 	continue
						# next = result
						# continue
					# 缓存
					self.save_wav(long_frames, self.temp_save_path)
					result = self.model.get_recognize(self.temp_save_path)
					# 清空缓冲区
					frames = []
					if next == result:
						continue
					next = result
					print(result)
					
						
			if status==0:
				num += 1
				if num == 2: # 停止识别
					if is_speak:
						if len(frames)>0 and len(long_frames)>0: # 判断是不是最后的尾音
							long_frames.extend(frames)
							self.save_wav(long_frames, self.temp_save_path)
							result = self.model.get_recognize(self.temp_save_path)
						if result != "":
							print(result)
					num = 0
					# 静音
					long_frames = []
					# 清空缓冲区
					frames = []
					is_speak=False
					result=""

if __name__ == '__main__':
	service = RecognizeService()
	service.recording(service.temp_save_path)