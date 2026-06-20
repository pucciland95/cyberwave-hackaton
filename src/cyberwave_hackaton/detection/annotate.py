'''
Annotation tool for YOLO format.
Saves .txt annotation files AND images with bounding boxes drawn on them.

Keys:
  Draw box   → click and drag with left mouse button
  n          → confirm current box + class
  c          → switch class
  s          → save annotations + annotated image, move to next image
  q          → quit without saving
'''

import os
import cv2
import fonts

current_directory = os.path.dirname(os.path.abspath(__file__))
image_folder = os.path.join(current_directory, "Images")
label_folder = os.path.join(current_directory, "Dataset", "labels")
annotated_folder = os.path.join(current_directory, "Dataset", "annotated_images")
untouched_folder = os.path.join(current_directory, "Dataset", "images")
os.makedirs(label_folder, exist_ok=True)
os.makedirs(annotated_folder, exist_ok=True)
os.makedirs(untouched_folder, exist_ok=True)
classes_ids = ["cube_hackaton"]

drawing = False
ix, iy = -1, -1
rectangles, classes, rectangles_save = [], [], []
current_class = 0
img = None


def draw_rectangle(event, x, y, flags, params):
    global ix, iy, drawing, rectangles, current_class

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_copy = img.copy()
            cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)
            cv2.putText(img_copy, f"Class: {classes_ids[current_class]}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Image", img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        rectangles.append((ix, iy, x, y))
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
        cv2.imshow("Image", img)


def save_annotations(image_filename, rectangles_save, classes):
    h, w, _ = img.shape
    basename = os.path.splitext(os.path.basename(image_filename))[0]

    # Save .txt YOLO labels
    label_filename = os.path.join(label_folder, basename + '.txt')
    with open(label_filename, 'w') as f:
        for (x1, y1, x2, y2), class_id in zip(rectangles_save, classes):
            x_center = (x1 + x2) / 2 / w
            y_center = (y1 + y2) / 2 / h
            width = abs(x2 - x1) / w
            height = abs(y2 - y1) / h
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

    # Save annotated image with bounding boxes
    annotated_img = img.copy()
    for (x1, y1, x2, y2), class_id in zip(rectangles_save, classes):
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated_img, classes_ids[class_id],
                    (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    annotated_path = os.path.join(annotated_folder, basename + '_annotated.jpg')
    cv2.imwrite(annotated_path, annotated_img)
    untouched_path = os.path.join(untouched_folder, basename + '.jpg')
    cv2.imwrite(untouched_path, img)

    print(f"{fonts.green}Saved labels → {label_filename}{fonts.reset}")
    print(f"{fonts.green}Saved image  → {annotated_path}{fonts.reset}")


def annotate_images():
    global img, rectangles, classes, current_class, rectangles_save

    image_files = [os.path.join(root, file)
                   for root, _, files in os.walk(image_folder)
                   for file in files if file.lower().endswith(('.jpg', '.png', '.jpeg'))]

    if not image_files:
        print(f"{fonts.red}No images found in {image_folder}{fonts.reset}")
        return

    print(f"{fonts.green}Found {len(image_files)} images.{fonts.reset}")

    for image_filename in image_files:
        img = cv2.imread(image_filename)
        img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_LINEAR)

        cv2.imshow("Image", img)
        cv2.setMouseCallback("Image", draw_rectangle)

        rectangles, rectangles_save, classes = [], [], []

        print(f"\n{fonts.red}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{fonts.reset}")
        print(f"{fonts.red}Image: {os.path.basename(image_filename)}{fonts.reset}")
        print(f"{fonts.green}  Draw box  → click and drag{fonts.reset}")
        print(f"{fonts.green}  n         → confirm box{fonts.reset}")
        print(f"{fonts.green}  c         → switch class{fonts.reset}")
        print(f"{fonts.green}  s         → save and next image{fonts.reset}")
        print(f"{fonts.green}  q         → quit{fonts.reset}")
        print(f"{fonts.red}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{fonts.reset}")

        while True:
            img_with_text = img.copy()
            cv2.putText(img_with_text, f"Class: {classes_ids[current_class]} | boxes: {len(rectangles_save)}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img_with_text, "n=confirm  c=class  s=save&next  q=quit",
                        (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.imshow("Image", img_with_text)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('c'):
                current_class = (current_class + 1) % len(classes_ids)
                print(f"{fonts.purple}Switched to class: {classes_ids[current_class]}{fonts.reset}")

            elif key == ord('n'):
                if len(rectangles) > 0:
                    classes.append(current_class)
                    rectangles_save.append(rectangles[-1])
                    (x1, y1, x2, y2) = rectangles[-1]
                    print(f"{fonts.purple}Confirmed box #{len(rectangles_save)}: {rectangles[-1]} | class: {classes_ids[current_class]}{fonts.reset}")
                else:
                    print(f"{fonts.red}No box drawn yet — draw a box first.{fonts.reset}")

            elif key == ord('s'):
                if len(rectangles_save) > 0:
                    save_annotations(image_filename, rectangles_save, classes)
                else:
                    print(f"{fonts.red}No confirmed boxes to save. Draw a box and press 'n' first.{fonts.reset}")
                break

            elif key == ord('q'):
                print(f"{fonts.red}Quit.{fonts.reset}")
                cv2.destroyAllWindows()
                return

        cv2.destroyAllWindows()


if __name__ == '__main__':
    annotate_images()