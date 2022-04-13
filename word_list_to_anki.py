# Code to take a txt file and convert it to an anki CLOZE deck with TTS audio from Microsoft Azure
import azure.cognitiveservices.speech as speechsdk
import argparse
import time
from fileinput import filename
from re import I
from datetime import datetime
from numpy import true_divide
import requests
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import shutil

SPEECH_KEY, SERVICE_REGION = "563a007c698f49db813a24a6fa604b9f", "eastus"
IMAGE_KEY = "6f1b8dd3ae454b14bc7da591b22229c5"
SEARCH_URL = "https://api.bing.microsoft.com/v7.0/images/search"

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

def generate_image(search_term, out_name, lang):

    if lang == "zh-TW-YunJheNeural":
        mkt = "zh-TW"
        set_lang = "zh-hant"
    else:
        mkt = "ja-JP"
        set_lang = "jp"

    thumbnail_urls = []

    # Keep making requests of different length string till result achieved
    for i in range(len(search_term), -1, -1):

        # Throttle the search
        print("Throttling image search at index: " + str(i))
        start = time.time()
        while(time.time() - start < 2):
            continue

        # Setup search
        search_term = search_term[0:i]
        headers = {"Ocp-Apim-Subscription-Key" : IMAGE_KEY}
        params  = {"q": search_term, "license": "public", "imageType": "photo", "mkt": mkt, "setLang": set_lang}

        # Get response
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        search_results = response.json()
        thumbnail_urls = [img["thumbnailUrl"] for img in search_results["value"][:1]]

        # If empty response, move search backward one char (from end)
        if len(thumbnail_urls) > 0:
            break

    # Once result found, write to file
    image_data = requests.get(thumbnail_urls[-1], stream=True)
    with open(out_name, 'wb') as out_file:
        shutil.copyfileobj(image_data.raw, out_file)
    
def generate_cloze(sentence, hints):
    
    cloze_items = []

    # Scan for cloze items
    for i in range(len(sentence)):
            if sentence[i] == "[":
                    x = ""
                    j = i
                    while x != "]":
                        x = sentence[j]
                        j += 1

                    cloze_items.append(["{{c" + str(len(cloze_items) + 1) + "::" + sentence[i+1:j-1] + "::" + hints[len(cloze_items)] + "}}", sentence[i:j]])
    
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
        hints = s[2].strip().split(",")

        # First get audio (throttle it)
        out_name = datetime.now().strftime("%d%m%Y%H:%M:%S").replace(":","") + "_" + lang + "_" + str(index)
        sentence_clean = sentence.replace("[", "").replace("]", "")

        if (index + 1) % 20 == 0:
            print("Processed 20 sentences, waiting 1 minute...")
            start = time.time()
            while(time.time() - start < 65):
                continue

        speech_synthesis_to_mp3_file(sentence_clean.strip(), output_dir + out_name + ".mp3", lang)
        # generate_image(sentence_clean.strip(), output_dir + out_name + ".jpg", lang)

        # Convert to cloze
        sentence = generate_cloze(sentence, hints)

        # Package for output
        out_lines.append((sentence, out_name + ".mp3", notes))
    
    return out_lines

def output_anki_file(lines, lang, output_dir):
    file_name = output_dir + lang + "_out.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        for line in lines:
            x = line[0] + "|" + "[sound:" + line[1] + "]" + "|" + line[2] +"\n"
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