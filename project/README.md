# Face Recognition System

### Data Science Project by Jashwanth Namachivayam

A locally-running face recognition web application built with Python, Flask, OpenCV and the face_recognition library. Upload any image to identify a person from a local face database with confidence scoring and facial landmark detection.

---

## Features

- Upload any photo to identify a person
- Compares against a local face database
- Shows confidence score and facial landmarks
- Supports group photos with multiple faces
- Modern dark UI with glassmorphism design
- 100% offline — no internet required

---

## Project Structure

```
face-recognition-system/
├── app.py                  # Flask backend
├── build_database.py       # Run once to encode database
├── label_faces.py          # Label faces from a group photo
├── requirements.txt        # Python dependencies
├── START.bat               # Windows double-click launcher
│
├── database/               # Add face photos here
│   └── Person Name/
│       ├── photo1.jpg
│       ├── photo2.jpg
│       └── photo3.jpg
│
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       └── particles.js
│
└── templates/
    └── index.html
```

---

## Setup & Installation

### Requirements
- Python 3.9, 3.10 or 3.11
- CMake (for dlib)

### Step 1 — Install CMake
- **Windows:** Download from https://cmake.org/download and check "Add to PATH"
- **Mac:** `brew install cmake`
- **Linux:** `sudo apt-get install cmake build-essential`

### Step 2 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/face-recognition-system.git
cd face-recognition-system
```

### Step 3 — Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate.bat

# Mac/Linux
source venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install dlib-bin
pip install face-recognition --no-deps
pip install flask opencv-python numpy werkzeug pillow face-recognition-models
```

### Step 5 — Add faces to database
Create a folder inside `database/` named after the person and add their photos:
```
database/
└── John Doe/
    ├── photo1.jpg
    ├── photo2.jpg
    └── photo3.jpg
```

### Step 6 — Build the database
```bash
python build_database.py
```
This runs once and saves encodings to `face_cache.pkl`.

### Step 7 — Run the app
```bash
python app.py
```
Open your browser at **http://127.0.0.1:5000**

---

## How It Works

| Step | Concept | Description |
|---|---|---|
| 1 | Data Collection | Scans database/ folder for known faces |
| 2 | Preprocessing | Converts images to RGB, normalises |
| 3 | Face Detection | HOG-based detector locates faces |
| 4 | Feature Extraction | 68-point facial landmark detection |
| 5 | Face Encoding | ResNet-34 → 128-dimensional embedding |
| 6 | Pattern Matching | Euclidean distance comparison |
| 7 | Prediction | Threshold + confidence score output |

---

## Labeling Faces from a Group Photo

```bash
python label_faces.py group.jpg
```
Detects all faces, shows each one, you type the name — automatically saves cropped faces to the database.

---

## Tech Stack

- **Backend:** Python, Flask
- **Face Recognition:** face_recognition, dlib
- **Image Processing:** OpenCV, NumPy
- **Frontend:** HTML, CSS, JavaScript
