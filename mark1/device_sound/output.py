# coding=utf-8


import sounddevice as sd

from paddlespeech.cli.tts.infer import TTSExecutor
tts = TTSExecutor()


def talk(text):
     wav, samples = tts(text=text, raw_output=True)
     sd.play(wav, samples)
     sd.wait()


if __name__ == '__main__':
    talk('你好')
