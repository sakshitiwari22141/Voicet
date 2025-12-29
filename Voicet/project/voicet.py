from flask import Flask, render_template, request, redirect, session, flash, make_response, send_file
from werkzeug.utils import secure_filename
import os
import subprocess
import whisper
import pandas as pd
# from pytube import YouTube (Removed as we use yt-dlp in main.py)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import re
import torch
import functools
import inspect
import numpy as np

# Fix for PyTorch 2.6+ weights_only issue across all libraries (including Whisper/TTS)
def patch_torch_load():
    try:
        original_load = torch.load
        sig = inspect.signature(original_load)
        if 'weights_only' in sig.parameters:
            @functools.wraps(original_load)
            def safe_load(*args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            torch.load = safe_load
    except Exception:
        pass

patch_torch_load()
import wave
import random
import string


from scipy.io.wavfile import write
import sys

# sys.path.append('/home/shubhankar/Project/VAKYANSH_TTS')
vakyansh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'VAKYANSH_TTS'))
sys.path.append(vakyansh_path)
from tts_infer.tts import TextToMel, MelToWav
from tts_infer.transliterate import XlitEngine
from tts_infer.num_to_word_on_sent import normalize_nums

if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([np.core.multiarray.scalar])

# Global cache for TTS models to avoid reloading on every request
tts_model_cache = {}



