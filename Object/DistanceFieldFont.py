import os


class FontData:
    def __init__(self, language, font_data):
        self.language = language
        self.unicode_name = font_data['unicode_name'],
        self.unicode_range = font_data['unicode_range'],
        self.text_count = font_data['text_count'],
        self.font_size = font_data['font_size'],
        self.texture = font_data['texture']


class DistanceFieldFont:
    def __init__(self, name, font_datas):
        """
        :param font_datas:font_data in FontLoader.py
        """
        self.name = name
        self.font_datas = {}

        for language in font_datas:
            self.font_datas[language] = FontData(language, font_datas[language])

    def get_font_texture(self, language='ascii'):
        """
        :param language : FontLoader.language_infos
        """
        return self.font_datas[language].texture if language in self.font_datas else None


