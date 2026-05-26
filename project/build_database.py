"""
build_database.py
=================
Run this ONCE after adding new photos to the database folder.
It encodes all faces and saves them to face_cache.pkl.

Usage:
    python build_database.py

The Flask app then loads face_cache.pkl instantly on startup.
You never need to run this again unless you add new people.
"""

import os
import pickle
import numpy as np
import face_recognition
from pathlib import Path

DATABASE_FOLDER = 'database'
CACHE_FILE      = 'face_cache.pkl'
ALLOWED         = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

known_encodings = []
known_names     = []
known_paths     = []

db_path = Path(DATABASE_FOLDER)

print("=" * 50)
print("  Face Database Builder")
print("=" * 50)

total_people = 0
total_photos = 0

for person_dir in sorted(db_path.iterdir()):
    if not person_dir.is_dir():
        continue

    name = person_dir.name.replace('_', ' ').replace('-', ' ').title()
    person_encodings = []
    person_img_paths = []

    print(f"\n[{name}]")

    for img_path in sorted(person_dir.iterdir()):
        if img_path.suffix.lower().lstrip('.') not in ALLOWED:
            continue
        try:
            print(f"  encoding {img_path.name}...", end=' ', flush=True)
            image = face_recognition.load_image_file(str(img_path))
            encs  = face_recognition.face_encodings(image)
            if encs:
                person_encodings.append(encs[0])
                person_img_paths.append(str(img_path))
                total_photos += 1
                print("✓")
            else:
                print("✗ no face found")
        except Exception as e:
            print(f"✗ error: {e}")

    if person_encodings:
        avg_encoding = np.mean(person_encodings, axis=0)
        distances    = [np.linalg.norm(enc - avg_encoding) for enc in person_encodings]
        best_path    = person_img_paths[int(np.argmin(distances))]
        known_encodings.append(avg_encoding)
        known_names.append(name)
        known_paths.append(best_path)
        total_people += 1
        print(f"  → averaged {len(person_encodings)} photos")

# Also handle flat files
for img_path in sorted(db_path.iterdir()):
    if not img_path.is_file():
        continue
    if img_path.suffix.lower().lstrip('.') not in ALLOWED:
        continue
    name = img_path.stem.replace('_', ' ').replace('-', ' ').title()
    print(f"\n[{name}] (flat file)")
    print(f"  encoding {img_path.name}...", end=' ', flush=True)
    try:
        image = face_recognition.load_image_file(str(img_path))
        encs  = face_recognition.face_encodings(image)
        if encs:
            known_encodings.append(encs[0])
            known_names.append(name)
            known_paths.append(str(img_path))
            total_people += 1
            total_photos += 1
            print("✓")
        else:
            print("✗ no face found")
    except Exception as e:
        print(f"✗ error: {e}")

# Save cache
with open(CACHE_FILE, 'wb') as f:
    pickle.dump({
        'encodings': known_encodings,
        'names':     known_names,
        'paths':     known_paths,
    }, f)

print("\n" + "=" * 50)
print(f"  Done! {total_people} people, {total_photos} photos encoded.")
print(f"  Saved to {CACHE_FILE}")
print("  Now run: python app.py")
print("=" * 50)