codes_as_string = '''Acehnese (Arabic script)	ace_Arab
Acehnese (Latin script)	ace_Latn
Mesopotamian Arabic	acm_Arab
Ta’izzi-Adeni Arabic	acq_Arab
Tunisian Arabic	aeb_Arab
Afrikaans	afr_Latn
South Levantine Arabic	ajp_Arab
Akan	aka_Latn
Amharic	amh_Ethi
North Levantine Arabic	apc_Arab
Modern Standard Arabic	arb_Arab
Modern Standard Arabic (Romanized)	arb_Latn
Najdi Arabic	ars_Arab
Moroccan Arabic	ary_Arab
Egyptian Arabic	arz_Arab
Assamese	asm_Beng
Asturian	ast_Latn
Awadhi	awa_Deva
Central Aymara	ayr_Latn
South Azerbaijani	azb_Arab
North Azerbaijani	azj_Latn
Bashkir	bak_Cyrl
Bambara	bam_Latn
Balinese	ban_Latn
Belarusian	bel_Cyrl
Bemba	bem_Latn
Bengali	ben_Beng
Bhojpuri	bho_Deva
Banjar (Arabic script)	bjn_Arab
Banjar (Latin script)	bjn_Latn
Standard Tibetan	bod_Tibt
Bosnian	bos_Latn
Buginese	bug_Latn
Bulgarian	bul_Cyrl
Catalan	cat_Latn
Cebuano	ceb_Latn
Czech	ces_Latn
Chokwe	cjk_Latn
Central Kurdish	ckb_Arab
Crimean Tatar	crh_Latn
Welsh	cym_Latn
Danish	dan_Latn
German	deu_Latn
Southwestern Dinka	dik_Latn
Dyula	dyu_Latn
Dzongkha	dzo_Tibt
Greek	ell_Grek
English	eng_Latn
Esperanto	epo_Latn
Estonian	est_Latn
Basque	eus_Latn
Ewe	ewe_Latn
Faroese	fao_Latn
Fijian	fij_Latn
Finnish	fin_Latn
Fon	fon_Latn
French	fra_Latn
Friulian	fur_Latn
Nigerian Fulfulde	fuv_Latn
Scottish Gaelic	gla_Latn
Irish	gle_Latn
Galician	glg_Latn
Guarani	grn_Latn
Gujarati	guj_Gujr
Haitian Creole	hat_Latn
Hausa	hau_Latn
Hebrew	heb_Hebr
Hindi	hin_Deva
Chhattisgarhi	hne_Deva
Croatian	hrv_Latn
Hungarian	hun_Latn
Armenian	hye_Armn
Igbo	ibo_Latn
Ilocano	ilo_Latn
Indonesian	ind_Latn
Icelandic	isl_Latn
Italian	ita_Latn
Javanese	jav_Latn
Japanese	jpn_Jpan
Kabyle	kab_Latn
Jingpho	kac_Latn
Kamba	kam_Latn
Kannada	kan_Knda
Kashmiri (Arabic script)	kas_Arab
Kashmiri (Devanagari script)	kas_Deva
Georgian	kat_Geor
Central Kanuri (Arabic script)	knc_Arab
Central Kanuri (Latin script)	knc_Latn
Kazakh	kaz_Cyrl
Kabiyè	kbp_Latn
Kabuverdianu	kea_Latn
Khmer	khm_Khmr
Kikuyu	kik_Latn
Kinyarwanda	kin_Latn
Kyrgyz	kir_Cyrl
Kimbundu	kmb_Latn
Northern Kurdish	kmr_Latn
Kikongo	kon_Latn
Korean	kor_Hang
Lao	lao_Laoo
Ligurian	lij_Latn
Limburgish	lim_Latn
Lingala	lin_Latn
Lithuanian	lit_Latn
Lombard	lmo_Latn
Latgalian	ltg_Latn
Luxembourgish	ltz_Latn
Luba-Kasai	lua_Latn
Ganda	lug_Latn
Luo	luo_Latn
Mizo	lus_Latn
Standard Latvian	lvs_Latn
Magahi	mag_Deva
Maithili	mai_Deva
Malayalam	mal_Mlym
Marathi	mar_Deva
Minangkabau (Arabic script)	min_Arab
Minangkabau (Latin script)	min_Latn
Macedonian	mkd_Cyrl
Plateau Malagasy	plt_Latn
Maltese	mlt_Latn
Meitei (Bengali script)	mni_Beng
Halh Mongolian	khk_Cyrl
Mossi	mos_Latn
Maori	mri_Latn
Burmese	mya_Mymr
Dutch	nld_Latn
Norwegian Nynorsk	nno_Latn
Norwegian Bokmål	nob_Latn
Nepali	npi_Deva
Northern Sotho	nso_Latn
Nuer	nus_Latn
Nyanja	nya_Latn
Occitan	oci_Latn
West Central Oromo	gaz_Latn
Odia	ory_Orya
Pangasinan	pag_Latn
Eastern Panjabi	pan_Guru
Papiamento	pap_Latn
Western Persian	pes_Arab
Polish	pol_Latn
Portuguese	por_Latn
Dari	prs_Arab
Southern Pashto	pbt_Arab
Ayacucho Quechua	quy_Latn
Romanian	ron_Latn
Rundi	run_Latn
Russian	rus_Cyrl
Sango	sag_Latn
Sanskrit	san_Deva
Santali	sat_Olck
Sicilian	scn_Latn
Shan	shn_Mymr
Sinhala	sin_Sinh
Slovak	slk_Latn
Slovenian	slv_Latn
Samoan	smo_Latn
Shona	sna_Latn
Sindhi	snd_Arab
Somali	som_Latn
Southern Sotho	sot_Latn
Spanish	spa_Latn
Tosk Albanian	als_Latn
Sardinian	srd_Latn
Serbian	srp_Cyrl
Swati	ssw_Latn
Sundanese	sun_Latn
Swedish	swe_Latn
Swahili	swh_Latn
Silesian	szl_Latn
Tamil	tam_Taml
Tatar	tat_Cyrl
Telugu	tel_Telu
Tajik	tgk_Cyrl
Tagalog	tgl_Latn
Thai	tha_Thai
Tigrinya	tir_Ethi
Tamasheq (Latin script)	taq_Latn
Tamasheq (Tifinagh script)	taq_Tfng
Tok Pisin	tpi_Latn
Tswana	tsn_Latn
Tsonga	tso_Latn
Turkmen	tuk_Latn
Tumbuka	tum_Latn
Turkish	tur_Latn
Twi	twi_Latn
Central Atlas Tamazight	tzm_Tfng
Uyghur	uig_Arab
Ukrainian	ukr_Cyrl
Umbundu	umb_Latn
Urdu	urd_Arab
Northern Uzbek	uzn_Latn
Venetian	vec_Latn
Vietnamese	vie_Latn
Waray	war_Latn
Wolof	wol_Latn
Xhosa	xho_Latn
Eastern Yiddish	ydd_Hebr
Yoruba	yor_Latn
Yue Chinese	yue_Hant
Chinese (Simplified)	zho_Hans
Chinese (Traditional)	zho_Hant
Standard Malay	zsm_Latn
Zulu	zul_Latn'''

