import re
from typing import Dict, List, Tuple, Any

class TipTapValidator:
    # Валидатор структуры TIPTAP JSON

    # Разрешенные типы узлов (добавлен noticeBlock на всякий случай)
    ALLOWED_NODES = {
        'doc', 'paragraph', 'text', 'heading',
        'bulletList', 'orderedList', 'listItem',
        'hardBreak', 'horizontalRule',
        'image', 'notice', 'noticeBlock'
    }

    # Разрешенные типы форматирования 
    ALLOWED_MARKS = {
        'bold', 'italic', 'underline', 'strike',
        'code', 'link', 'subscript', 'superscript',
        'textStyle', 'highlight'
    }

    # Разрешенные значения для атрибутов
    ALLOWED_TEXT_ALIGN = {'left', 'center', 'right', 'justify', 'start', 'end'}
    
    NOTICE_BLOCK_KINDS = {
        'warning', 'caution', 'disassembly', 'assembly', 'inspect', 'clean', 
        'measure', 'lubricate', 'toolSize', 'torque', 'electrical', 'reference', 'weight'
    }
    
    # Добавлен transparent, initial и blob: для картинок
    COLOR_REGEX = re.compile(r'^(#([0-9a-fA-F]{3,8})|rgba?\([^)]+\)|transparent|initial)$', re.IGNORECASE)
    FONT_SIZE_REGEX = re.compile(r'^(\d+(\.\d+)?(px|em|rem|%|pt)?)$', re.IGNORECASE)
    IMAGE_SRC_REGEX = re.compile(r'^(https?://|data:image/|blob:)', re.IGNORECASE)
    
    # Ограничения 
    MAX_TEXT_LENGTH = 10000 
    MAX_DOCUMENT_LENGTH = 50000
    MAX_EMPTY_PARAGRAPHS = 5 # Увеличил до 5, чтобы не триггерить на пустые абзацы между блоками
    MAX_DEPTH = 15

    def __init__(self, data: Dict[str, Any], verbose: bool = False):
        self.data = data
        self.verbose = verbose
        self.errors: List[str] = []
        self._total_text_length = 0
        self._empty_paragraphs_in_row = 0

    def validate(self) -> Tuple[bool, List[str]]:
        self.errors = []
        self._total_text_length = 0
        self._empty_paragraphs_in_row = 0

        if not isinstance(self.data, dict):
            self.errors.append('Корневой элемент должен быть JSON-объектом (dict)')
            return self._finalize()
        
        if self.data.get('type') != 'doc':
            self.errors.append(f"Корневой тип должен быть 'doc', получено: '{self.data.get('type')}'")
            return self._finalize()

        if 'content' not in self.data or not isinstance(self.data['content'], list):
            self.errors.append('Документ пуст: отсутствует или не является массивом поле content')
            return self._finalize()

        self._validate_content(self.data['content'], path='root.content', depth=0)

        if self._total_text_length > self.MAX_DOCUMENT_LENGTH:
            self.errors.append(
                f'Общая длина текста ({self._total_text_length}) превышает лимит ({self.MAX_DOCUMENT_LENGTH})'
            )
            
        return self._finalize()
    
    def _validate_content(self, content: List, path: str, depth: int): 
        if not isinstance(content, list):
            self.errors.append(f'{path}: поле content должно быть массивом')
            return

        for index, node in enumerate(content):
            self._validate_node(node, path=f'{path}[{index}]', depth=depth)

    def _validate_node(self, node: Dict, path: str, depth: int):
        if not isinstance(node, dict):
            self.errors.append(f'{path}: узел должен быть объектом')
            return
        if 'type' not in node:
            self.errors.append(f'{path}: узел должен иметь поле "type"')
            return

        node_type = node['type']

        if node_type not in self.ALLOWED_NODES:
            self.errors.append(f"{path}: элемент '{node_type}' не поддерживается")
            return 

        if depth > self.MAX_DEPTH:
            self.errors.append(f'{path}: превышена максимальная глубина вложенности ({self.MAX_DEPTH})')
            return  

        if 'attrs' in node and isinstance(node['attrs'], dict):
            self._validate_attrs(node['attrs'], node_type, path)

        if node_type == 'paragraph':
            self._check_empty_paragraph(node, path) 

        if node_type == 'text':
            if 'marks' in node:
                if isinstance(node['marks'], list):
                    self._validate_marks(node['marks'], path=f'{path}.marks')
            
            if 'text' not in node or node['text'] is None:
                self.errors.append(f'{path}: текстовый узел должен иметь поле "text"')
                return

            text = str(node['text'])
            self._total_text_length += len(text)

            if len(text) > self.MAX_TEXT_LENGTH:
                self.errors.append(f'{path}: текст слишком длинный ({len(text)} > {self.MAX_TEXT_LENGTH})')

            if text.strip():
                self._empty_paragraphs_in_row = 0

        if 'content' in node:
            if isinstance(node['content'], list):
                self._validate_content(node['content'], path=f'{path}.content', depth=depth + 1)

    def _validate_attrs(self, attrs: Dict, node_type: str, path: str):
        if node_type == 'heading':
            level = attrs.get('level')
            if level is None or not isinstance(level, int) or not (1 <= level <= 6):
                self.errors.append(f"{path}.attrs.level: уровень заголовка должен быть целым числом от 1 до 6")
            
            align = attrs.get('textAlign')
            if align and align not in self.ALLOWED_TEXT_ALIGN:
                self.errors.append(f"{path}.attrs.textAlign: недопустимое выравнивание '{align}'")

        elif node_type == 'paragraph':
            align = attrs.get('textAlign')
            if align and align not in self.ALLOWED_TEXT_ALIGN:
                self.errors.append(f"{path}.attrs.textAlign: недопустимое выравнивание '{align}'")

        elif node_type == 'orderedList':
            start = attrs.get('start')
            if start is not None and (not isinstance(start, int) or start < 1):
                self.errors.append(f"{path}.attrs.start: нумерация должна начинаться с целого числа >= 1")

        elif node_type == 'image':
            src = attrs.get('src')
            if not src:
                self.errors.append(f"{path}.attrs.src: обязательный атрибут для изображения")
            elif not isinstance(src, str) or not self.IMAGE_SRC_REGEX.match(src):
                self.errors.append(f"{path}.attrs.src: недопустимый источник. Разрешены http://, https://, blob: или data:image/...")
            
            # Проверка на null или строку
            if attrs.get('alt') is not None and not isinstance(attrs['alt'], str):
                self.errors.append(f"{path}.attrs.alt: должен быть строкой или null")
            if attrs.get('title') is not None and not isinstance(attrs['title'], str):
                self.errors.append(f"{path}.attrs.title: должен быть строкой или null")

        # Поддержка и notice, и noticeBlock (в зависимости от того, как названо в TipTapExtension)
        elif node_type in ('notice', 'noticeBlock'):
            kind = attrs.get('kind')
            if not kind:
                self.errors.append(f"{path}.attrs.kind: обязательный атрибут для {node_type}")
            elif kind not in self.NOTICE_BLOCK_KINDS:
                self.errors.append(f"{path}.attrs.kind: недопустимое значение '{kind}'. Разрешены: {', '.join(sorted(self.NOTICE_BLOCK_KINDS))}")

    def _check_empty_paragraph(self, node: Dict, path: str): 
        content = node.get('content', [])
        if not isinstance(content, list):
            return
            
        is_empty = True
        for child in content:
            if not isinstance(child, dict):
                continue
            if child.get('type') == 'text' and str(child.get('text', '')).strip():
                is_empty = False
                break
            if child.get('type') in ('hardBreak', 'horizontalRule'):
                is_empty = False
                break

        if is_empty:
            self._empty_paragraphs_in_row += 1
            if self._empty_paragraphs_in_row > self.MAX_EMPTY_PARAGRAPHS:
                self.errors.append(
                    f"{path}: слишком много пустых параграфов подряд (максимум {self.MAX_EMPTY_PARAGRAPHS})"
                )
        else:
            self._empty_paragraphs_in_row = 0

    def _validate_marks(self, marks: List, path: str):
        for index, mark in enumerate(marks):
            mark_path = f'{path}[{index}]'

            if not isinstance(mark, dict):
                self.errors.append(f'{mark_path}: mark должен быть объектом')
                continue
                
            if 'type' not in mark:
                self.errors.append(f'{mark_path}: mark должен иметь поле type')
                continue

            mark_type = mark['type']

            if mark_type not in self.ALLOWED_MARKS:
                self.errors.append(f"{mark_path}: форматирование '{mark_type}' не поддерживается")
                continue

            if 'attrs' in mark and isinstance(mark['attrs'], dict):
                attrs = mark['attrs']
                
                if mark_type == 'link':
                    self._validate_link(attrs, mark_path)
                elif mark_type == 'textStyle':
                    self._validate_text_style(attrs, mark_path)
                elif mark_type == 'highlight':
                    self._validate_highlight(attrs, mark_path)

    def _validate_text_style(self, attrs: Dict, path: str):
        # Используем `if color:` вместо `if color is not None:`, чтобы игнорировать и null, и ""
        color = attrs.get('color')
        if color:
            if not isinstance(color, str):
                self.errors.append(f"{path}.attrs.color: должен быть строкой")
            elif not self.COLOR_REGEX.match(color):
                self.errors.append(f"{path}.attrs.color: недопустимый формат цвета '{color}'")
        
        font_size = attrs.get('fontSize')
        if font_size:
            if not isinstance(font_size, str):
                self.errors.append(f"{path}.attrs.fontSize: должен быть строкой")
            elif not self.FONT_SIZE_REGEX.match(font_size):
                self.errors.append(f"{path}.attrs.fontSize: недопустимый формат размера '{font_size}'")

    def _validate_highlight(self, attrs: Dict, path: str):
        color = attrs.get('color')
        if color:
            if not isinstance(color, str):
                self.errors.append(f"{path}.attrs.color: должен быть строкой")
            elif not self.COLOR_REGEX.match(color):
                self.errors.append(f"{path}.attrs.color: недопустимый формат цвета выделения '{color}'")

    def _validate_link(self, attrs: Dict, path: str):
        href = attrs.get('href')
        if href is None:
            self.errors.append(f"{path}.attrs.href: обязательный атрибут для ссылки")
            return
            
        if not isinstance(href, str):
            self.errors.append(f"{path}.attrs.href: должен быть строкой")
            return
            
        href = href.strip()
        if not href:
            self.errors.append(f"{path}.attrs.href: ссылка должна иметь непустой href")
            return

        dangerous = ('javascript:', 'data:', 'vbscript:', 'file:')
        if any(href.lower().startswith(d) for d in dangerous):
            self.errors.append(f"{path}.attrs.href: опасный протокол в ссылке '{href}'")
            return

        # allowed_prefixes = ('https://', 'http://', 'dmref://', '#', '/', 'blob:')
        # if not any(href.startswith(prefix) for prefix in allowed_prefixes):
        #     self.errors.append(
        #         f"{path}.attrs.href: запрещенный протокол '{href}'. Разрешены: https, http, dmref, якоря (#), относительные (/), blob:"
        #     )

    def _finalize(self) -> Tuple[bool, List[str]]:
        is_valid = len(self.errors) == 0

        if self.verbose and not is_valid:
            print(f'[TipTap Validator] Ошибок: {len(self.errors)}')
            for err in self.errors:
                print(f'  - {err}')

        return is_valid, self.errors