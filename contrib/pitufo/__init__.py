import re
import os
import copy
from binascii import hexlify

import rtfunicode

from . import images


STYLES = {
    'Normal': '\\sb280',
    'Heading 1': '\\sb400\\fs48\\b',
    'Heading 2': '\\sb360\\fs40\\b',
    'Heading 3': '\\sb320\\fs32\\b',
    'Heading 4': '\\sb280\\fs24\\b',
    'List Item Level 1': '\\sb80\\tx320\\tx720\\fi-720\\li720\\tab\\\'95\\tab',
    'List Item Level 2': '\\sb80\\tx1040\\tx1440\\fi-1440\\li1440\\tab\\\'95\\tab',
    'List Item Level 3': '\\sb80\\tx1760\\tx2160\\fi-2160\\li2160\\tab\\\'95\\tab',
    'List Item Level 4': '\\sb80\\tx2480\\tx2880\\fi-2880\\li2880\\tab\\\'95\\tab',
    'Table Cell': '\\fs18',
    'Table Cell Left': '\\fs18\\ql',
    'Table Cell Right': '\\fs18\\qr',
    'Table Cell Center': '\\fs18\\qc',
    'Table Header': '\\fs18\\qc\\b',
}

PAGE_MAX_WITH = 8640

class Document(list):
    meta = {}
    styles = copy.copy(STYLES)

    def write(self, f):
        f.write(b'{\\rtf1\\ansi\n')

        if self.meta:
            f.write(b'{\\info\n')
            for key, value in self.meta.items():
                start = b'{\\'
                end = b'}'
                if key not in ('title', 'subject', 'author', 'operator', 'keywords', 'comment', 'doccomm', ):
                    start += b'*\\'
                f.write(start + '{key} {value}'.format(key=key, value=_render_value(value)).encode() + end)
            f.write(b'}\n')

        for command in self:
            # print(command.render())
            f.write(command.render(styles=self.styles).encode())

        f.write(b'}\n')
        f.flush()


class Paragraph(object):
    START = '\\pard\\plain{style} '
    END = '\n\\par\n'

    def __init__(self, content, style='Normal'):
        self.content = content
        self.style = style
        super().__init__()

    def render(self, styles):
        content = ''
        for value in self.content:
            content += _render_value(value)
        return self.START.format(style=styles[self.style]) + content + self.END


class Heading(Paragraph):

    def __init__(self, content, level=1, style=None):
        style = 'Heading {0}'.format(level)
        super().__init__(content, style)


class BulletedListItem(Paragraph):

    def __init__(self, content, level=1, style=None):
        style = 'List Item Level {0}'.format(level)
        super().__init__(content, style)


class Image(Paragraph):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.START += '\\qc '
        self.END = ']}}' + self.END
        self.filename = os.path.basename(self.content)

    def render(self, styles):
        return self.START.format(style=styles[self.style]) \
                + '{\\*\\shppict ' + _render_image(self.content) \
                + '}{\\nonshppict {[' \
                + self.filename + self.END


class Table(list):

    def render(self, styles):
        num_cols = max([len(row) for row in self])
        col_width = PAGE_MAX_WITH / num_cols
        row_format = '\\trowd \\trqc\\trgaph108\\trrh280\n'
        for i in range(num_cols):
            row_format += '\\clbrdrt\\brdrs\\clbrdrl\\brdrs\\clbrdrb\\brdrs\\clbrdrr\\brdrs\\cellx{0}\n'.format(int(col_width * (i+1)))
        result = '\\pard\\plain\\par\n'
        for row in self:
            result += row_format
            result += row.render(styles, cols=num_cols)
            result += '\\intbl\\row\n'
        return result


class TableRow(list):

    def render(self, styles, cols=0):
        result = ''
        padding = [TableCell([''])] * (cols - len(self))
        for cell in self + padding:
            result += cell.render(styles)
        return result


class TableCell(Paragraph):

    def __init__(self, content, style='Table Cell'):
        super().__init__(content, style=style)
        self.START = '\\intbl' + self.START
        self.END = '\\cell\n'

    # def render(self):
    #     print(type(self.content), self.content)
    #     return '-'


def _render_values(values):
    result = ''
    for value in values:
        result += _render_value(value)
    return result


def _render_value(value):
    '''encodes unicode if needed, and interprets some basic HTML tags'''

    if type(value) is bytes:
        value = value.decode()

    elif re.match(r'^<br\s?/?>$', value, flags=re.IGNORECASE):
        value = '\\line '
    elif re.match(r'^<sup>$', value, flags=re.IGNORECASE):
        value = '\\super '
    elif re.match(r'^<sub>$', value, flags=re.IGNORECASE):
        value = '\\sub '
    elif re.match(r'^</su[pb]>$', value, flags=re.IGNORECASE):
        value = '\\nosupersub '

    else:
        value = value.encode('rtfunicode').decode()
    return value


def _render_image(filepath):

    GOAL_FACTOR = 10  # default is 20 twips per pixel

    result = ['{\\pict']
    name, extension = os.path.splitext(filepath)
    extension = extension.lower()

    with open(filepath, 'rb') as f:
        # get image type and dimensoins
        if extension == '.png':
            img_type = 'pngblip'
            width, height = images._get_png_dimensions(f.read(100))
        elif extension in ('.jpg', '.jpeg'):
            img_type = 'jpegblip'
            width, height = images._get_jpg_dimensions(f)
        else:
            raise Exception('unkown image type: ' + extension)

        # issue preamble, with image type and dimensoins
        goal_factor = min(GOAL_FACTOR, 1.0*PAGE_MAX_WITH/width)
        preamble = '\\{img_type}\\picw{0}\\pich{1}\\picwgoal{2}\\pichgoal{3}'.format(
            width, height, int(width*goal_factor), int(height*goal_factor), img_type=img_type)
        result.append(preamble)

        # dump the file in hex format
        f.seek(0, 0)
        image = hexlify(f.read())
        for i in range(0, len(image), 128):
            result.append(image[i:i+128].decode())

    result.append('}')
    return '\n'.join(result)