codes_as_string = codes_as_string.split('\n')

flores_codes = {}
for code in codes_as_string:
    lang, lang_code = code.split('\t')
    flores_codes[lang] = lang_code


# --- Model Configuration ---
# Whisper Model (Transcription)
# Options: 'tiny.en', 'base.en', 'small.en', 'medium.en'
# 'base.en' is a good balance of speed and accuracy. 
WHISPER_MODEL_NAME = 'base.en'
asr_model = whisper.load_model(WHISPER_MODEL_NAME)

# Transcription Options
# Increased beam_size/best_of improves quality but needs more CPU.
transcribe_options = dict(
    beam_size=5, 
    best_of=5, 
    without_timestamps=False, 
    language='English', 
    fp16=False
)

device = "cpu"
if torch.cuda.is_available():
    device = "cuda"

# NLLB Model (Translation)
# Options: 'facebook/nllb-200-distilled-600M' (Fast), 'facebook/nllb-200-distilled-1.3B' (Accurate)
TASK = "translation"
CKPT = "facebook/nllb-200-distilled-1.3B"

print(f"Loading {CKPT}...")
model = AutoModelForSeq2SeqLM.from_pretrained(CKPT)
tokenizer = AutoTokenizer.from_pretrained(CKPT)




app = Flask(__name__)
# hardcoded credentials
USERS = {'user1': 'pass1', 'user2': 'pass2'}
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mkv'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        url = request.form["url"]
        file = request.files['file']
        language_voice = request.form.get('translateTo')
        gender_voice = request.form.get('gender')
        if gender_voice == "male":
            gender = 'male'
        else :
            gender = 'female'
        print(f'File Uploaded : {file.filename}')
        print(f'Translate To : {language_voice}')
        print(f'Voice Gender : {gender_voice}')
        if file and allowed_file(file.filename):
            filename_original = secure_filename(file.filename)
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            extension = os.path.splitext(file.filename)[1]
            filename = random_string + extension
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            flash('File Uploaded','success')
            print(video_path)
            translate_video(video_path,language_voice,gender_voice,random_string)
            flash('Video Translated Succesfully','success')
            return send_file(f'{random_string}.mp4',   download_name=(f'Dubbed_{language_voice}_{gender_voice}_{filename_original}.mp4') ,as_attachment=True)

        elif url:
            youtube = YouTube(url)
            filename_original = youtube.title
            video = youtube.streams.get_highest_resolution()
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            filename = random_string + '.mp4'
            video_path = video.download(filename=filename)
            print(f'Filename : {filename}')
            print(f'Filepath : {video_path}')
            flash('File Uploaded','success')
            print(video_path)
            translate_video(video_path,language_voice,gender_voice, random_string)
            flash('Video Translated Succesfully','success')
            return send_file(f'{random_string}.mp4',   download_name=(f'Dubbed_{language_voice}_{gender_voice}_{filename_original}.mp4') ,as_attachment=True)


        else:
            flash('File not allowed. Only mp4, avi and mkv are allowed','warning')
            return redirect('/')
    return redirect('/')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # check if the entered credentials match the hardcoded ones
        if request.form['username'] in USERS and request.form['password'] == USERS[request.form['username']]:
            session['username'] = request.form['username']
            return redirect('/')
        else:
            flash('Invalid credentials','danger')
            return redirect('/login')
    else:
        return render_template('login.html')

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    # session.cookie.clear()
    session.pop('username', None)
    return redirect('/')

def get_captions(file_path):
    audio = whisper.load_audio(file_path)
    
    try:
        # Try with the high-quality options defined at the top
        transcription = asr_model.transcribe(audio, **transcribe_options)
    except Exception as e:
        print(f"⚠️ High-quality transcription failed ({e}). Retrying with simpler settings...")
        # Fallback to beam_size=1 to avoid "cannot reshape tensor" errors
        fallback_options = transcribe_options.copy()
        fallback_options['beam_size'] = 1
        fallback_options['best_of'] = 1
        transcription = asr_model.transcribe(audio, **fallback_options)
    
    rows = []
    for segment in transcription['segments']:
        rows.append({'START' : segment['start'], 'END' : segment['end'], 'TEXT' : segment['text'] })
    
    df = pd.DataFrame(rows)
    return df

