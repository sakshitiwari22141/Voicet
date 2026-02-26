
import os
import time

import subprocess
import whisper
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import re
import torch
import functools
import inspect
import numpy as np
import wave
import random
import string
from scipy.io.wavfile import write
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fix for PyTorch 2.6+ weights_only issue
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

# Add Vakanysh path
vakyansh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'VAKYANSH_TTS'))
# Preference for model_storage if available (contains working checkpoints)
model_storage_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'model_storage'))

if os.path.exists(model_storage_path):
    vakyansh_models_base = model_storage_path
else:
    vakyansh_models_base = os.path.join(vakyansh_path, 'tts_infer', 'translit_models')

sys.path.append(vakyansh_path)

from tts_infer.tts import TextToMel, MelToWav
from tts_infer.transliterate import XlitEngine
from tts_infer.num_to_word_on_sent import normalize_nums

if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([np.core.multiarray.scalar])

# --- Global Configuration & Cache ---
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

_model_cache = {}

WHISPER_MODEL_NAME = 'base.en'
NLLB_CHECKPOINT = "facebook/nllb-200-distilled-600M"

# --- Lazy Loading Functions ---

def get_whisper_model():
    if 'whisper' not in _model_cache:
        start_time = time.time()
        logger.info(f"⏳ Loading Whisper model: {WHISPER_MODEL_NAME}...")
        _model_cache['whisper'] = whisper.load_model(WHISPER_MODEL_NAME, device=device)
        logger.info(f"✅ Whisper model loaded in {time.time() - start_time:.2f}s")
    return _model_cache['whisper']

def get_nllb_pipeline(src_lang, tgt_lang):
    # Cache key based on model name, not lang (pipeline can be reused if we just load model once)
    # Actually, pipeline is specific to task, but model/tokenizer are heavy.
    
    if 'nllb_model' not in _model_cache:
        start_time = time.time()
        logger.info(f"⏳ Loading NLLB model: {NLLB_CHECKPOINT}...")
        _model_cache['nllb_model'] = AutoModelForSeq2SeqLM.from_pretrained(NLLB_CHECKPOINT).to(device)
        _model_cache['nllb_tokenizer'] = AutoTokenizer.from_pretrained(NLLB_CHECKPOINT)
        logger.info(f"✅ NLLB model loaded in {time.time() - start_time:.2f}s")
    
    # We create a new pipeline for the specific language pair, but reuse the loaded model
    # Note: The original code created a pipeline every time. We can do the same but use the cached model.
    return pipeline("translation",
                    model=_model_cache['nllb_model'],
                    tokenizer=_model_cache['nllb_tokenizer'],
                    src_lang=src_lang,
                    tgt_lang=tgt_lang,
                    max_length=400,
                    device=0 if device == "cuda" else -1)

# --- Language Codes ---

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

# Mapping for Vakyansh XlitEngine (full name to short code)
FULL_TO_SHORT_LANG = {
    "hindi": "hi",
    "kannada": "kn",
    "tamil": "ta",
    "telugu": "te",
    "malayalam": "ml",
    "marathi": "mr",
    "gujarati": "gu",
    "bengali": "bn",
    "panjabi": "pa",
    "urdu": "ur",
    "english": "en"
}

# --- Language Helpers ---

def get_available_languages():
    """
    Scans vakyansh_models_base to find languages that have at least one usable checkpoint (.pth).
    Returns a list of full language names.
    """
    available = []
    # Using the same mapping keys we defined
    candidates = list(FULL_TO_SHORT_LANG.keys())
    
    for lang in candidates:
        # Check both genders for any usable glow model
        glow_female = os.path.join(vakyansh_models_base, lang, 'female', 'glow_ckp')
        glow_male = os.path.join(vakyansh_models_base, lang, 'male', 'glow_ckp')
        
        has_female = False
        if os.path.isdir(glow_female):
            if any(f.endswith('.pth') for f in os.listdir(glow_female)):
                has_female = True
                
        has_male = False
        if os.path.isdir(glow_male):
            if any(f.endswith('.pth') for f in os.listdir(glow_male)):
                has_male = True
        
        if has_female or has_male:
            available.append(lang.capitalize())
            
    return sorted(available)

transcribe_options = dict(
    beam_size=5, 
    best_of=5, 
    without_timestamps=False, 
    language='English', 
    fp16=False
)

def get_captions(file_path):
    # Lazy load mechanism
    asr_model = get_whisper_model()
    
    start_time = time.time()
    logger.info("🎙️ Starting transcription...")
    audio = whisper.load_audio(file_path)
    
    try:
        transcription = asr_model.transcribe(audio, **transcribe_options)
    except Exception as e:
        logger.warning(f"⚠️ High-quality transcription failed ({e}). Retrying with simpler settings...")
        fallback_options = transcribe_options.copy()
        fallback_options['beam_size'] = 1
        fallback_options['best_of'] = 1
        transcription = asr_model.transcribe(audio, **fallback_options)
    
    logger.info(f"📝 Transcription completed in {time.time() - start_time:.2f}s")
    
    rows = []
    for segment in transcription['segments']:
        rows.append({'START' : segment['start'], 'END' : segment['end'], 'TEXT' : segment['text'] })
    
    return pd.DataFrame(rows)

def convert_floats(row):
    pattern = r'\d+\.\d+'
    words = row['TEXT'].split()
    for i in range(len(words)):
        if words[i].endswith('.'):
            words[i] = words[i][:-1]
        try:
            float_val = float(words[i])
            words[i] = str(int(float_val)) + ' decimal ' + str(int(round (float_val % 1,2) * 10))
        except ValueError:
            pass
    return ' '.join(words)


