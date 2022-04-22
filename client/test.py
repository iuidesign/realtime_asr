import pyaudio
import wave
from vad import Vad
import numpy as np



class Recognize_server():
	def __init__(self,CHUNK = 256,
	             FORMAT = pyaudio.paInt16,
	             CHANNELS = 1,
	             SAMPALE_RATE = 16000):
		self.CHUNK = 256
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 1
		self.SAMPALE_RATE = 16000  # 默认是 44100 保真度最高，识别的时候使用16000
		self.temp_save_path = "../cache/"
 
		# 保存录音
		self.audio = pyaudio.PyAudio()
		for i in range(self.audio.get_device_count()):
			print(i,self.audio.get_device_info_by_index(i)['name'])
		self.stream = self.audio.open(format=FORMAT,
		                channels=CHANNELS,
		                rate=SAMPALE_RATE,
		                input=True,
		                frames_per_buffer=CHUNK,
						input_device_index=0)

		# self.model=Recognize()
		
		self.vad = Vad(CHUNK)
		self.frames = []
		self.long_frames=[]
		self.max_size = 10
		
		# 缓冲区大小
		self.cur_cache_size=0
		self.max_cache_size=5
	
	# 保存麦克风数据，到时候会替换成向服务器传递的数据的功能
	def save_wav(self,path):
		wf = wave.open(path, 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
		wf.setframerate(self.SAMPALE_RATE)
		wf.writeframes(b''.join(self.long_frames))
		wf.close()
		print('\033[93m' + "已录入缓冲区" + '\033[0m')
		self.frames=[]
		print('\033[93m' + "已清空入缓冲区" + '\033[0m')
		
	# 获取麦克风数据
	def recording(self):
		chech_data = self.stream.read(self.CHUNK)
		status = self.vad.check_ontime(chech_data)
		if status==2:
			print('\033[93m' + "正在说话..." + '\033[0m')
			stream_data = self.stream.read(self.CHUNK)
			# 增加音量
			wave_data = np.frombuffer(stream_data, dtype=np.int16) * 5
			self.frames.append(wave_data)
			if len(self.frames) >=self.max_size:
				self.long_frames.extend(self.frames)
				if len(self.long_frames)>self.max_size*5:
					self.long_frames=self.long_frames[-self.max_size*5:]
				# 缓存
				# self.save_wav(self.temp_save_path+str(self.cur_cache_size)+"temp.wav")
				self.save_wav(self.temp_save_path + str(self.cur_cache_size) + "temp.wav")
				# self.save_wav("../cache/temp.wav")

		
		if status==0 and len(self.frames)>10:
			# 缓存
			self.long_frames.extend(self.frames)
			# self.save_wav(self.temp_save_path + str(num) + "temp.wav")
			self.save_wav(self.temp_save_path + str(self.cur_cache_size) + "temp.wav")
			# self.cur_cache_size += 1
			self.long_frames=[]
			self.frames=[]
			

if __name__ == '__main__':
	serve = Recognize_server()
	print('\033[93m' + "recording" + '\033[0m')
	# 缓冲区大小
	while True:
		serve.recording()
 

