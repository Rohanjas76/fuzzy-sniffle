# Face Recognition System

import os, uuid, pickle, base64
import numpy as np
import cv2
import face_recognition
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER']     = 'static/uploads'
app.config['RESULTS_FOLDER']    = 'static/results'
app.config['MAX_CONTENT_LENGTH']= 16 * 1024 * 1024
CACHE_FILE = 'face_cache.pkl'
ALLOWED    = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

# ── Load cache once at startup ──
def load_cache():
    if not os.path.exists(CACHE_FILE):
        print("[ERROR] face_cache.pkl not found — run: python build_database.py")
        return [], [], []
    with open(CACHE_FILE, 'rb') as f:
        c = pickle.load(f)
    print(f"[OK] Loaded {len(c['names'])} identity/identities from cache instantly.")
    return c['encodings'], c['names'], c['paths']

DB_ENC, DB_NAMES, DB_PATHS = [], [], []

def allowed_file(fn):
    return '.' in fn and fn.rsplit('.', 1)[1].lower() in ALLOWED

def encode_image_to_base64(path):
    with open(path, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    ext  = Path(path).suffix.lstrip('.').lower()
    mime = 'jpeg' if ext in ('jpg','jpeg') else ext
    return f"data:image/{mime};base64,{data}"

def recognize_face(uploaded_path):
    image_bgr = cv2.imread(uploaded_path)
    if image_bgr is None:
        return {'error': 'Cannot read image file'}

    image_rgb      = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(image_rgb, model='hog')
    face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

    if not face_locations:
        return {'error': 'No face detected in the uploaded image.'}

    landmarks_list = face_recognition.face_landmarks(image_rgb, [face_locations[0]])
    landmarks      = landmarks_list[0] if landmarks_list else {}
    result_image   = image_bgr.copy()
    results        = []

    for i, (face_loc, face_enc) in enumerate(zip(face_locations, face_encodings)):
        top, right, bottom, left = face_loc

        if not DB_ENC:
            results.append({'face_index':i,'name':'Unknown Person','confidence':0.0,
                            'matched':False,'db_image':None,'location':face_loc})
            cv2.rectangle(result_image,(left,top),(right,bottom),(0,0,255),3)
            continue

        face_distances = face_recognition.face_distance(DB_ENC, face_enc)
        best_idx       = int(np.argmin(face_distances))
        best_distance  = float(face_distances[best_idx])
        THRESHOLD      = 0.60
        confidence     = max(0.0, round((1.0 - best_distance) * 100 * 1.15, 2))
        matched        = best_distance <= THRESHOLD

        if matched:
            name    = DB_NAMES[best_idx]
            db_path = DB_PATHS[best_idx]
            color   = (0, 255, 120)
        else:
            name      = 'Unknown Person'
            db_path   = None
            color     = (0, 80, 255)
            confidence = min(confidence, 35.0)

        cv2.rectangle(result_image,(left,top),(right,bottom),color,3)
        lbt = top - 35 if top > 40 else bottom + 5
        cv2.rectangle(result_image,(left,lbt),(right,lbt+30),color,cv2.FILLED)
        cv2.putText(result_image,f"{name} {confidence:.1f}%",(left+6,lbt+22),
                    cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,0,0),2)

        lm_colors = {'chin':(255,200,0),'left_eyebrow':(0,255,255),
                     'right_eyebrow':(0,255,255),'nose_bridge':(255,100,200),
                     'nose_tip':(255,100,200),'left_eye':(0,200,255),
                     'right_eye':(0,200,255),'top_lip':(100,255,100),
                     'bottom_lip':(100,255,100)}
        for feature, pts in landmarks.items():
            for pt in pts:
                cv2.circle(result_image, pt, 2, lm_colors.get(feature,(255,255,255)), -1)

        results.append({'face_index':i,'name':name,'confidence':round(confidence,2),
                        'matched':matched,'distance':round(best_distance,4),
                        'db_image':db_path,'location':face_loc})

    result_path = os.path.join(app.config['RESULTS_FOLDER'], f"r_{uuid.uuid4().hex[:8]}.jpg")
    cv2.imwrite(result_path, result_image)
    try: os.remove(uploaded_path)
    except: pass

    primary      = results[0] if results else {}
    db_image_b64 = None
    if primary.get('db_image'):
        try:
            # Show the cropped face from the database image
            db_img = cv2.imread(primary['db_image'])
            if db_img is not None:
                db_locs = face_recognition.face_locations(
                    cv2.cvtColor(db_img, cv2.COLOR_BGR2RGB), model='hog')
                if db_locs:
                    t, r, b, l = db_locs[0]
                    pad = 30
                    dh, dw = db_img.shape[:2]
                    crop = db_img[max(0,t-pad):min(dh,b+pad),
                                  max(0,l-pad):min(dw,r+pad)]
                    tmp = 'static/results/_tmp_db.jpg'
                    cv2.imwrite(tmp, crop)
                    db_image_b64 = encode_image_to_base64(tmp)
                    try: os.remove(tmp)
                    except: pass
                else:
                    db_image_b64 = encode_image_to_base64(primary['db_image'])
            else:
                db_image_b64 = encode_image_to_base64(primary['db_image'])
        except: pass

    result_b64 = encode_image_to_base64(result_path)
    try: os.remove(result_path)
    except: pass

    return {
        'faces_detected':   len(results),
        'primary': {'name':       primary.get('name','Unknown'),
                    'confidence': primary.get('confidence',0),
                    'matched':    primary.get('matched',False),
                    'distance':   primary.get('distance',1.0)},
        'all_faces':         [{k:v for k,v in r.items() if k!='location'} for r in results],
        'result_image':      result_b64,
        'db_image':          db_image_b64,
        'known_faces_count': len(DB_NAMES),
        'landmark_count':    sum(len(v) for v in landmarks.values()),
    }

@app.route('/')
def index():
    return render_template('index.html', db_count=len(DB_NAMES))

@app.route('/recognize', methods=['POST'])
def recognize():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    file = request.files['image']
    if not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    filename    = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    result = recognize_face(upload_path)
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)

@app.route('/db-stats')
def db_stats():
    return jsonify({'count': len(DB_NAMES), 'names': DB_NAMES})

if __name__ == '__main__':
    for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
    DB_ENC[:], DB_NAMES[:], DB_PATHS[:] = load_cache()
    app.run(debug=False, host='127.0.0.1', port=8731)
