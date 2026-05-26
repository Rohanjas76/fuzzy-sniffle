"""
label_faces.py
==============
Run this tool to label faces in a group photo.
It detects all faces, shows them one by one, you type the name,
and it saves each cropped face into the database/ folder.

Usage:
    python label_faces.py path/to/group_photo.jpg
"""

import sys
import os
import cv2
import face_recognition
import numpy as np
from pathlib import Path

DATABASE_FOLDER = 'database'

def label_faces(image_path):
    print(f"\n{'='*50}")
    print("  Face Labeling Tool")
    print(f"{'='*50}\n")

    # Load image
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        print(f"[ERROR] Cannot open image: {image_path}")
        sys.exit(1)

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    print(f"Detecting faces in {Path(image_path).name}...")
    face_locations = face_recognition.face_locations(image_rgb, model='hog')

    if not face_locations:
        print("[ERROR] No faces detected in this image.")
        sys.exit(1)

    print(f"Found {len(face_locations)} face(s).\n")

    saved = 0

    for i, (top, right, bottom, left) in enumerate(face_locations):
        # Add padding around the face crop
        pad = 30
        h, w = image_bgr.shape[:2]
        t = max(0, top - pad)
        b = min(h, bottom + pad)
        l = max(0, left - pad)
        r = min(w, right + pad)

        # Crop the face
        face_crop = image_bgr[t:b, l:r]

        # Show the full image with this face highlighted
        display = image_bgr.copy()
        cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 120), 3)
        cv2.putText(display, f"Face #{i+1}", (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 120), 2)

        # Scale down for display if too large
        dh, dw = display.shape[:2]
        max_dim = 900
        if max(dh, dw) > max_dim:
            scale = max_dim / max(dh, dw)
            display = cv2.resize(display, (int(dw*scale), int(dh*scale)))

        cv2.imshow(f"Label Face #{i+1} of {len(face_locations)} — press any key", display)
        cv2.waitKey(1)

        # Show cropped face too
        face_show = cv2.resize(face_crop, (200, 200)) if face_crop.size > 0 else face_crop
        cv2.imshow("Cropped Face", face_show)
        cv2.waitKey(1)

        print(f"Face #{i+1} of {len(face_locations)}")
        name = input("  Enter name (or press Enter to skip): ").strip()

        cv2.destroyAllWindows()

        if not name:
            print("  Skipped.\n")
            continue

        # Clean name for folder
        folder_name = name.strip()
        person_dir  = Path(DATABASE_FOLDER) / folder_name
        person_dir.mkdir(parents=True, exist_ok=True)

        # Count existing photos
        existing = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
        photo_num = len(existing) + 1
        save_path = person_dir / f"photo{photo_num}.jpg"

        cv2.imwrite(str(save_path), face_crop)
        print(f"  ✓ Saved as: {save_path}\n")
        saved += 1

    cv2.destroyAllWindows()
    print(f"{'='*50}")
    print(f"  Done! {saved} face(s) saved to database/")
    print(f"  Now run: python build_database.py")
    print(f"{'='*50}\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python label_faces.py path/to/group_photo.jpg")
        print("Example: python label_faces.py group.jpg")
        sys.exit(1)
    label_faces(sys.argv[1])