def convert_floats(row):
    # define regular expression pattern to match float values
    pattern = r'\d+\.\d+'
    # split text into words
    words = row['TEXT'].split()
    # check each word for a float
    for i in range(len(words)):
        if words[i].endswith('.'):
            # remove last full stop from word
            words[i] = words[i][:-1]
        try:
            float_val = float(words[i])
            # if float found, convert to string format
            words[i] = str(int(float_val)) + ' decimal ' + str(int(round (float_val % 1,2) * 10))
        except ValueError:
            pass
    # join words back into text string
    return ' '.join(words)


import logging
logger = logging.getLogger(__name__)

def translate(df, src_lang="eng_Latn", tgt_lang="hin_Deva", max_batch_chars=400):
    """
    Translates segments in the dataframe.
    Uses context batching: groups multiple short segments into a single chunk
    to provide better context (gender, tense, etc.) for the NLLB model.
    """
    translation_pipeline = pipeline(TASK,
                                    model=model,
                                    tokenizer=tokenizer,
                                    src_lang=src_lang,
                                    tgt_lang=tgt_lang,
                                    max_length=400,
                                    device=device)

    # REVISED ROBUST APPROACH: Prepend previous segment as context (prefixing)
    # This is a common trick for NMT models.
    
    output_column = []
    previous_context = ""
    
    for index, row in df.iterrows():
        current_text = row['TEXT'].strip()
        if not current_text:
            output_column.append("")
            continue
            
        # Prepend previous segment if available for context
        # We don't want to translate the whole thing, just use it for context.
        # NLLB doesn't have a "context" parameter, so we just give it more text.
        
        try:
            if previous_context:
                full_input = f"{previous_context} {current_text}"
                result = translation_pipeline(full_input)
                if result and len(result) > 0:
                    translated_full = result[0]['translation_text']
                    
                    # Try to extract only the last part (the current segment's translation)
                    # This is tricky without knowing the alignment. 
                    
                    output_value = translated_full # Fallback
                    # If the translation has a clear sentence break, take the last part
                    # (Very rough heuristic for Hindi/English)
                    if '।' in translated_full:
                        output_value = translated_full.split('।')[-1].strip()
                    elif '.' in translated_full:
                         output_value = translated_full.split('.')[-1].strip()
                else:
                    logger.warning(f"Translation returned empty result for: {full_input}")
                    output_value = current_text
            else:
                result = translation_pipeline(current_text)
                if result and len(result) > 0:
                    output_value = result[0]['translation_text']
                else:
                    logger.warning(f"Translation returned empty result for: {current_text}")
                    output_value = current_text
        except Exception as e:
            logger.error(f"Translation error at index {index}: {e}")
            output_value = current_text # Fallback to original text on error
            
        output_column.append(output_value)
        previous_context = current_text
        
    df['TRANSLATION'] = output_column
    return df

def translit(text, lang):
    reg = re.compile(r'[a-zA-Z]')
    engine = XlitEngine(lang)
    words = [engine.translit_word(word, topk=1)[lang][0] if reg.match(word) else word for word in text.split()]
    updated_sent = ' '.join(words)
    return updated_sent


def run_tts(text, lang='hi',count=0):
#    language_voice= language_voice.lower()
#    gender_voice = gender_voice.lower()

#    glow_model_dir=f'/home/shubhankar/TestProjects/WebApp/VAKYANSH_TTS/tts_infer/translit_models/{language_voice}/{gender_voice}/glow_ckp'
#    hifi_model_dir=f'/home/shubhankar/TestProjects/WebApp/VAKYANSH_TTS/tts_infer/translit_models/{language_voice}/{gender_voice}/hifi_ckp'

#    print('#'*200)
#    print(language_voice)
#    print(gender_voice)
#    print(glow_model_dir)
#    print(hifi_model_dir)
#    print('#'*200)

