from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


class IntroTextGenerator():
    width = 0
    height = 0
    draw = NotImplemented
    img = NotImplemented
    title_font = ImageFont.truetype('fonts/NeoSansStd-Bold.otf', size=50)
    title_font_color = (21, 45, 76, 255)
    course_font = ImageFont.truetype('fonts/NeoSansStd-Regular.otf', size=30)
    course_font_color = (255, 255, 255, 255)

    def __init__(self, resolution):
        if resolution == '2160':
            self.width = 3840
            self.height = 2160
        elif resolution == '1080':
            self.width = 1920
            self.height = 1080
        elif resolution == '720':
            self.width = 1280
            self.height = 720
        elif resolution == '480':
            self.width = 640
            self.height = 480

        self.img = Image.new(mode='RGBA', size=(self.width, self.height), color=(255, 255, 255, 0))
        self.draw = ImageDraw.Draw(self.img)

    def draw_title_text(self, title):
        w, h = self.draw.textsize(title, font=self.title_font)
        self.draw.text(((self.width - w) / 2, (self.height - h) / 2), title, self.title_font_color, font=self.title_font)

    def draw_course_text(self, course):
        w, h = self.draw.textsize(course, font=self.course_font)
        self.draw.text(((self.width - w) / 2, (self.height - h) / 2 + 485), course, self.course_font_color, font=self.course_font)

    def save_image(self, fn):
        self.img.save(fn, 'PNG')


if __name__ == '__main__':
    tg = IntroTextGenerator('1080')
    tg.draw_title_text('Title text her')
    tg.draw_course_text('01005 Matematik 1 - E18/F19')
    tg.save_image('test1.png')


ffmpeg_command = 'ffmpeg -i video.mp4 -i image.png -filter_complex "[0:v][1:v] overlay=0:0:enable=" -c:a copy output.mp4'

