# coding:utf-8

import io
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ops_sia.cache import Backend
from ops_sia.options import get_options

options = get_options()


class CodeAuth(object):
    def __init__(self,
                 font_path="/usr/share/fonts/monaco/Monaco.ttf",
                 number=options.code_auth_len,
                 size=(100, 30),
                 bgcolor=(255, 255, 255),
                 fontcolor=(0, 0, 255),
                 linecolor=(255, 0, 0),
                 draw_line=True,
                 line_number=(1, 5)
                 ):
        self.font_path = font_path
        self.number = number
        self.size = size
        self.bgcolor = bgcolor
        self.fontcolor = fontcolor
        self.linecolor = linecolor
        self.draw_line = draw_line
        self.line_number = line_number
        self.cache = Backend()

    # 用来随机生成一个字符串
    def gene_text(self):
        source = list(string.letters)
        for index in range(0, 10):
            source.append(str(index))
        return ''.join(random.sample(source, self.number))

    # 用来绘制干扰线
    def gene_line(self, draw, width, height):
        begin = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([begin, end], fill=self.linecolor)

    # 生成验证码
    def gene_code(self):
        width, height = self.size
        image = Image.new('RGBA', (width, height), self.bgcolor)
        font = ImageFont.truetype(self.font_path, 25)
        draw = ImageDraw.Draw(image)
        text = self.gene_text()
        font_width, font_height = font.getsize(text)
        draw.text(((width - font_width) / self.number, (height - font_height) / self.number), text,
                  font=font, fill=self.fontcolor)
        if self.draw_line:
            self.gene_line(draw, width, height)
        # 创建扭曲
        # image = image.transform((width+30,height+10), Image.AFFINE, (1,-0.3,0,-0.1,1,0),Image.BILINEAR)
        image = image.transform((width + 20, height + 10), Image.AFFINE, (1, -0.3, 0, -0.1, 1, 0),
                                Image.BILINEAR)
        image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

        imgio = io.BytesIO()
        image.save(imgio, "GIF")
        return imgio.getvalue(), text
        # image.save('idencode.png') #保存验证码图片

    def check_auth_code(self, auth_code, session_id):
        result = self.cache.conn.get(session_id)
        if not result:
            return False
        elif auth_code.lower() != result.lower():
            return False
        # 验证成功之后删除
        self.cache.conn.delete(session_id)
        return True

#
#
# class CodeAuth(object):
#     def __init__(self,
#                  size=(120, 30),
#                  img_type="GIF",
#                  mode="RGB",
#                  bg_color=(255, 255, 255),
#                  fg_color=(0, 0, 255),
#                  font_size=18,
#                  font_type="Monaco.ttf",
#                  # length=options.code_auth_len,
#                  length=4,
#                  draw_lines=True,
#                  n_line=(1, 2),
#                  draw_points=True,
#                  point_chance=2
#                  ):
#         # 小写字母，去除可能干扰的i，l，o，z
#         self._letter_cases = "abcdefghjkmnpqrstuvwxy"
#         # 大写字母
#         self._upper_cases = self._letter_cases.upper()
#         # 数字
#         self._numbers = ''.join(map(str, range(3, 10)))
#         self.chars = ''.join((self._letter_cases, self._upper_cases, self._numbers))
#         self.size = size
#         self.img_type = img_type
#         self.mode = mode
#         self.bg_color = bg_color
#         self.fg_color = fg_color
#         self.font_size = font_size
#         self.font_type = font_type
#         self.length = length
#         self.draw_lines = draw_lines
#         self.n_line = n_line
#         self.draw_points = draw_points
#         self.point_chance = point_chance
#         self.width, self.height = size
#         self.img = Image.new(self.mode, self.size, self.bg_color)
#         self.draw = ImageDraw.Draw(self.img)
#         if self.draw_lines:
#             self.create_lines()
#         if draw_points:
#             self.create_points()
#         self.cache = Backend()
#         """
#         @todo: 生成验证码图片
#         @param size: 图片的大小，格式（宽，高），默认为(120, 30)
#         @param chars: 允许的字符集合，格式字符串
#         @param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
#         @param mode: 图片模式，默认为RGB
#         @param bg_color: 背景颜色，默认为白色
#         @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
#         @param font_size: 验证码字体大小
#         @param font_type: 验证码字体，默认为 ae_AlArabiya.ttf
#         @param length: 验证码字符个数
#         @param draw_lines: 是否划干扰线
#         @param n_lines: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
#         @param draw_points: 是否画干扰点
#         @param point_chance: 干扰点出现的概率，大小范围[0, 100]
#         @param width: 宽
#         @param height: 高
#         @param img: 创建图形
#         @param
#         @return: [0]: PIL Image实例
#         @return: [1]: 验证码图片中的字符串
#         """
#
#     @property
#     def get_chars(self):
#         """生成给定长度的字符串，返回列表格式"""
#         return random.sample(self.chars, self.length)
#
#     def create_lines(self):
#         """绘制干扰线数"""
#         line_num = random.randint(*self.n_line)
#
#         for i in range(line_num):
#             # 起始点
#             begin = (random.randint(0, self.size[0]), random.randint(0, self.size[1]))
#             # 结束点
#             end = (random.randint(0, self.size[0]), random.randint(0, self.size[1]))
#             self.draw.line([begin, end], fill=(0, 0, 0))
#
#     def create_points(self):
#         """绘制干扰点"""
#         # 大小限制在[0, 100]
#         chance = min(100, max(0, int(self.point_chance)))
#
#         for w in range(self.width):
#             for h in range(self.height):
#                 tmp = random.randint(0, 100)
#                 if tmp > 100 - chance:
#                     self.draw.point((w, h), fill=(0, 0, 0))
#
#     @property
#     def create_strs(self):
#         """绘制验证码字符"""
#         c_chars = self.get_chars
#         # 每个字符前后以空格隔开
#         strs = ' %s ' % ' '.join(c_chars)
#
#         font = ImageFont.truetype(self.font_type, self.font_size)
#         font_width, font_height = font.getsize(strs)
#
#         self.draw.text(((self.width - font_width) / 3, (self.height - font_height) / 3),
#                     strs, font=font, fill=self.fg_color)
#
#         return ''.join(c_chars)
#
#     @property
#     def auth_img_code(self):
#         # 图形扭曲参数
#         params = [1 - float(random.randint(1, 2)) / 100,
#                   0,
#                   0,
#                   0,
#                   1 - float(random.randint(1, 10)) / 100,
#                   float(random.randint(1, 2)) / 500,
#                   0.001,
#                   float(random.randint(1, 2)) / 500
#                   ]
#         # 创建扭曲
#         img = self.img.transform(self.size, Image.PERSPECTIVE, params)
#
#         # 滤镜，边界加强（阈值更大）
#         img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
#         imgio = io.BytesIO()
#         img.save(imgio, "GIF")
#         return imgio.getvalue(), self.create_strs
#         # return img, strs
#
#     def check_auth_code(self, auth_code, session_id):
#         result = self.cache.conn.get(session_id)
#         if not result:
#             return False
#         elif auth_code != result:
#             return False
#         return True
