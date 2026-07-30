
### 1. Data Flow & Pipeline Intermediate Results
Show how a video segment is processed at each layer.

#### Example: "Can I Stop You For 5 Sec?"

| Pipeline Stage | Component / Model | Data Type / Format | Sample Data |
| :--- | :--- | :--- | :--- |
| **Input Video** | User Upload / YouTube | Video File (`.mp4`) | `Can I Stop You For 5 Sec? #shorts.mp4` |
| **Audio Extraction**| `ffmpeg` | Audio File (`.wav`) | `16kHz, mono` raw audio stream |
| **Transcription** | Whisper (`base.en`) | Pandas DataFrame | `START: 0.00`, `END: 5.00`<br>**Text**: `"Can I stop you for 5 sec?"` |
| **Punctuation & Float Normalization** | Regex / Custom parser | Python String | `"Can I stop you for 5 decimal 0 seconds"` (or normalized text) |
| **Translation** | NLLB-200 (`600M`) | Python String | Target (Hindi): `"क्या मैं आपको 5 सेकंड के लिए रोक सकता हूँ?"` |
| **Text Normalization (TTS prep)** | `normalize_nums` / Transliteration | Python String | `"क्या मैं आपको पांच सेकंड के लिए रोक सकता हूँ?"` |
| **TTS Mel Generation** | Vakyansh `TextToMel` (Glow-TTS) | Tensor | Mel-spectrogram coefficients |
| **Audio Generation** | Vakyansh `MelToWav` (HiFi-GAN) | Audio Chunk (`.wav`) | `temp_1_4839.wav` (22.05kHz audio) |
| **Audio Concatenation** | `sox` | Audio File (`.wav`) | `output.wav` (Merged segments) |
| **Muxing / Final Export** | `ffmpeg` | Video File (`.mp4`) | `Can I Stop You For 5 Sec?_Hindi_Female.mp4` |

---

### 2. Sample Database Records
Show the schema and sample records from `db.sqlite`.

#### User Table Schema & Data
Stores user credentials (hashed passwords) and identities.
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(1000) UNIQUE NOT NULL
);
```
**Sample Data**:
| id | email | password | name |
| :--- | :--- | :--- | :--- |
| 1 | `chocolateboyz0011@gmail.com` | `scrypt:32768:8:1$...` | `Ujjawal` |

#### Videos Table Schema & Data
Tracks original uploads and target translation/dubbing jobs.
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    youtube_url VARCHAR(200),
    file_name VARCHAR(200),
    file_extension VARCHAR(10),
    file_path VARCHAR(200),
    original_filename VARCHAR(200),
    task_id VARCHAR(100),
    translate_to_languge VARCHAR(200),
    translate_to_gender VARCHAR(200),
    video_processed INTEGER DEFAULT 0,
    percent_processed INTEGER DEFAULT 0,
    date_posted DATETIME DEFAULT CURRENT_TIMESTAMP,
    posted_by VARCHAR(1000) FOREIGN KEY REFERENCES user(name)
);
```
**Sample Data**:
| id | original_filename | translate_to_languge | translate_to_gender | task_id | video_processed | posted_by |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `Can I Stop You For 5 Sec? #shorts.mp4` | *None (Original)* | *None* | *None* | 0 | `Ujjawal` |
| 2 | `Can I Stop You For 5 Sec? #shorts_Hindi_Female.mp4` | `hindi` | `Female` | `58b44f9d-e929-4384-b610-098b5ad862d1` | 0 | `Ujjawal` |

---

### 3. Model Configuration & Accuracy Log Data
Compare the defaults vs. optional high-performance models used for testing.

#### Model Parameters
- **Whisper**: `base.en` (Beam size: 5, Best of: 5, fp16: False)
- **NLLB-200**: `facebook/nllb-200-distilled-600M` (Default) vs `facebook/nllb-200-distilled-1.3B` / `3.3B` (For higher accuracy)
- **TTS**: Glow-TTS + HiFi-GAN (Vakyansh checkpoints for Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Bengali, Punjabi, Urdu)

#### Context Batching Results (From [ACCURACY_LOG.md](https://raw.githubusercontent.com/sakshitiwari22141/Voicet/refs/heads/main/docs/ACCURACY_LOG.md))
Show how context grouping improves output coherence:
*   **Without Batching**: Segment-by-segment translation maps phrases directly without context, causing tense/gender mismatch.
*   **With Batching (implemented)**: Merges text segments up to 400 characters, passing larger contextual blocks to NLLB-200.

---

### 4. UI Assets
- Include the UI landing page screenshot from the project root: 

![Voicet-Homepage](https://github.com/sakshitiwari22141/Voicet/blob/main/Voicet-Homepage.png?raw=true).