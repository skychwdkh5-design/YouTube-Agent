"""Labels as float-positioned sprites (no integer text placement, so they fade/move without stepping)."""
from PIL import Image, ImageDraw, ImageFont
import engine as E
from engine import W, H, Sprite, mat, compose, draw
FI = "/usr/share/fonts/opentype/inter/"
F_TAG = ImageFont.truetype(FI + "Inter-SemiBold.otf", 22)
INK, OCHRE = (244, 238, 226), (232, 176, 84)
ILL_TXT = "ILLUSTRATION / NOT TO SCALE"
C_EO1 = "NASA EO-1 ALI · May 2, 2011 · NASA Earth Observatory"
_cache = {}

def tag(text, bg=(10, 18, 34, 170), fg=INK, font=F_TAG):
    key = (text, bg, fg)
    if key not in _cache:
        d = ImageDraw.Draw(Image.new("RGBA", (4, 4))); l, t, r, b = d.textbbox((0, 0), text, font=font)
        w, h = r - l + 28, b - t + 18; im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
        dd.rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], 12, fill=bg)
        dd.text((14 * 2 - l * 2, 9 * 2 - t * 2), text, font=ImageFont.truetype(font.path, font.size * 2), fill=fg + (255,))
        _cache[key] = Sprite(im)
    return _cache[key]

def put_tag(c, text, x, y, right=False, a=1.0, bg=(10, 18, 34, 170)):
    if a <= 0.004: return
    s = tag(text, bg=bg); k = 0.5
    px = x - s.w * k if right else x
    draw(c, s, mat(px, y, 0, k, k, 0, 0), alpha=a)


F = lambda name, size: ImageFont.truetype(FI + name, size)
F_HOOK, F_MID, F_DATE = F("Inter-Black.otf", 112), F("Inter-ExtraBold.otf", 40), F("Inter-Bold.otf", 46)
_wc = {}

def textlen(text, font):
    return ImageDraw.Draw(Image.new("RGBA", (4, 4))).textlength(text, font=font)

def word(text, font, color):
    """Word with soft drop shadow as a 2x-supersampled sprite (draw with scale 0.5)."""
    key = (text, font.size, color)
    if key not in _wc:
        f2 = ImageFont.truetype(font.path, font.size * 2); w = int(textlen(text, f2)) + 80; h = int(font.size * 2 * 1.6) + 40
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((30, 26), text, font=f2, fill=(0, 0, 0, 150))
        from PIL import ImageFilter
        sh = sh.filter(ImageFilter.GaussianBlur(10)); fg = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(fg).text((26, 18), text, font=f2, fill=color + (255,))
        sh.alpha_composite(fg); _wc[key] = Sprite(sh)
    return _wc[key]
