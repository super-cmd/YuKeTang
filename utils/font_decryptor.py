# utils/font_decryptor.py
import requests
from io import BytesIO
from fontTools.ttLib import TTFont
import json
import hashlib
import re
from bs4 import BeautifulSoup

class FontDecryptor:
    """
    雨课堂混淆字体解密工具类
    """

    def __init__(self, headers=None):
        self.headers = headers or {}

    @staticmethod
    def hash_glyph_commands(commands):
        command_str = json.dumps(commands, sort_keys=True)
        return hashlib.sha1(command_str.encode()).hexdigest()

    def decrypt_font(self, font_url, mapping_file="mapping_file.json"):
        """下载字体并生成映射"""
        res = requests.get(font_url, headers=self.headers)
        font_data = BytesIO(res.content)
        obf_font = TTFont(font_data)

        cmap = obf_font.getBestCmap()
        glyph_unicodes = {}
        for code, name in cmap.items():
            glyph_unicodes.setdefault(name, []).append(code)

        with open(mapping_file, "r", encoding="utf-8") as f:
            original_glyph_to_uni = json.load(f)

        obf_to_orig = {}
        for glyph_name in obf_font.getGlyphOrder():
            unicodes = glyph_unicodes.get(glyph_name, [])
            if not unicodes:
                continue
            unicode_t = unicodes[0]

            glyph = obf_font["glyf"][glyph_name]
            commands = []

            if glyph.numberOfContours > 0:
                commands = [
                    f"CONTOUR_END:{glyph.endPtsOfContours}",
                    f"COORDS:{glyph.coordinates}"
                ]
            elif glyph.isComposite():
                components = [f"{c.glyphName}({c.x},{c.y})" for c in glyph.components]
                commands = ["COMPOSITE"] + components

            glyph_hash = self.hash_glyph_commands(commands)

            if glyph_hash in original_glyph_to_uni:
                obf_to_orig[unicode_t] = original_glyph_to_uni[glyph_hash]

        return obf_to_orig

    def decrypt_text(self, text, font_url=None, mapping=None):
        if mapping is None:
            mapping = self.decrypt_font(font_url) if font_url else {}
        return "".join(chr(mapping.get(ord(c), ord(c))) for c in text)

    def decrypt_html(self, html_text, font_url=None, mapping=None):
        """
        解析 HTML 中加密字体 <span class="xuetangx-com-encrypted-font">...</span>
        如果提供 mapping，则直接使用，不再下载字体
        """
        if mapping is None:
            mapping = self.decrypt_font(font_url) if font_url else {}

        def replace_span(match):
            enc_text = match.group(1)
            return "".join(chr(mapping.get(ord(c), ord(c))) for c in enc_text)

        decrypted_html = re.sub(
            r'<span class="xuetangx-com-encrypted-font">(.*?)</span>',
            replace_span,
            html_text
        )

        soup = BeautifulSoup(decrypted_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
