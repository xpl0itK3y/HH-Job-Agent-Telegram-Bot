from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.utils.vacancy_tag import build_vacancy_tag

CARD_WIDTH = 1200
CARD_HEIGHT = 720
CARD_STORAGE_DIR = Path("storage/cards")
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


class VacancyCardService:
    def render_png(
        self,
        *,
        vacancy: dict,
        vacancy_tag: str | None = None,
    ) -> Path:
        CARD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        vacancy_tag = vacancy_tag or build_vacancy_tag(vacancy_id=vacancy.get("id"))
        output_path = CARD_STORAGE_DIR / f"{vacancy_tag.lstrip('#').lower()}.png"

        image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (12, 18, 31))
        draw = ImageDraw.Draw(image)
        accent = (66, 218, 163)
        light = (235, 244, 255)
        muted = (138, 155, 179)

        self._draw_background(draw, accent)

        title_font = ImageFont.truetype(MONO_BOLD, 48)
        company_font = ImageFont.truetype(MONO_BOLD, 28)
        body_font = ImageFont.truetype(MONO_REG, 24)
        small_font = ImageFont.truetype(MONO_BOLD, 20)

        draw.rounded_rectangle((36, 36, CARD_WIDTH - 36, CARD_HEIGHT - 36), radius=28, outline=accent, width=3)
        draw.rectangle((36, 36, 52, CARD_HEIGHT - 36), fill=accent)

        draw.text((90, 70), vacancy_tag, fill=accent, font=small_font)
        draw.text((90, 122), vacancy.get("title") or "Untitled vacancy", fill=light, font=title_font)
        draw.text((90, 188), vacancy.get("company_name") or "Unknown company", fill=accent, font=company_font)

        salary = self._format_salary(vacancy)
        meta_lines = [
            f"Salary: {salary}",
            f"Location: {vacancy.get('area_name') or 'Not specified'}",
            f"Format: {vacancy.get('work_format') or 'Not specified'}",
            f"Experience: {vacancy.get('experience') or 'Not specified'}",
            f"Provider: {vacancy.get('provider') or '-'} / {vacancy.get('source_country_code') or '-'}",
        ]
        y = 260
        for line in meta_lines:
            draw.text((90, y), line, fill=muted, font=body_font)
            y += 38

        draw.text((90, 470), "Tech stack", fill=light, font=small_font)
        x = 90
        for skill in (vacancy.get("key_skills_json") or [])[:5]:
            x = self._draw_tag(draw, x, 510, skill, accent, body_font)

        summary_title_y = 590
        draw.text((90, summary_title_y), "Summary", fill=light, font=small_font)
        summary = vacancy.get("description_ai_summary") or vacancy.get("description_clean") or "No summary"
        wrapped_summary = self._wrap_text(summary, line_length=64)[:3]
        line_y = summary_title_y + 38
        for line in wrapped_summary:
            draw.text((90, line_y), line, fill=muted, font=body_font)
            line_y += 32

        image.save(output_path, format="PNG")
        return output_path

    def _draw_background(self, draw: ImageDraw.ImageDraw, accent: tuple[int, int, int]) -> None:
        for y in range(CARD_HEIGHT):
            ratio = y / CARD_HEIGHT
            color = (
                int(12 + (24 - 12) * ratio),
                int(18 + (30 - 18) * ratio),
                int(31 + (58 - 31) * ratio),
            )
            draw.line((0, y, CARD_WIDTH, y), fill=color)

        for x in range(0, CARD_WIDTH, 30):
            for y in range(0, CARD_HEIGHT, 30):
                draw.rectangle((x, y, x + 2, y + 2), fill=(accent[0] // 6, accent[1] // 6, accent[2] // 6))

    def _draw_tag(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        accent: tuple[int, int, int],
        font: ImageFont.FreeTypeFont,
    ) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = (bbox[2] - bbox[0]) + 28
        draw.rounded_rectangle((x, y, x + width, y + 40), radius=12, outline=accent, width=2)
        draw.text((x + 14, y + 7), text, fill=(235, 244, 255), font=font)
        return x + width + 12

    def _format_salary(self, vacancy: dict) -> str:
        salary_from = vacancy.get("salary_from")
        salary_to = vacancy.get("salary_to")
        currency = vacancy.get("salary_currency") or ""
        if salary_from is None and salary_to is None:
            return "Not specified"
        return f"{salary_from or '?'} - {salary_to or '?'} {currency}".strip()

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
