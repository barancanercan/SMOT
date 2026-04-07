"""
Professional PDF Report Generator for Intelligence Reports
Modular design with separate sections for clean layout
"""
import re
from datetime import datetime

from fpdf import FPDF


class DarkPDF(FPDF):
    """FPDF with automatic dark background on every page"""

    def __init__(self):
        super().__init__()
        self.is_cover = True  # First page is cover

    def header(self):
        """Called automatically on every new page"""
        # Draw dark background
        self.set_fill_color(11, 11, 11)
        self.rect(0, 0, 210, 297, 'F')

        # Skip header bar on cover page
        if self.is_cover:
            return

        # Header bar
        self.set_fill_color(26, 26, 26)
        self.rect(0, 0, 210, 12, 'F')
        self.set_fill_color(77, 163, 255)
        self.rect(0, 12, 210, 1, 'F')

        self.set_xy(0, 2)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(156, 163, 175)
        self.cell(210, 8, 'SMOT - SOSYAL MEDYA GOZLEM ARACI', align='C')

    def footer(self):
        """Called automatically on every page"""
        if self.is_cover:
            return

        self.set_y(-12)
        self.set_fill_color(26, 26, 26)
        self.rect(0, self.get_y() - 2, 210, 14, 'F')
        self.set_font('Helvetica', '', 7)
        self.set_text_color(107, 114, 128)
        self.cell(0, 10, f'Sayfa {self.page_no() - 1}', align='C')


