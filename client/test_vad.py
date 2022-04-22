# -*- I Love Python!!! And You? -*-
# @Time    : 2022/4/11 21:56
# @Author  : sunao
# @Email   : 939419697@qq.com
# @File    : test4.py
# @Software: PyCharm
import pyaudio
import wave

if __name__ == '__main__':
	
	audio = pyaudio.PyAudio()
	stream = audio.open(rate=16000,
	           channels=1,
	           format=pyaudio.paInt16,
	           input=True,
	           input_device_index=0,
	           frames_per_buffer=1000)
	frames = []
	for i in range(5*16):
		data = stream.read(1000)
		frames.append(data)
	
	wf = wave.open("./temp.wav", 'wb')
	wf.setnchannels(1)
	wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
	wf.setframerate(16000)
	wf.writeframes(b''.join(frames))
	wf.close()
	
	
	
	
	print('Python')
