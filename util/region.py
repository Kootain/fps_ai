# coding=utf-8

class Rect(object):
    pass


class Box(object):
    def __init__(self, topx, topy, botx, boty):
        self.topx = topx
        self.topy = topy
        self.botx = botx
        self.boty = boty

    def rect(self):
        return Rect(x=self.topx, y=self.topy, width=self.botx-self.topx, height=self.boty-self.topy)

    def tuple(self):
        return self.topx, self.topy, self.botx, self.boty

    def __repr__(self):
        return f'({self.topx},{self.topy},{self.botx},{self.boty})'


class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def box(self):
        return Box(topx=self.x, topy=self.y, botx=self.x+self.width, boty=self.y+self.height)

    def tuple(self):
        return self.x, self.y, self.width, self.height

    def __repr__(self):
        return f'({self.x},{self.y},{self.width},{self.height})'


screen_width, screen_height = 2560, 1440
grab_width, grab_height = 640, 640
center_box = Box(int(screen_width / 2 - grab_width / 2), int(screen_height / 2 - grab_height / 2), int(screen_width / 2 + grab_width / 2), int(screen_height / 2 + grab_height / 2))


if __name__ == '__main__':
    box = Box(1, 1, 5, 5)
    print(box.rect())