class IntelligencePDFGenerator:
    """
    Professional Intelligence Report PDF Generator
    Dark theme with blue/teal accents
    """

    # Color Palette
    COLORS = {
        'bg_dark': (11, 11, 11),
        'bg_card': (26, 26, 26),
        'bg_card_alt': (20, 20, 22),
        'primary': (77, 163, 255),
        'secondary': (0, 209, 178),
        'accent': (99, 102, 241),
        'success': (16, 185, 129),
        'warning': (245, 158, 11),
        'danger': (239, 68, 68),
        'text_white': (255, 255, 255),
        'text_light': (229, 231, 235),
        'text_muted': (156, 163, 175),
        'text_dim': (107, 114, 128),
        'border': (55, 65, 81),
    }

    def __init__(self):
        self.pdf = DarkPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.set_margins(15, 15, 15)

    def generate(self, username: str, name: str, party: str,
                 district: str, content: str) -> bytes:
        """Generate complete PDF report"""

        # Parse markdown content into sections
        sections = self._parse_content(content)

        # Cover page
        self._add_cover_page(username, name, party, district)

        # Content pages
        self._add_content_pages(sections)

        # Disclaimer
        self._add_disclaimer_page()

        return self.pdf.output()

    def _safe_text(self, text: str) -> str:
        """Convert all special characters to ASCII"""
        replacements = {
            # Turkish
            'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
            'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
            # Quotes
            ''': "'", ''': "'", '"': '"',
            '‚': ',', '„': '"',
            # Dashes
            '–': '-', '—': '-', '‐': '-', '−': '-',
            # Other
            '…': '...', '•': '*', '·': '*', '°': 'o',
            '×': 'x', '÷': '/', '→': '->', '←': '<-',
            '©': '(c)', '®': '(R)', '™': '(TM)',
            '€': 'EUR', '£': 'GBP',
            '\u200b': '', '\u00a0': ' ', '\ufeff': '',
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Remove remaining non-ASCII
        return ''.join(c if ord(c) < 256 else '?' for c in text)

    def _set_color(self, color_name: str, fill: bool = False):
        """Set draw/fill/text color by name"""
        c = self.COLORS.get(color_name, self.COLORS['text_light'])
        if fill:
            self.pdf.set_fill_color(*c)
        else:
            self.pdf.set_text_color(*c)

    def _draw_page_bg(self):
        """Draw dark background for current page"""
        self.pdf.set_fill_color(*self.COLORS['bg_dark'])
        self.pdf.rect(0, 0, 210, 297, 'F')

    def _parse_content(self, content: str) -> list[dict]:
        """Parse markdown into structured sections"""
        sections = []
        current_section = {'type': 'text', 'title': '', 'items': []}

        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Main headers
            if line.startswith('# '):
                if current_section['items']:
                    sections.append(current_section)
                current_section = {
                    'type': 'h1',
                    'title': line[2:],
                    'items': []
                }
            elif line.startswith('## '):
                if current_section['items'] or current_section['title']:
                    sections.append(current_section)
                current_section = {
                    'type': 'h2',
                    'title': line[3:],
                    'items': []
                }
            elif line.startswith('### '):
                current_section['items'].append({
                    'type': 'h3',
                    'text': line[4:]
                })
            elif line.startswith('#### '):
                current_section['items'].append({
                    'type': 'h4',
                    'text': line[5:]
                })
            elif line.startswith('> '):
                current_section['items'].append({
                    'type': 'quote',
                    'text': line[2:]
                })
            elif line.startswith('- ') or line.startswith('* '):
                current_section['items'].append({
                    'type': 'bullet',
                    'text': line[2:]
                })
            elif re.match(r'^\d+\.', line):
                text = re.sub(r'^\d+\.\s*', '', line)
                current_section['items'].append({
                    'type': 'numbered',
                    'text': text
                })
            elif '|' in line and not line.startswith('|--'):
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if cells and not all('-' in c and len(c) > 2 for c in cells):
                    current_section['items'].append({
                        'type': 'table_row',
                        'cells': cells
                    })
            elif line.startswith('---') or line.startswith('***'):
                current_section['items'].append({'type': 'hr'})
            elif '**' in line:
                current_section['items'].append({
                    'type': 'bold_text',
                    'text': line
                })
            else:
                current_section['items'].append({
                    'type': 'text',
                    'text': line
                })

        if current_section['items'] or current_section['title']:
            sections.append(current_section)

        return sections

    def _add_cover_page(self, username: str, name: str, party: str, district: str):
        """Generate professional cover page"""
        self.pdf.is_cover = True
        self.pdf.add_page()

        # Left accent bar
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(0, 0, 6, 297, 'F')

        # Top line
        self.pdf.set_fill_color(*self.COLORS['secondary'])
        self.pdf.rect(6, 40, 198, 2, 'F')

        # Classification badge
        self.pdf.set_fill_color(*self.COLORS['danger'])
        self.pdf.rect(140, 15, 55, 14, 'F')
        self.pdf.set_font('Helvetica', 'B', 10)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.set_xy(140, 17)
        self.pdf.cell(55, 10, 'RESTRICTED', align='C')

        # Title
        self.pdf.set_xy(20, 55)
        self.pdf.set_font('Helvetica', 'B', 32)
        self._set_color('text_white')
        self.pdf.cell(0, 15, 'ISTIHBARAT')
        self.pdf.set_xy(20, 72)
        self.pdf.cell(0, 15, 'RAPORU')

        # Subtitle
        self.pdf.set_xy(20, 95)
        self.pdf.set_font('Helvetica', '', 11)
        self._set_color('text_muted')
        self.pdf.cell(0, 8, 'AI-Powered Social Media Intelligence Analysis')

        # Subject card
        self._draw_info_card(20, 120, 170, 70, [
            ('SUBJECT', self._safe_text(name), 'text_white', 14),
            ('HANDLE', f'@{username}', 'primary', 12),
            ('PARTY', self._safe_text(party), 'secondary', 12),
            ('DISTRICT', self._safe_text(district or 'Bilinmiyor'), 'text_light', 11),
        ])

        # Date
        self.pdf.set_xy(20, 200)
        self.pdf.set_font('Helvetica', '', 10)
        self._set_color('text_dim')
        self.pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}')

        # Bottom decoration
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(20, 260, 50, 2, 'F')
        self.pdf.set_fill_color(*self.COLORS['secondary'])
        self.pdf.rect(75, 260, 50, 2, 'F')

        # Footer
        self.pdf.set_xy(20, 270)
        self.pdf.set_font('Helvetica', '', 8)
        self._set_color('text_dim')
        self.pdf.cell(0, 5, 'SMOT v3.1 | Powered by OpenAI GPT')

    def _draw_info_card(self, x: float, y: float, w: float, h: float,
                        items: list[tuple]):
        """Draw info card with label-value pairs"""
        self.pdf.set_fill_color(*self.COLORS['bg_card'])
        self.pdf.rect(x, y, w, h, 'F')

        # Left accent
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(x, y, 4, h, 'F')

        current_y = y + 8
        for label, value, color, size in items:
            self.pdf.set_xy(x + 12, current_y)
            self.pdf.set_font('Helvetica', '', 9)
            self._set_color('text_dim')
            self.pdf.cell(35, 6, label + ':')

            self.pdf.set_font('Helvetica', 'B', size)
            self._set_color(color)
            self.pdf.cell(0, 6, value)
            current_y += 14

    def _add_content_pages(self, sections: list[dict]):
        """Render all content sections"""
        self.pdf.is_cover = False  # Enable header/footer
        self.pdf.add_page()
        self.pdf.set_y(18)  # Start below header

        for section in sections:
            self._render_section(section)

    def _draw_header(self):
        """Draw page header"""
        self.pdf.set_fill_color(*self.COLORS['bg_card'])
        self.pdf.rect(0, 0, 210, 14, 'F')
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(0, 14, 210, 1, 'F')

        self.pdf.set_xy(0, 3)
        self.pdf.set_font('Helvetica', 'B', 8)
        self._set_color('text_muted')
        self.pdf.cell(210, 8, 'SMOT - SOSYAL MEDYA GOZLEM ARACI', align='C')

        self.pdf.set_y(20)

    def _draw_footer(self):
        """Draw page footer"""
        self.pdf.set_y(-18)
        self.pdf.set_fill_color(*self.COLORS['bg_card'])
        self.pdf.rect(0, self.pdf.get_y(), 210, 18, 'F')
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(0, self.pdf.get_y(), 210, 1, 'F')

        self.pdf.set_font('Helvetica', '', 8)
        self._set_color('text_dim')
        self.pdf.cell(0, 15, f'Sayfa {self.pdf.page_no()}', align='C')

    def _check_page_break(self, needed_height: float = 25):
        """Check if we need a new page"""
        if self.pdf.get_y() > 270 - needed_height:
            self.pdf.add_page()
            self.pdf.set_y(18)  # Start below header

    def _render_section(self, section: dict):
        """Render a section with its items"""
        section_type = section.get('type', 'text')
        title = section.get('title', '')
        items = section.get('items', [])

        # Section title
        if title:
            self._check_page_break(20)
            if section_type == 'h1':
                self._render_h1(title)
            elif section_type == 'h2':
                self._render_h2(title)

        # Section items
        for item in items:
            self._render_item(item)

    def _render_h1(self, text: str):
        """Render H1 header"""
        self.pdf.ln(8)
        y = self.pdf.get_y()

        # Full width blue bar
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(15, y, 180, 12, 'F')

        self.pdf.set_xy(20, y + 2)
        self.pdf.set_font('Helvetica', 'B', 12)
        self.pdf.set_text_color(255, 255, 255)
        self.pdf.cell(170, 8, self._safe_text(text))

        self.pdf.set_y(y + 16)

    def _render_h2(self, text: str):
        """Render H2 header"""
        self.pdf.ln(10)
        y = self.pdf.get_y()

        # Card style header
        self.pdf.set_fill_color(*self.COLORS['bg_card'])
        self.pdf.rect(15, y, 180, 10, 'F')
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(15, y, 4, 10, 'F')

        self.pdf.set_xy(22, y + 1)
        self.pdf.set_font('Helvetica', 'B', 11)
        self._set_color('primary')
        self.pdf.cell(0, 8, self._safe_text(text))

        self.pdf.set_y(y + 14)

    def _render_item(self, item: dict):
        """Render individual item"""
        item_type = item.get('type', 'text')

        self._check_page_break(15)

        if item_type == 'h3':
            self._render_h3(item.get('text', ''))
        elif item_type == 'h4':
            self._render_h4(item.get('text', ''))
        elif item_type == 'quote':
            self._render_quote(item.get('text', ''))
        elif item_type == 'bullet':
            self._render_bullet(item.get('text', ''))
        elif item_type == 'numbered':
            self._render_bullet(item.get('text', ''), numbered=True)
        elif item_type == 'table_row':
            self._render_table_row(item.get('cells', []))
        elif item_type == 'hr':
            self._render_hr()
        elif item_type == 'bold_text':
            self._render_bold_text(item.get('text', ''))
        else:
            self._render_text(item.get('text', ''))

    def _render_h3(self, text: str):
        """Render H3 subheader"""
        self.pdf.ln(6)
        self.pdf.set_x(15)
        self.pdf.set_font('Helvetica', 'B', 10)
        self._set_color('secondary')
        self.pdf.cell(0, 6, self._safe_text(text))
        self.pdf.ln(3)
        # Small underline
        self.pdf.set_fill_color(*self.COLORS['secondary'])
        self.pdf.rect(15, self.pdf.get_y(), 30, 1, 'F')
        self.pdf.ln(5)

    def _render_h4(self, text: str):
        """Render H4 subheader"""
        self.pdf.ln(4)
        self.pdf.set_x(15)
        self.pdf.set_font('Helvetica', 'B', 9)
        self._set_color('text_white')
        self.pdf.cell(0, 5, self._safe_text(text))
        self.pdf.ln(4)

    def _render_quote(self, text: str):
        """Render blockquote"""
        self.pdf.ln(4)
        y = self.pdf.get_y()

        safe_text = self._safe_text(text)
        # Estimate height
        text_width = self.pdf.get_string_width(safe_text)
        lines = max(1, int(text_width / 155) + 1)
        height = lines * 5 + 10

        self._check_page_break(height + 5)
        y = self.pdf.get_y()

        # Background
        self.pdf.set_fill_color(25, 28, 35)
        self.pdf.rect(15, y, 180, height, 'F')
        # Accent
        self.pdf.set_fill_color(*self.COLORS['primary'])
        self.pdf.rect(15, y, 4, height, 'F')

        self.pdf.set_xy(24, y + 4)
        self.pdf.set_font('Helvetica', 'I', 9)
        self._set_color('text_light')
        self.pdf.multi_cell(165, 5, safe_text)

        self.pdf.set_y(y + height + 4)

    def _render_bullet(self, text: str, numbered: bool = False):
        """Render bullet point"""
        self.pdf.ln(2)
        y = self.pdf.get_y()

        # Bullet
        if not numbered:
            self.pdf.set_fill_color(*self.COLORS['secondary'])
            self.pdf.rect(20, y + 2, 3, 3, 'F')

        self.pdf.set_xy(28, y)
        self.pdf.set_font('Helvetica', '', 9)
        self._set_color('text_light')
        self.pdf.multi_cell(162, 5, self._safe_text(self._strip_md(text)))

    def _render_table_row(self, cells: list[str]):
        """Render table row"""
        if not cells:
            return

        self.pdf.ln(1)
        y = self.pdf.get_y()

        # Row background
        self.pdf.set_fill_color(22, 24, 28)
        self.pdf.rect(15, y, 180, 7, 'F')

        col_width = 175 / len(cells)
        self.pdf.set_xy(17, y)
        self.pdf.set_font('Helvetica', '', 8)

        for i, cell in enumerate(cells):
            if i == 0:
                self._set_color('text_muted')
            else:
                self._set_color('text_light')
            cell_text = self._safe_text(self._strip_md(cell))[:40]
            self.pdf.cell(col_width, 7, cell_text)

        self.pdf.ln(1)

    def _render_hr(self):
        """Render horizontal rule"""
        self.pdf.ln(6)
        self.pdf.set_fill_color(*self.COLORS['border'])
        self.pdf.rect(15, self.pdf.get_y(), 180, 1, 'F')
        self.pdf.ln(6)

    def _render_bold_text(self, text: str):
        """Render text with bold markers"""
        self.pdf.ln(2)
        self.pdf.set_x(15)
        self.pdf.set_font('Helvetica', '', 9)
        self._set_color('text_light')
        self.pdf.multi_cell(180, 5, self._safe_text(self._strip_md(text)))

    def _render_text(self, text: str):
        """Render normal paragraph"""
        self.pdf.ln(1)
        self.pdf.set_x(15)
        self.pdf.set_font('Helvetica', '', 9)
        self._set_color('text_light')
        self.pdf.multi_cell(180, 5, self._safe_text(self._strip_md(text)))

    def _strip_md(self, text: str) -> str:
        """Remove markdown formatting"""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        return text

    def _add_disclaimer_page(self):
        """Add disclaimer page"""
        self.pdf.add_page()
        self.pdf.set_y(18)  # Below header

        # Title
        self.pdf.set_xy(15, 25)
        self.pdf.set_font('Helvetica', 'B', 14)
        self._set_color('primary')
        self.pdf.cell(0, 10, 'METODOLOJI VE SORUMLULUK REDDI')

        self.pdf.ln(15)

        disclaimer_sections = [
            ('VERI KAYNAKLARI', [
                'Kamuya acik sosyal medya paylasimlari (X/Twitter)',
                'Kullanicinin profil bilgileri ve biyografisi',
                'Tweet metinleri, etkilesim istatistikleri',
            ]),
            ('ANALIZ METODOLOJISI', [
                'OpenAI GPT modeli ile dogal dil isleme',
                'Yesil/Kirmizi/Gri Takim analiz cercevesi',
                'Istatistiksel etkilesim metrikleri',
            ]),
            ('KISITLAMALAR', [
                'Analiz sadece kamuya acik verilere dayanmaktadir',
                'AI yorumlari kesin gercekleri yansitmayabilir',
                'Siyasi egilim tespitleri istatistiksel tahminlerdir',
            ]),
        ]

        for title, items in disclaimer_sections:
            self.pdf.set_x(15)
            self.pdf.set_font('Helvetica', 'B', 10)
            self._set_color('secondary')
            self.pdf.cell(0, 8, title)
            self.pdf.ln(6)

            for item in items:
                self.pdf.set_fill_color(*self.COLORS['secondary'])
                self.pdf.rect(20, self.pdf.get_y() + 2, 2, 2, 'F')
                self.pdf.set_x(26)
                self.pdf.set_font('Helvetica', '', 9)
                self._set_color('text_light')
                self.pdf.cell(0, 5, item)
                self.pdf.ln(5)

            self.pdf.ln(6)

        # Legal notice
        self.pdf.ln(5)
        self.pdf.set_fill_color(*self.COLORS['bg_card'])
        y = self.pdf.get_y()
        self.pdf.rect(15, y, 180, 35, 'F')

        self.pdf.set_xy(20, y + 5)
        self.pdf.set_font('Helvetica', 'B', 9)
        self._set_color('warning')
        self.pdf.cell(0, 5, 'YASAL UYARI')

        self.pdf.set_xy(20, y + 12)
        self.pdf.set_font('Helvetica', '', 8)
        self._set_color('text_muted')
        notice = ('Bu rapor sadece bilgilendirme amaclidir. Icerik, herhangi bir kisi '
                  'veya kurumun resmi gorusunu temsil etmez. Rapordaki bilgilerin '
                  'dogrulugu garanti edilmez.')
        self.pdf.multi_cell(170, 4, notice)

        # Footer branding
        self.pdf.set_xy(15, 250)
        self.pdf.set_font('Helvetica', 'B', 11)
        self._set_color('secondary')
        self.pdf.cell(0, 6, 'SMOT - SOSYAL MEDYA GOZLEM ARACI')

        self.pdf.set_xy(15, 258)
        self.pdf.set_font('Helvetica', '', 9)
        self._set_color('text_dim')
        self.pdf.cell(0, 5, 'AI-Powered Political Intelligence Platform v3.1')


def generate_intelligence_pdf(username: str, name: str, party: str,
                              district: str, content: str) -> bytes:
    """
    Generate a professional PDF intelligence report

    Args:
        username: Twitter handle
        name: Full name
        party: Political party
        district: Electoral district
        content: Markdown report content

    Returns:
        PDF bytes
    """
    generator = IntelligencePDFGenerator()
    return generator.generate(username, name, party, district, content)
