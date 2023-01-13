import io
import re
from string import Template

import stellaris.ast as ast


__all__ = [
    'Error',
    'LexError',
    'ParseError',
    'parse',
    'parse_template',
]

class Error(Exception):
    pass


class ParseError(Error):
    pass


class LexError(Error):
    pass


def find_pos(text, index):
    line = text.count('\n', 0, index) + 1

    prev_newline = text.rfind('\n', 0, index)
    column = index - prev_newline

    return line, column


def lex(text):
    if not isinstance(text, str):
        raise ValueError('text must be a str')

    skip_chars = set('\t\n\r \ufeff')
    token_chars = set('{=}')
    chars = skip_chars | token_chars

    tokens = {
        # frequency is typically: i > l > q
        'f': r'[+-]?\d+\.\d*',
        'i': r'[+-]?\d+',
        'd': r'\[\[.+\]',
        'a': r'@\\?\[[^]]*\]',
        'p': r'\$[0-9a-zA-Z_|]+\$',
        'v': r'@[a-zA-Z_:.-][^\s>=<]*',
        'l': r'[a-zA-Z_:.-][^\s>=<]*',
        'q': r'"(\\["]|[^"])*"',
        'o': r'[<>!]=?',
        'c': r'#.*',
    }
    tokens_exp = '|'.join(f'(?P<{t}>{e})' for t, e in tokens.items())
    tokens_exp = re.compile(tokens_exp)

    index = 0

    while ...:
        try:
            c = text[index]
        except IndexError:
            return

        prev = index

        if c in chars:
            index += 1
            if c in token_chars:
                yield c, prev, index
            continue

        m = tokens_exp.match(text, index)
        try:
            index = m.end()
            yield m.lastgroup, prev, index
        except AttributeError:
            line, column = find_pos(text, index)
            raise LexError(f'unexpected \'{c!r}\' at {line}:{column}.')


def parse(text):
    tokens = lex(text)

    def parse_exps():
        exps = []

        fst = op = exp = None
        comments = []

        for typ, start, end in tokens:
            try:
                match typ:
                    case 't':
                        continue
                    case 'v':
                        exp = ast.Var(text[start+1:end])
                    case 'l':
                        exp = ast.Label(text[start:end])
                    case 'p':
                        exp = ast.Param(text[start:end])
                    case '=':
                        fst, op = exps.pop(), '='
                        continue
                    case 'o':
                        fst, op = exps.pop(), text[start:end]
                        continue
                    case 'i':
                        exp = ast.Int(text[start:end])
                    case '{':
                        exp = parse_exps()
                    case '}':
                        break
                    case 'f':
                        exp = ast.Float(text[start:end])
                    case 'q':
                        exp = ast.Quoted(text[start:end])
                    case 'c':
                        comments.append(ast.Comment(text[start:end]))
                        continue
                    case 'a':
                        raise ParseError('inline arithmetic not implemented')
                    case 'd':
                        raise ParseError('conditional block not implemented')
                    case _:
                        raise ValueError
            except (IndexError, ValueError):
                line, column = find_pos(text, start)
                raise ParseError(f'unexpected {typ} at {line}:{column}.')
            except Error as e:
                raise e

            if op is not None:
                exp = ast.Statement(fst, op, exp)
                fst = op = None

            if fst is not None:
                raise ValueError

            exps.extend(comments)
            comments = []
            exps.append(exp)

        return ast.Exps(exps)

    return parse_exps()


def parse_template(template, mapping=None, /, **kwds):
    if isinstance(template, str):
        template = Template(template)

    if mapping is None:
        mapping = {}

    return parse(template.substitute(mapping, **kwds))