#    text_to_mel = TextToMel(glow_model_dir=glow_model_dir, device=device)
#    mel_to_wav = MelToWav(hifi_model_dir=hifi_model_dir, device=device)


    logger.info(f"Original Text from user: {text}")
    if lang == 'hi':
        text = text.replace('।', '.') # only for hindi models
    text_num_to_word = normalize_nums(text, lang) # converting numbers to words in lang
    text_num_to_word_and_transliterated = translit(text_num_to_word, lang) # transliterating english words to lang
    logger.info(f"Text after preprocessing: {text_num_to_word_and_transliterated}")


    mel = text_to_mel.generate_mel(text_num_to_word_and_transliterated)
    audio, sr = mel_to_wav.generate_wav(mel)

    fName = f'temp_{count+1}_{random.randint(1000, 9999)}.wav'
    write(filename=fName, rate=sr, data=audio) # for saving wav file, if needed
    audio_file_path = os.path.abspath(fName)
    return audio_file_path




def translate_video(video_path,language_voice,gender_voice,output_path):
    df = get_captions(video_path)
    logger.info('*'*50)
    logger.info('Subtitles Generated')
    df['TEXT'] = df.apply(lambda row: convert_floats(row), axis=1)
    tgt_lang = flores_codes[language_voice.capitalize()]
    df2 = translate(df,tgt_lang=tgt_lang)
    logger.info('*'*50)
    logger.info('Subtitles Translated')
    logger.info(df2.head())

    language_voice= language_voice.lower()
    gender_voice = gender_voice.lower()

    # glow_model_dir=f'/home/shubhankar/Project/VAKYANSH_TTS/tts_infer/translit_models/{language_voice}/{gender_voice}/glow_ckp'
    # hifi_model_dir=f'/home/shubhankar/Project/VAKYANSH_TTS/tts_infer/translit_models/{language_voice}/{gender_voice}/hifi_ckp'
    
    vakyansh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'VAKYANSH_TTS'))
    glow_model_dir = os.path.join(vakyansh_path, 'tts_infer', 'translit_models', language_voice, gender_voice, 'glow_ckp')
    hifi_model_dir = os.path.join(vakyansh_path, 'tts_infer', 'translit_models', language_voice, gender_voice, 'hifi_ckp')

    logger.info('#'*50)
    logger.info(f"Lang: {language_voice}, Gender: {gender_voice}")
    logger.info(f"Glow: {glow_model_dir}")
    logger.info(f"HiFi: {hifi_model_dir}")
    logger.info('#'*50)

    global tts_model_cache
    
    model_key = f"{language_voice}_{gender_voice}"
    
    if model_key not in tts_model_cache:
        print(f"Loading TTS models for {model_key}...")
        if not os.path.exists(glow_model_dir) or not os.listdir(glow_model_dir):
            raise FileNotFoundError(f"Missing Glow model directory: {glow_model_dir}. Please download the models as per README.")
        if not os.path.exists(hifi_model_dir) or not os.listdir(hifi_model_dir):
            raise FileNotFoundError(f"Missing HiFi model directory: {hifi_model_dir}. Please download the models as per README.")

        global text_to_mel
        global mel_to_wav

        text_to_mel_instance = TextToMel(glow_model_dir=glow_model_dir, device=device)
        mel_to_wav_instance = MelToWav(hifi_model_dir=hifi_model_dir, device=device)
        tts_model_cache[model_key] = (text_to_mel_instance, mel_to_wav_instance)
    
    text_to_mel, mel_to_wav = tts_model_cache[model_key]




    try:
        for index, row in df2.iterrows():
        # get the translation and ID
            text = row['TRANSLATION']
            id = index
        # generate audio file using the TTS function and store the path in the "path" column
            path = run_tts(text, count=id )
            df.at[index, 'AUDIO'] = path
    except AssertionError:
        print('Oooooooooooooooooooooooooooooooooooooooooooops')


    wav_files = sorted([f for f in os.listdir('.') if f.startswith('temp_') and f.endswith('.wav')], key=lambda x: int(x.split('_')[1]))
    if wav_files:
        sox_command = ["sox"] + wav_files + ["output.wav"]
        subprocess.run(sox_command, check=True)

        ffmpeg_command = [
            "ffmpeg", "-y", "-i", video_path, "-i", "output.wav",
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", output_path
        ]
        subprocess.run(ffmpeg_command, check=True)

        for f in wav_files + ["output.wav"]:
            if os.path.exists(f):
                os.remove(f)






