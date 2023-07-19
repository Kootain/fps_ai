# coding=utf8

def filter_target(results, targets=None):
    r = results[0]
    boxes = r.boxes
    names = r.names
    new_boxes = []
    if boxes is not None:
        for d in reversed(boxes):
            cls = names[int(d.cls.squeeze())]
            if cls in targets:
                new_boxes.append(d)
    r.boxes = new_boxes
