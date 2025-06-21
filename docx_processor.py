# import docx
# from docx.shared import Pt, Cm
# from docx.oxml import parse_xml
# from docx.oxml.ns import nsdecls
# import pandas as pd
# from typing import List, Dict, Union
# import io
# import re
#
#
# class DocxProcessor:
#     @staticmethod
#     def extract_basic_metadata(doc) -> Dict:
#         """Извлекает только основные параметры оформления из DOCX"""
#         sections = doc.sections[0]
#         style = doc.styles['Normal']
#
#         return {
#             'font': style.font.name,
#             'font_size': style.font.size.pt if style.font.size else 14,
#             'top_margin': sections.top_margin.cm,
#             'bottom_margin': sections.bottom_margin.cm,
#             'left_margin': sections.left_margin.cm,
#             'right_margin': sections.right_margin.cm,
#             'line_spacing': style.paragraph_format.line_spacing or 1.5,
#             'paragraph_indent': style.paragraph_format.first_line_indent.cm if style.paragraph_format.first_line_indent else 1.25,
#             'has_headers': len(doc.sections[0].header.tables) > 0,
#             'has_pagination': any(page_num in f.text for page_num in ['стр.', 'page'] for f in doc.footers),
#             'has_title_page': any('титульный' in p.text.lower() for p in doc.paragraphs[:10])
#         }
#
#     @staticmethod
#     def _check_headers(doc) -> bool:
#         """Проверяет оформление заголовков по ГОСТ"""
#         for paragraph in doc.paragraphs:
#             if paragraph.style.name.startswith('Heading'):
#                 # Проверка: заголовки должны быть жирными и без точки в конце
#                 if not paragraph.style.font.bold:
#                     return False
#                 if paragraph.text.strip().endswith('.'):
#                     return False
#                 # Проверка выравнивания (по центру для заголовков 1 уровня)
#                 if 'Heading 1' in paragraph.style.name and paragraph.alignment != 1:  # 1 = center
#                     return False
#         return True
#
#     @staticmethod
#     def _check_images(doc) -> bool:
#         """Проверяет оформление рисунков по ГОСТ"""
#         has_errors = False
#         for paragraph in doc.paragraphs:
#             if 'Рис.' in paragraph.text:
#                 # Проверка формата подписи: "Рис. 1. - Описание"
#                 if not re.match(r'^Рис\. \d+\..+', paragraph.text):
#                     has_errors = True
#                 # Проверка что рисунок действительно существует перед подписью
#                 if not DocxProcessor._has_image_before_paragraph(doc, paragraph):
#                     has_errors = True
#         return not has_errors
#
#     @staticmethod
#     def _has_image_before_paragraph(doc, paragraph) -> bool:
#         """Проверяет наличие рисунка перед подписью"""
#         # Логика поиска изображения перед подписью
#         prev_elem = paragraph._element.getprevious()
#         while prev_elem is not None:
#             if prev_elem.tag.endswith('pict'):
#                 return True
#             prev_elem = prev_elem.getprevious()
#         return False
#
#     @staticmethod
#     def _check_tables(doc) -> bool:
#         """Проверяет оформление таблиц по ГОСТ"""
#         for table in doc.tables:
#             # Проверка наличия заголовка таблицы
#             if not table.rows[0].cells[0].text.strip():
#                 return False
#
#             # Проверка что таблица имеет границы
#             tbl_pr = table._element.xpath('w:tblPr')
#             if tbl_pr and 'w:borders' not in tbl_pr[0].xml:
#                 return False
#         return True
#
#     @staticmethod
#     def _check_links(doc) -> bool:
#         """Проверяет оформление ссылок по ГОСТ"""
#         for paragraph in doc.paragraphs:
#             if '[' in paragraph.text and ']' in paragraph.text:
#                 # Проверка формата ссылок: [1] или [1, с. 15]
#                 if not re.search(r'\[\d+(, с\. \d+)?\]', paragraph.text):
#                     return False
#         return True
#
#     @staticmethod
#     def _check_details(doc) -> bool:
#         """Проверяет наличие всех реквизитов документа"""
#         required_details = [
#             'УДК', 'ББК', 'Автор', 'Название',
#             'Год', 'Страниц'
#         ]
#         first_page_text = '\n'.join(p.text for p in doc.paragraphs[:20])
#         return all(detail in first_page_text for detail in required_details)
#
#     @staticmethod
#     def _check_contents(doc) -> bool:
#         """Проверяет содержание/оглавление"""
#         for paragraph in doc.paragraphs:
#             if 'содержание' in paragraph.text.lower() or 'оглавление' in paragraph.text.lower():
#                 # Проверка что содержание не пустое
#                 next_para = paragraph._element.getnext()
#                 if next_para is not None and next_para.text.strip():
#                     return True
#         return False
#
#     @staticmethod
#     def _check_lists(doc) -> bool:
#         """Проверяет оформление списков"""
#         for paragraph in doc.paragraphs:
#             if paragraph.style.name == 'List Paragraph':
#                 # Проверка отступов в списках
#                 if paragraph.paragraph_format.left_indent < Pt(18):
#                     return False
#         return True
#
#     @staticmethod
#     def _check_appendix(doc) -> bool:
#         """Проверяет оформление приложений"""
#         appendix_pattern = re.compile(r'^Приложение [А-Я]', re.IGNORECASE)
#         for paragraph in doc.paragraphs:
#             if appendix_pattern.match(paragraph.text):
#                 # Проверка что приложение начинается с новой страницы
#                 if 'pageBreakBefore' not in paragraph._element.xml:
#                     return False
#         return True
#
#     @staticmethod
#     def _check_pagination(doc) -> bool:
#         """Проверяет наличие нумерации страниц"""
#         for footer in doc.sections[0].footer.paragraphs:
#             if any(char.isdigit() for char in footer.text):
#                 return True
#         return False
#
#     @staticmethod
#     def _check_title_page(doc) -> bool:
#         """Проверяет наличие титульного листа"""
#         first_page_text = '\n'.join(p.text for p in doc.paragraphs[:10])
#         keywords = ['реферат', 'курсовая', 'диплом', 'титульный']
#         return any(keyword in first_page_text.lower() for keyword in keywords)
#
#     @staticmethod
#     def process_files(files: List[io.BytesIO]) -> pd.DataFrame:
#         """Обрабатывает список файлов и возвращает DataFrame"""
#         data = []
#         for file in files:
#             try:
#                 doc = docx.Document(file)
#                 metadata = DocxProcessor.extract_metadata(doc)
#                 data.append(metadata)
#             except Exception as e:
#                 print(f"Ошибка обработки файла: {str(e)}")
#         return pd.DataFrame(data)
