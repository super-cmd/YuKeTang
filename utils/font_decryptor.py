# font_decryptor.py
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

    def decrypt_text(self, text, font_url):
        mapping = self.decrypt_font(font_url)
        return "".join(chr(mapping.get(ord(c), ord(c))) for c in text)

    def decrypt_html(self, html_text, font_url):
        """
        直接解析 HTML 中的 <span class="xuetangx-com-encrypted-font">...</span>
        并返回纯文本
        """
        mapping = self.decrypt_font(font_url)

        def replace_span(match):
            enc_text = match.group(1)
            return "".join(chr(mapping.get(ord(c), ord(c))) for c in enc_text)

        # 替换所有加密 span
        decrypted_html = re.sub(
            r'<span class="xuetangx-com-encrypted-font">(.*?)</span>',
            replace_span,
            html_text
        )

        # 使用 BeautifulSoup 去掉剩余 HTML 标签
        soup = BeautifulSoup(decrypted_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)


if __name__ == "__main__":
    font_url = "https://fe-static-yuketang.yuketang.cn/fe_font/product/exam_font_71fcafe41b694a9985b6d3b8717e8bce.ttf"
    obf_text = "坏是剂头径费湿干促什标职验"
    html_text = '<p><span class="xuetangx-com-encrypted-font">坏是剂头径费湿干促什标职验</span>。</p><p></p><!--!doctype-->'

    decryptor = FontDecryptor()
    print("=== 解密纯文本 ===")
    print(decryptor.decrypt_text(obf_text, font_url))

    print("\n=== 解密 HTML ===")
    print(decryptor.decrypt_html(html_text, font_url))
