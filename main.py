import multiprocessing
import os
import re
import time
import wave
import torch
from pydub import AudioSegment, silence

import whisper
import pyaudio

file_path = 'C:\\Users\\GlebHleb\\Desktop\\temp'


def check_void(sh_var, lock):
    global abs_path
    check_files = os.listdir(path=file_path)

    for file_name in check_files:
        abs_path = file_path + '\\' + file_name

        if re.search("command", abs_path):
            continue

        my_audio = AudioSegment.from_file(abs_path)
        sile = silence.detect_silence(my_audio, min_silence_len=1, silence_thresh=-50)
        sile = [((start / 1000), (stop / 1000)) for start, stop in sile]  # convert to sec

        if len(sile) < 1:
            continue

        average = 0.0
        duration = 1.0

        for start, stop in sile:
            average += stop - start

        detect_empty_sample = average / (duration / 100)
        maybe_empty = detect_empty_sample > 77

        if maybe_empty:
            os.remove(abs_path)

            with lock:
                print(sh_var.value)

                if sh_var.value >= 3:
                    continue

                sh_var.value += 1
        else:

            with lock:
                sh_var.value = 2
                return abs_path


def recognize(sh_var, lock):
    print("Process - 1 Recognize")
    task = "transcribe"
    device = torch.device("cuda", 3)
    model = whisper.load_model("small", device)

    kwargs = {}
    kwargs['language'] = 'ru'
    kwargs['verbose'] = False
    kwargs['task'] = 'transcribe'
    kwargs['temperature'] = 0
    kwargs['best_of'] = None
    kwargs['beam_size'] = None
    kwargs['patience'] = None
    kwargs['length_penalty'] = None
    kwargs['suppress_tokens'] = "-1"
    kwargs['initial_prompt'] = None
    kwargs['condition_on_previous_text'] = False  # seems source of false Transcripts
    # kwargs['fp16'] = True  # set false if using cpu
    kwargs['compression_ratio_threshold'] = 2.4  # 2.4
    kwargs['logprob_threshold'] = 0.0  # -1.0 #-0.5
    # kwargs['no_speech_threshold'] = 0.2  # 0.6 #0.2

    while True:

        search_file = check_void(sh_var, lock)

        if search_file:
            result = model.transcribe(search_file, **kwargs)
        else:
            continue

        text = result["text"]
        # whisper.transcribe(model, audio=s['fname'], verbose=False, **options)
        if re.search('(алиса)|(алис)|(лиса)|(алюса)|(ариса)', text.lower()):
            print("Слушаю вас!")

            with lock:
                sh_var.value = 0

        elif re.search("((\s)*((дорогая(,)*)*\sя)\sдома)", text.lower()):

            print("AC/DC")
        elif re.search("(стоп)|(stop)|(остоновись)", text.lower()):

            print("Конечнаааяя...")
            with lock:
                sh_var.value = 3

        print(text)
        os.remove(search_file)


def polling_every_second():
    print("Process - 2 polling_every_second run")
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    while True:

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, frames_per_buffer=CHUNK,
                        input_device_index=0, input=True)

        frames = []

        for i in range(0, int(RATE / CHUNK * 1)):
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(file_path + '\\' + time.time().__str__() + '.wav', 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


def record_command(shared_variable, locker):
    print("Process - 3 record_command run")
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    while True:

        with locker:
            if shared_variable.value <= 3:

                while True:

                    p = pyaudio.PyAudio()

                    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, frames_per_buffer=CHUNK,
                                    input_device_index=0, input=True)

                    frames = []

                    while True:
                        with locker:
                            if shared_variable.value >= 3:
                                data = stream.read(CHUNK)
                                frames.append(data)
                                continue
                            break

                    # if RECORD_SECONDS != 1 & flag:
                    ##Закрытие потока и освобождение ресурсов
                    stream.stop_stream()
                    stream.close()
                    p.terminate()

                    wf = wave.open(file_path + '\\' + time.time().__str__() + '.wav', 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))
                    wf.close()
    # bool_0 = False
    # record_audio_in_two_threads(shared_variable, locker, bool_0)
    #
    # with locker:
    #     if shared_variable.value <= 0:
    #         bool_1 = True
    #         record_audio_in_two_threads(shared_variable, locker, bool_1)


# def record_audio_in_two_threads(shared_variable, locker, bool_1):
#     print("Proc_3")
#     while True:
#
#         with locker:
#             if shared_variable.value <= 3:
#                 CHUNK = 1024
#                 FORMAT = pyaudio.paInt16
#                 CHANNELS = 1
#                 RATE = 44100
#
#                 while True:
#
#                     p = pyaudio.PyAudio()
#
#                     stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, frames_per_buffer=CHUNK,
#                                     input_device_index=0, input=True)
#
#                     frames = []
#
#                     if bool_1:
#                         while True:
#                             with locker:
#                                 if shared_variable.value <= 3:
#                                     data = stream.read(CHUNK)
#                                     frames.append(data)
#                                     continue
#                                 break
#                     else:
#                         for i in range(0, int(RATE / CHUNK * 1)):
#                             data = stream.read(CHUNK)
#                             frames.append(data)
#
#                     # if RECORD_SECONDS != 1 & flag:
#                     ##Закрытие потока и освобождение ресурсов
#                     stream.stop_stream()
#                     stream.close()
#                     p.terminate()
#
#                     wf = wave.open(file_path + '\\' + time.time().__str__() + '.wav', 'wb')
#                     wf.setnchannels(CHANNELS)
#                     wf.setsampwidth(p.get_sample_size(FORMAT))
#                     wf.setframerate(RATE)
#                     wf.writeframes(b''.join(frames))
#                     wf.close()


def save_audio_in_file(command, frames, p):
    wf = wave.open(file_path + '\\' + time.time().__str__() + command + '.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(b''.join(frames))
    wf.close()


# def record_command(Locker, sh_var):
#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt16,
#                     channels=1,
#                     rate=44100,
#                     input=True,
#                     frames_per_buffer=1024)
#     frames = []
#
#     while True:
#         with Locker:
#             if sh_var.value == 0:
#                 print("rec_com_start")
#
#                 for i in range(0, 10):
#                     print("rec_com")
#                     data = stream.read(1024)
#                     frames.append(data)
#                     time.sleep(0.01)
#                     sh_var += 1
#                     if sh_var >= 5:
#                         sh_var.value = 3
#                         break
#                     with Locker:
#                         if sh_var.value == 3:
#                             break
#                 save_audio_in_file("command", frames, p)
#                 frames.clear()


if __name__ == "__main__":
    locker = multiprocessing.Lock()
    shared_variable = multiprocessing.Value("i", 3)

    process_3 = multiprocessing.Process(target=record_command, args=(shared_variable, locker))
    process_3.start()

    process_2 = multiprocessing.Process(target=polling_every_second)
    process_2.start()

    process_1 = multiprocessing.Process(target=recognize, args=(shared_variable, locker))
    process_1.start()
