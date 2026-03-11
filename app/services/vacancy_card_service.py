import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.utils.vacancy_tag import build_vacancy_tag

FONT_PATHS = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    ],
}
CARD_STORAGE_DIR = Path("storage/cards")
W = 1200
H = 760
PAD = 36
MARGIN = 52
PS = 3
TAG_W = 190
TAG_H = 58


class VacancyCardService:
    def render_gif(self, *, vacancy: dict, vacancy_tag: str | None = None) -> Path:
        CARD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        vacancy_tag = vacancy_tag or build_vacancy_tag(vacancy_id=vacancy.get("id"))
        output_path = CARD_STORAGE_DIR / f"{vacancy_tag.lstrip('#').lower()}.gif"

        prepared = {
            "company": (vacancy.get("company_name") or "UNKNOWN")[:12].upper(),
            "position": vacancy.get("title") or "Untitled vacancy",
            "salary": self._format_salary(vacancy),
            "format": self._format_location(vacancy),
            "tags": (vacancy.get("key_skills_json") or ["General"])[:3],
            "badge": self._build_badge(vacancy),
            "vacancy_tag": vacancy_tag,
            "summary": vacancy.get("description_ai_summary") or vacancy.get("description_clean") or "No summary",
        }

        accent = self._random_accent((vacancy.get("id") or 0) + len(prepared["position"]))
        frames = [
            self._render_frame(prepared, frame_idx, accent, rng_seed=frame_idx * 31 + 17)
            for frame_idx in range(42)
        ]
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            loop=0,
            duration=60,
            optimize=False,
        )
        return output_path

    def _render_frame(
        self,
        vacancy: dict,
        frame_idx: int,
        accent: tuple[int, int, int],
        rng_seed: int,
    ) -> Image.Image:
        rng = random.Random(rng_seed)
        dark = (10, 12, 22)
        mid = (18, 22, 44)

        img = Image.new("RGBA", (W, H), dark)
        draw = ImageDraw.Draw(img)

        for y in range(H):
            draw.rectangle([0, y, W, y], fill=self._lerp_col(dark, mid, y / H))

        grid_color = tuple(max(0, int(c * 0.06)) for c in accent)
        self._px_grid(draw, grid_color)

        cx, cy = PAD, PAD
        cw, ch = W - PAD * 2, H - PAD * 2
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, cw - 1, ch - 1], fill=(16, 18, 36, 245))

        for t in range(PS):
            col = tuple(int(c * (0.25 + 0.75 * (t == 0))) for c in accent) + (255,)
            cd.rectangle([t, t, cw - 1 - t, ch - 1 - t], outline=col)

        cd.rectangle([0, 0, PS * 3, ch - 1], fill=accent + (255,))
        img.paste(card, (cx, cy), card)
        draw = ImageDraw.Draw(img)
        ox = cx + PS * 3 + MARGIN
        card_right = cx + cw

        row_title = cy + 42
        row_company = row_title + 82
        row_divider = row_company + 80
        row_sal_lbl = row_divider + 28
        row_sal_val = row_sal_lbl + 38
        row_loc_lbl = row_sal_val + 88
        row_loc_val = row_loc_lbl + 38
        row_bar = row_loc_val + 64
        row_stk_lbl = row_bar + 38
        row_tags = row_stk_lbl + 42
        row_summary = row_tags + 96
        row_status = cy + ch - 58

        blink_fast = (frame_idx // 4) % 2 == 0
        blink_slow = (frame_idx // 10) % 2 == 0
        blink_cur = (frame_idx // 6) % 2 == 0

        f_title = self._fnt(52, bold=True)
        title_ox = ox + (rng.randint(-3, 3) if rng.random() < 0.15 else 0)
        draw.text((title_ox, row_title), vacancy["position"], fill=(255, 255, 255), font=f_title)
        if blink_cur:
            tb = f_title.getbbox(vacancy["position"])
            draw.rectangle([ox + tb[2] + 6, row_title + 2, ox + tb[2] + 14, row_title + 50], fill=accent)

        f_company = self._fnt(34, bold=True)
        pill_bg = tuple(max(0, min(255, int(c * 0.22))) for c in accent)
        self._px_rect(draw, ox, row_company, TAG_W, TAG_H, pill_bg)
        self._px_border(draw, ox, row_company, TAG_W, TAG_H, accent, 4)
        self._draw_centered_text(draw, ox, row_company, TAG_W, TAG_H, vacancy["company"], f_company)

        self._px_dashed_line(draw, ox, card_right - 24, row_divider, tuple(int(c * 0.45) for c in accent))

        f_label = self._fnt(21, bold=True)
        f_salary = self._fnt(42, bold=True)
        lbl_col = (200, 212, 235) if blink_slow else (160, 175, 200)
        draw.text((ox, row_sal_lbl), "[ SALARY ]", fill=lbl_col, font=f_label)
        draw.text((ox, row_sal_val), vacancy["salary"], fill=accent, font=f_salary)

        f_info = self._fnt(28, bold=True)
        draw.text((ox, row_loc_lbl), "[ LOCATION ]", fill=lbl_col, font=f_label)
        draw.text((ox, row_loc_val), vacancy["format"], fill=accent, font=f_info)

        bar_val = 0.72 + 0.04 * math.sin(frame_idx * 0.15)
        self._px_health_bar(draw, ox, row_bar, 260, bar_val, accent)

        draw.text((ox, row_stk_lbl), "[ TECH STACK ]", fill=lbl_col, font=f_label)
        tx = ox
        f_tag = self._fnt(26, bold=True)
        for i, tag in enumerate(vacancy["tags"]):
            tag_acc = accent if (frame_idx + i * 7) % 20 > 2 else (255, 255, 255)
            tx += self._px_tag(draw, tx, row_tags, tag, tag_acc, f_tag)

        f_summary = self._fnt(18)
        draw.text((ox, row_summary), "[ SUMMARY ]", fill=lbl_col, font=f_label)
        for idx, line in enumerate(self._wrap_text(vacancy["summary"], 68)[:3]):
            draw.text((ox, row_summary + 34 + idx * 28), line, fill=(190, 202, 222), font=f_summary)

        f_badge = self._fnt(24, bold=True)
        badge_bbox = f_badge.getbbox(vacancy["badge"])
        badge_w = badge_bbox[2] + 44
        badge_x = card_right - badge_w - 8
        badge_acc = accent if blink_fast else tuple(min(255, c + 60) for c in accent)
        self._px_badge(draw, vacancy["badge"], badge_acc, f_badge, badge_x, cy + 30)

        draw.text((card_right - 220, row_status), vacancy["vacancy_tag"], fill=accent, font=self._fnt(20, bold=True))
        dot_col = (0, 255, 100) if blink_fast else (0, 100, 50)
        draw.rectangle([ox, row_status + 4, ox + 16, row_status + 20], fill=dot_col)
        draw.text((ox + 26, row_status + 1), "READY", fill=(210, 220, 240), font=self._fnt(23, bold=True))

        img_rgb = img.convert("RGB")
        if (frame_idx % 12) in (0, 1):
            self._apply_noise_lines(ImageDraw.Draw(img_rgb), rng, accent, intensity=1.0)
            img_rgb = self._apply_glitch(img_rgb, rng, intensity=1.0)
        self._apply_pixel_noise(img_rgb, rng, density=0.0015, acc=accent)
        return img_rgb

    def _random_accent(self, seed: int) -> tuple[int, int, int]:
        rng = random.Random(seed)
        return rng.choice(
            [
                (255, 60, 100),
                (0, 230, 140),
                (255, 200, 0),
                (80, 160, 255),
                (255, 120, 0),
                (40, 200, 255),
            ]
        )

    def _fnt(self, size: int, *, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        variant = "bold" if bold else "regular"
        for font_path in FONT_PATHS[variant]:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _lerp_col(self, c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def _px_rect(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        draw.rectangle([x, y, x + w - 1, y + h - 1], fill=color)

    def _px_border(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int],
        thickness: int = PS,
    ) -> None:
        draw.rectangle([x, y, x + w - 1, y + thickness - 1], fill=color)
        draw.rectangle([x, y + h - thickness, x + w - 1, y + h - 1], fill=color)
        draw.rectangle([x, y, x + thickness - 1, y + h - 1], fill=color)
        draw.rectangle([x + w - thickness, y, x + w - 1, y + h - 1], fill=color)

    def _px_dashed_line(self, draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, color: tuple[int, int, int], dash: int = 16, gap: int = 8) -> None:
        x, on = x0, True
        while x < x1:
            end = min(x + (dash if on else gap), x1)
            if on:
                draw.rectangle([x, y, end, y + 3], fill=color)
            x, on = end, not on

    def _px_grid(self, draw: ImageDraw.ImageDraw, color: tuple[int, int, int], step: int = 26) -> None:
        for x in range(0, W, step):
            for y in range(0, H, step):
                draw.rectangle([x, y, x + 2, y + 2], fill=color)

    def _px_health_bar(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, val: float, accent: tuple[int, int, int]) -> None:
        segs = 16
        seg_w = (w - segs) // segs
        for i in range(segs):
            sx = x + i * (seg_w + 1)
            color = accent if i < int(segs * val) else tuple(max(0, v - 140) for v in accent)
            self._px_rect(draw, sx, y, seg_w, 12, color)

    def _px_tag(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, accent: tuple[int, int, int], font: ImageFont.FreeTypeFont) -> int:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (TAG_W - tw) // 2 - bbox[0]
        ty = y + (TAG_H - th) // 2 - bbox[1]
        bg = tuple(max(0, min(255, int(c * 0.13))) for c in accent)
        self._px_rect(draw, x, y, TAG_W, TAG_H, bg)
        self._px_border(draw, x, y, TAG_W, TAG_H, accent, 4)
        draw.text((tx, ty), text, fill=(255, 255, 255), font=font)
        return TAG_W + 14

    def _px_badge(self, draw: ImageDraw.ImageDraw, text: str, accent: tuple[int, int, int], font: ImageFont.FreeTypeFont, bx: int, by: int) -> None:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        px_p, py_p = 20, 10
        w, h = tw + px_p * 2, th + py_p * 2
        self._px_rect(draw, bx, by, w, h, accent)
        dark_acc = tuple(max(0, c - 80) for c in accent)
        self._px_border(draw, bx, by, w, h, dark_acc, PS)
        draw.text((bx + px_p - bbox[0], by + py_p - bbox[1]), text, fill=(8, 8, 18), font=font)

    def _apply_glitch(self, img: Image.Image, rng: random.Random, intensity: float = 1.0) -> Image.Image:
        pixels = img.load()
        glitch_lines = rng.randint(2, int(6 * intensity))
        for _ in range(glitch_lines):
            y = rng.randint(0, H - 1)
            shift = rng.randint(-int(30 * intensity), int(30 * intensity))
            row = [pixels[x, y] for x in range(W)]
            for x in range(W):
                src = (x - shift) % W
                pixels[x, y] = row[src]
        return img

    def _apply_noise_lines(self, draw: ImageDraw.ImageDraw, rng: random.Random, acc: tuple[int, int, int], intensity: float = 1.0) -> None:
        n = rng.randint(1, int(4 * intensity))
        for _ in range(n):
            y = rng.randint(0, H - 1)
            h_line = rng.randint(1, 3)
            alpha = rng.randint(60, 160)
            color = tuple(min(255, int(cc * 0.4 + alpha)) for cc in acc)
            draw.rectangle([0, y, W, y + h_line], fill=color)

    def _apply_pixel_noise(self, img: Image.Image, rng: random.Random, density: float, acc: tuple[int, int, int]) -> None:
        draw = ImageDraw.Draw(img)
        count = int(W * H * density)
        for _ in range(count):
            x = rng.randint(0, W - 1)
            y = rng.randint(0, H - 1)
            bright = rng.randint(100, 255)
            color = tuple(min(255, int(cc * 0.3 + bright * 0.7)) for cc in acc)
            draw.rectangle([x, y, x + 1, y + 1], fill=color)

    def _draw_centered_text(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, text: str, font: ImageFont.FreeTypeFont) -> None:
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (w - tw) // 2 - bbox[0]
        ty = y + (h - th) // 2 - bbox[1]
        draw.text((tx, ty), text, fill=(255, 255, 255), font=font)

    def _format_salary(self, vacancy: dict) -> str:
        salary_from = vacancy.get("salary_from")
        salary_to = vacancy.get("salary_to")
        currency = vacancy.get("salary_currency") or ""
        if salary_from is None and salary_to is None:
            return "Not specified"
        return f"{salary_from or '?'} - {salary_to or '?'} {currency}".strip()

    def _format_location(self, vacancy: dict) -> str:
        work_format = vacancy.get("work_format") or "Not specified"
        area_name = vacancy.get("area_name") or "Unknown area"
        return f"{work_format}  /  {area_name}"

    def _build_badge(self, vacancy: dict) -> str:
        if vacancy.get("salary_to"):
            return "HOT"
        if vacancy.get("source_country_code") == "RU":
            return "NEW"
        return "TOP"

    def _wrap_text(self, text: str, line_length: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            candidate = " ".join(current + [word])
            if len(candidate) <= line_length:
                current.append(word)
                continue
            if current:
                lines.append(" ".join(current))
            current = [word]
        if current:
            lines.append(" ".join(current))
        return lines
