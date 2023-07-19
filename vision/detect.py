# coding=utf-8

from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')


def detect(img):
    results = model(img)
    return results


def print_results(img, results):
    r = results[0]
    boxes = r.boxes
    names = r.names
    if boxes is not None:
        for d in reversed(boxes):
            cls = names[int(d.cls.squeeze())]
            conf = int(d.conf.squeeze() * 100)
            x1, y1, x2, y2 = (int(x) for x in d.xyxy.squeeze())
            cv2.putText(img, f'{cls} {conf}%', (x1 + 100, y1 + 100), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 2)
            cv2.rectangle(img, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=4)


