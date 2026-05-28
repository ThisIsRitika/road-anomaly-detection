import cv2
import os
import albumentations as A

# =========================
# PATHS
# =========================
image_dir = "images/train/images"
label_dir = "images/train/labels"

output_img_dir = "images/train/images_aug"
output_lbl_dir = "images/train/labels_aug"

os.makedirs(output_img_dir, exist_ok=True)
os.makedirs(output_lbl_dir, exist_ok=True)

# =========================
# DARK IMAGE FILTER
# =========================
def is_too_dark(image, threshold=40):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray.mean() < threshold

# =========================
# AUGMENTATION PIPELINE (FIXED)
# =========================
transform = A.Compose(
    [
        A.RandomBrightnessContrast(
            brightness_limit=(-0.3, -0.1),
            contrast_limit=(-0.2, 0.1),
            p=0.8,
        ),
        A.RandomGamma(gamma_limit=(70, 120), p=0.7),
        A.GaussNoise(p=0.4),
        A.MotionBlur(blur_limit=5, p=0.3),
    ],
    bbox_params=A.BboxParams(
        format="yolo",
        label_fields=["class_labels"],
        min_visibility=0.3,
    ),
)

# =========================
# PROCESS LOOP
# =========================
count = 0
skipped_dark = 0

for img_file in os.listdir(image_dir):
    print(f"Processing: {img_file}")

    # Skip non-images
    if not img_file.lower().endswith((".jpg", ".png", ".jpeg")):
        continue

    # Skip already augmented inputs
    if img_file.startswith("aug_"):
        continue

    img_path = os.path.join(image_dir, img_file)
    label_path = os.path.join(label_dir, img_file.rsplit(".", 1)[0] + ".txt")

    new_img_name = "aug_" + img_file
    output_img_path = os.path.join(output_img_dir, new_img_name)
    output_lbl_path = os.path.join(
        output_lbl_dir, new_img_name.rsplit(".", 1)[0] + ".txt"
    )

    # Skip if already exists
    if os.path.exists(output_img_path):
        print(f"⏭️ Skipping existing: {new_img_name}")
        continue

    image = cv2.imread(img_path)

    if image is None:
        print(f"❌ Could not read: {img_file}")
        continue

    # =========================
    # READ LABELS
    # =========================
    bboxes = []
    class_labels = []

    if os.path.exists(label_path):
        with open(label_path, "r") as f:
            for line in f.readlines():
                parts = line.strip().split()

                if len(parts) != 5:
                    continue

                try:
                    cls, x, y, w, h = map(float, parts)

                    # Clamp values
                    x = max(0.0, min(1.0, x))
                    y = max(0.0, min(1.0, y))
                    w = max(0.0, min(1.0, w))
                    h = max(0.0, min(1.0, h))

                    if w <= 0 or h <= 0:
                        continue

                    bboxes.append([x, y, w, h])
                    class_labels.append(int(cls))

                except:
                    continue

    if len(bboxes) == 0:
        print(f"⚠️ No objects in {img_file}, augmenting anyway")

    # =========================
    # AUGMENT
    # =========================
    try:
        augmented = transform(
            image=image,
            bboxes=bboxes,
            class_labels=class_labels,
        )
    except Exception as e:
        print(f"❌ Augmentation failed: {img_file}")
        continue

    aug_img = augmented["image"]
    aug_bboxes = augmented["bboxes"]
    aug_labels = augmented["class_labels"]

    # =========================
    # DARK FILTER (IMPORTANT)
    # =========================
    if is_too_dark(aug_img):
        print(f"🌑 Too dark, skipping: {new_img_name}")
        skipped_dark += 1
        continue

    # =========================
    # SAVE IMAGE
    # =========================
    cv2.imwrite(output_img_path, aug_img)

    # =========================
    # SAVE LABEL
    # =========================
    with open(output_lbl_path, "w") as f:
        for bbox, cls in zip(aug_bboxes, aug_labels):
            x, y, w, h = bbox
            f.write(f"{cls} {x} {y} {w} {h}\n")

    count += 1

# =========================
# DONE
# =========================
print("\n=========================")
print(f"✅ Done!")
print(f"✔ Images created: {count}")
print(f"🌑 Dark images skipped: {skipped_dark}")
print("=========================")