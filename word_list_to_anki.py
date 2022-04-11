# Code to take a txt file and convert it to an anki CLOZE deck with TTS audio from Microsoft Azure
from fileinput import filename
from re import I
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk
import argparse
import time


SPEECH_KEY, SERVICE_REGION = "563a007c698f49db813a24a6fa604b9f", "eastus"
CN = "zh-TW-YunJheNeural"
JA = "ja-JP-KeitaNeural"


def parse_args():
    """
    Parse all command line arguments
    Parameters:
        - None
    Returns:
        - args (argparse.Namespace): The list of arguments passed in
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-inp",type=str, help = "Input file", default = "text.txt")
    parser.add_argument("-outp",type=str, help = "Output directory", default = "./output/")
    parser.add_argument("-lang",type=str, help = "Language of file [ja, cn]", default = "ja")


    args = parser.parse_args()
    
    return args

def speech_synthesis_to_mp3_file(sentence, out_name, lang):
    """performs speech synthesis to an mp3 file"""
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
    speech_config.speech_synthesis_voice_name = lang
    file_config = speechsdk.audio.AudioOutputConfig(filename = out_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)


    result = speech_synthesizer.speak_text_async(sentence).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}], and the audio was saved to [{}]".format(sentence, out_name))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

def cloze(sentence):
    
    cloze_items = []


    # Scan for cloze items
    for i in range(len(sentence)):
            curr_letter = sentence[i]
            if curr_letter == "[":
                    x = ""
                    j = i
                    while x != "]":
                        x = sentence[j]
                        j += 1

                    cloze_items.append(["{{c" + str(len(cloze_items) + 1) + "::" + sentence[i+1:j-1] + "}}", sentence[i:j]])
    
    # Insert cloze items
    for cloze_item in cloze_items:
        sentence = sentence.replace(cloze_item[1], cloze_item[0])

    return sentence

def parse_txt_file(input_file, lang, output_dir):
    # Input text file lines must be of format SENTENCE | NOTES
    # Reads in sentences / gets cloze form, returns list of sentences to output
    f = open(input_file, 'r', encoding="utf-8")
    lines = f.readlines()

    out_lines = []

    for index, line in enumerate(lines):
       
        s = line.split("|")
        sentence = s[0]
        notes = s[1]

        # First get audio (throttle it)
        out_name = datetime.now().strftime("%d%m%Y%H:%M:%S").replace(":","") + "_" + lang + "_" + str(index) + ".mp3"
        sentence_clean = sentence.replace("[", "").replace("]", "")

        if index + 1 % 20 == 0:
            print("Processed TTS for 20 sentences, waiting 1 minute...")
            start = time.time()
            while(time.time() - start < 65):
                continue

        speech_synthesis_to_mp3_file(sentence_clean, output_dir + out_name, lang)

        # Convert to cloze
        sentence = cloze(sentence)

        # Package for output
        out_lines.append((sentence, out_name, notes))
    
    return out_lines

def output_anki_file(lines, lang, output_dir):
    file_name = output_dir + lang + "_out.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        for line in lines:
            x = line[0] + "|" + line[1] + "|" + line[2]
            f.write(x)
    
        f.close()

if __name__ == "__main__":
    
    args = parse_args()

    if args.lang == "ja":
        lang = JA
    else:
        lang = CN

    input_file = args.inp
    output_dir = args.outp

    lines = parse_txt_file(input_file, lang, output_dir)

    output_anki_file(lines, lang, output_dir)