def translate(df, src_lang="eng_Latn", tgt_lang="hin_Deva", max_batch_chars=400):
    start_time = time.time()
    logger.info(f"🌐 Translating to {tgt_lang}...")
    translation_pipeline = get_nllb_pipeline(src_lang, tgt_lang)

    output_column = []
    previous_context = ""
    
    for index, row in df.iterrows():
        current_text = row['TEXT'].strip()
        if not current_text:
            output_column.append("")
            continue
            
        try:
            if previous_context:
                full_input = f"{previous_context} {current_text}"
                result = translation_pipeline(full_input)
                if result and len(result) > 0:
                    translated_full = result[0]['translation_text']
                    output_value = translated_full
                    if '।' in translated_full:
                        output_value = translated_full.split('।')[-1].strip()
                    elif '.' in translated_full:
                         output_value = translated_full.split('.')[-1].strip()
                else:
                    output_value = current_text
            else:
                result = translation_pipeline(current_text)
                if result and len(result) > 0:
                    output_value = result[0]['translation_text']
                else:
                    output_value = current_text
        except Exception as e:
            logger.error(f"Translation error at index {index}: {e}")
            output_value = current_text
            
        output_column.append(output_value)
        previous_context = current_text
        
    logger.info(f"✨ Translation completed in {time.time() - start_time:.2f}s")
    df['TRANSLATION'] = output_column
    return df

# --- TTS & Transliteration ---

def translit(text, lang):
    reg = re.compile(r'[a-zA-Z]')
    # XlitEngine needs short codes (e.g., 'ta', 'te')
    short_lang = FULL_TO_SHORT_LANG.get(lang.lower(), lang)
    try:
        engine = XlitEngine(short_lang)
        words = [engine.translit_word(word, topk=1)[short_lang][0] if reg.match(word) else word for word in text.split()]
        updated_sent = ' '.join(words)
        return updated_sent
    except Exception as e:
        logger.warning(f"⚠️ Transliteration failed for {lang} ({e}). Returning original text.")
        return text

def run_tts(text, lang='hi', count=0):
    # Relies on global text_to_mel and mel_to_wav set in translate_video
    # This is legacy behavior preserved for now.
    
    logger.info(f"Original Text from user: {text}")
    if lang == 'hi':
        text = text.replace('।', '.') 
    text_num_to_word = normalize_nums(text, lang) 
    text_num_to_word_and_transliterated = translit(text_num_to_word, lang) 
    logger.info(f"Text after preprocessing: {text_num_to_word_and_transliterated}")

    mel = text_to_mel.generate_mel(text_num_to_word_and_transliterated)
    audio, sr = mel_to_wav.generate_wav(mel)

    fName = f'temp_{count+1}_{random.randint(1000, 9999)}.wav'
    write(filename=fName, rate=sr, data=audio)
    return os.path.abspath(fName)


# Global cache for TTS models
tts_model_cache = {}

# These must be global for run_tts to access them (legacy design)
text_to_mel = None
mel_to_wav = None

def translate_video(video_path, language_voice, gender_voice, output_path):
    df = get_captions(video_path)
    logger.info('Subtitles Generated')
    df['TEXT'] = df.apply(lambda row: convert_floats(row), axis=1)
    
    tgt_lang = flores_codes.get(language_voice.capitalize())
    if not tgt_lang:
        logger.error(f"Language code not found for {language_voice}")
        return

    df2 = translate(df, tgt_lang=tgt_lang)
    logger.info('Subtitles Translated')
    logger.info(df2.head())

    language_voice = language_voice.lower()
    gender_voice = gender_voice.lower()
    
    # Path construction for Vakyansh models
    glow_model_dir = os.path.join(vakyansh_models_base, language_voice, gender_voice, 'glow_ckp')
    hifi_model_dir = os.path.join(vakyansh_models_base, language_voice, gender_voice, 'hifi_ckp')

    logger.info('#'*50)
    logger.info(f"Lang: {language_voice}, Gender: {gender_voice}")
    logger.info(f"Glow: {glow_model_dir}")
    logger.info(f"HiFi: {hifi_model_dir}")
    logger.info('#'*50)

    global tts_model_cache
    global text_to_mel
    global mel_to_wav
    
    model_key = f"{language_voice}_{gender_voice}"
    
    if model_key not in tts_model_cache:
        logger.info(f"Loading TTS models for {model_key}...")
        if not os.path.exists(glow_model_dir) or not os.listdir(glow_model_dir):
            raise FileNotFoundError(f"Missing Glow model directory: {glow_model_dir}")
        if not os.path.exists(hifi_model_dir) or not os.listdir(hifi_model_dir):
            raise FileNotFoundError(f"Missing HiFi model directory: {hifi_model_dir}")

        start_time = time.time()
        text_to_mel_instance = TextToMel(glow_model_dir=glow_model_dir, device=device)
        mel_to_wav_instance = MelToWav(hifi_model_dir=hifi_model_dir, device=device)
        tts_model_cache[model_key] = (text_to_mel_instance, mel_to_wav_instance)
        logger.info(f"✅ TTS models loaded in {time.time() - start_time:.2f}s")
    
    text_to_mel, mel_to_wav = tts_model_cache[model_key]

    try:
        # Use simple iterrows for now
        for index, row in df2.iterrows():
            text = row['TRANSLATION']
            if not isinstance(text, str) or not text.strip():
                continue
            path = run_tts(text, lang=language_voice, count=index)
            df.at[index, 'AUDIO'] = path
            
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise e

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

