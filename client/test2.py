import time

import pyaudio
import wave
from decoder.recognize import Recognize
import numpy as np

class RecognizeService():
	def __init__(self):
		self.CHUNK = 1000
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.SAMPALE_RATE = 16000  # 默认是 44100 保真度最高，识别的时候使用16000
		self.temp_save_path = "../cache/temp1.wav"
		self.p = pyaudio.PyAudio()
		self.model = Recognize()
		self.stream = self.p.open(format=self.FORMAT,
		                channels=self.CHANNELS,
		                rate=self.SAMPALE_RATE,
		                input=True,
		                frames_per_buffer=self.CHUNK,
		                input_device_index=0)
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
		max_size = 2
		long_frames = []
		next=""
		while True:
			stream_data = self.stream.read(self.CHUNK,exception_on_overflow=False)
			# 增加音量
			wave_data = np.frombuffer(stream_data, dtype=np.int16)
			frames.append(wave_data)
			if len(frames) >= max_size:
				long_frames.extend(frames)
				if len(long_frames) > max_size * 20:
					long_frames = long_frames[-max_size * 6:]
				# 缓存
				if len(long_frames) > 0:
					self.save_wav(long_frames,self.temp_save_path)
					result = self.model.get_recognize(self.temp_save_path)
					if next==result:
						continue
					print(result)
					next=result
					# 清空缓冲区
					frames = []
				

if __name__ == '__main__':
	service = RecognizeService()
	service.recording(service.temp_save_path)