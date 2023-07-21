# coding=utf-8

from ultralytics import YOLO
from ultralytics.engine.results import Results
from typing import List
import cv2

model = YOLO('yolov8n.pt')
pose_model = YOLO('yolov8n-pose.pt')  #


def detect(img) -> List[Results]:
    return model(img)


def detect_pose(img) -> List[Results]:
    return pose_model(img)


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


if __name__ == '__main__':
    from vision.eye import frame
    from util.region import center_box

    video_path = "2.mp4"
    cap = cv2.VideoCapture(video_path)

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()
        frame = frame[center_box.topy:center_box.boty, center_box.topx:center_box.botx]

        if success:
            # Run YOLOv8 inference on the frame
            results = detect_pose(frame)

            # Visualize the results on the frame
            annotated_frame = results[0].plot()

            # Display the annotated frame
            cv2.imshow("YOLOv8 Inference", annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()

