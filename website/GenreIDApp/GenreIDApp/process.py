from pydub import AudioSegment
import os, sys
import wave
import pylab
import csv
import random  # For simulated confidence
from keras.models import load_model, model_from_json
import json
from PIL import Image
import numpy as np

MAIN_FOLDER = "/tmp/processing"
WAVS_FOLDER = "/tmp/processing/wavs"
MP3S_FOLDER = "/tmp/processing/mp3s"
MP3S_FOLDER = "/tmp/processing/mp3s"
STATIC_PROCESSING_FOLDER = "/var/www/GenreIDApp/GenreIDApp/static/processing"
SPECTROS_FOLDER = "/var/www/GenreIDApp/GenreIDApp/static/processing/spectros"
MODEL_JSON = "/var/www/GenreIDApp/GenreIDApp/static/processing/model/model.json"
MODEL_H5 = "/var/www/GenreIDApp/GenreIDApp/static/processing/model/model.h5"

IMG_SIZE = 128

GENRE_IDS = {
    0: "Pop",
    1: "Instrumental",
    2: "Hip-Hop",
    3: "Experimental",
    4: "Electronic",
    5: "Folk",
    6: "Rock",
    7: "International"
}




def load_and_resize_image(filename, image_size):
    img = Image.open(filename).convert('L')
    img = img.resize((image_size, image_size), resample=Image.ANTIALIAS)
    image_data = np.asarray(img, dtype=np.uint8).reshape(1, image_size,image_size,1)
    image_data = image_data/255.
    return image_data


def get_wav_info(wav_file_path):
    wav = wave.open(wav_file_path, 'r')
    frames = wav.readframes(-1)
    sound_info = pylab.fromstring(frames, 'Int16')
    frame_rate = wav.getframerate()
    wav.close()
    return sound_info, frame_rate


def make_spectro(wav_file_path):
    base_name = os.path.basename(wav_file_path)
    spectro_path = os.path.join(SPECTROS_FOLDER, "{}.png".format(base_name[:-4]))
    sound_info, frame_rate = get_wav_info(wav_file_path)
    pylab.style.use('grayscale')
    fig, ax = pylab.subplots(1, num=None, figsize=(1,1), dpi=128)
    fig.subplots_adjust(left=0, right=1, bottom=0,top=1)
    pylab.axis('off')
    # pxx, freqs, bins, im = ax.specgram(x=sound_info, fs=frame_rate, NFFT=512, noverlap=0)
    # ax.axis('off')
    # ax.gray()
    # pylab.figure(num=None, figsize=(1,1), dpi=128)
    # pylab.subplot(111)

    # pylab.title('spectrogram of %r' % sample)
    pylab.specgram(sound_info, Fs=frame_rate)
    pylab.savefig(spectro_path)
    pylab.close()

    return spectro_path


def predict_genre(spectro_path):
    # Load model.
    with open(MODEL_JSON) as f:
        data = json.load(f)
        json_string = json.dumps(data)

    model = model_from_json(json_string)
    model.load_weights(MODEL_H5)
    # Load spectrogram.
    spectro_data = load_and_resize_image(spectro_path, IMG_SIZE)
    # Make prediction.
    result = model.predict(spectro_data)
    genre = GENRE_IDS[result.argmax()]
    confidence = result.max()
    return genre, confidence


def process_mp3(mp3_file_path):
    base_name = os.path.basename(mp3_file_path)

    for dir_ in [MAIN_FOLDER, STATIC_PROCESSING_FOLDER, SPECTROS_FOLDER, WAVS_FOLDER, MP3S_FOLDER]:
        try:
            os.mkdir(dir_)
        except FileExistsError:
            continue

    mp3_obj = AudioSegment.from_mp3(mp3_file_path)
    segmented_mp3_arr = list(mp3_obj[::3000]) # Makes slices.

    wav_file_path = os.path.join(WAVS_FOLDER, "{}-0.wav".format(base_name[:-4]))
    segmented_mp3_arr[0].export(wav_file_path, format='wav')

    spectro_path = make_spectro(wav_file_path)
    genre, confidence = predict_genre(spectro_path)
    
    return genre, spectro_path, confidence

if __name__ == '__main__':
    mp3_file_path = sys.argv[1]
    genre, spectro_path, confidence = process_mp3(mp3_file_path)

    print(genre, spectro_path, confidence)
