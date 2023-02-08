import io

from abc import ABC
from copy import deepcopy


__all__ = [
    'Comment',
    'Node',
    'Exps',
    'Label',
    'Int',
    'Float',
    'Quoted',
    'Statement',
    'Var',
]


class Node(ABC):
    def pretty(self, f=None, indent='\t'):
        no_f = f is None
        if no_f:
            f = io.StringIO()

        self.__pretty__(f, indent, 0)

        if no_f:
            return f.getvalue()

    def __pretty__(self, f, indent, level):
        f.write(str(self))



class Exps(Node):
    def __init__(self, exps=None):
        if exps is None:
            exps = []
        self._exps = exps

    def clear(self):
        self._exps = []

    def extend(self, exps):
        self._exps.extend(exps)

    def append(self, exp):
        self._exps.append(exp)

    def labels(self):
        for exp in self._exps:
            match exp:
                case Statement(Label(l), _, _):
                    yield l

    def __len__(self):
        return sum(not isinstance(e, Comment) for e in self._exps)

    def __bool__(self):
        return len(self) != 0

    def __iter__(self):
        yield from self._exps

    def _get_statement(self, key):
        match key:
            case tuple((k, j)):
                key, i = k, j
            case k:
                key, i = k, 0

        # XXX: can be done in O(1) if we keep track of:
        #      - key, i |-> exps[i]
        # XXX: can do negative indexing in O(1) if we also keep track of:
        #      - key |-> number of exps using key
        j = i
        has_key = False
        for exp in self._exps:
            match exp:
                case Statement(k, _, v):
                    if k != key:
                        continue

                    has_key = True
                    if j >= 1:
                        j -= 1
                        continue

                    return exp

        if has_key:
            raise KeyError(key)
        else:
            raise IndexError(i)


    def set(self, key, value, i=0):
        statement = self._get_statement(key)
        statement.right = value

    def __getitem__(self, key):
        statement = self._get_statement(key)
        return statement.right

    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, IndexError):
            return default

    def __pretty__(self, f, indent, level):

        if level != 0:
            if self._exps:
                f.write('{\n')
            else:
                f.write('{ }')
                return

        for exp in self._exps:
            f.write(indent*level)
            exp.__pretty__(f, indent, level)
            f.write('\n')

        if level > 0:
            f.write(indent*(level-1))
            f.write('}')

    def __repr__(self):
        exps = ', '.join(map(repr, self._exps))
        return f'{self.__class__.__name__}([{exps}])'

    def __eq__(self, other):
        return self._exps == other._exps


class Statement(Node):
    __match_args__ = ('left', 'op', 'right')

    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __pretty__(self, f, indent, level):
        self.left.__pretty__(f, indent, level)
        f.write(f' {self.op} ')
        self.right.__pretty__(f, indent, level+1)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.left!r}, {self.op!r}, {self.right!r})'

    def __iter__(self):
        yield self.left
        yield self.op
        yield self.right

    def __eq__(self, other):
        return (
            self.left == other.left
            and self.op == other.op
            and self.right == other.right
        )


class Comment(str, Node):
    def __new__(cls, s):
        return super().__new__(cls, s.strip())

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)!r})'


class Label(str, Node):
    def __new__(cls, s):
        return super().__new__(cls, str(s))

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)!r})'


class Var(str, Node):
    def __new__(cls, s):
        return super().__new__(cls, s.strip('@'))

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)!r})'

    def __pretty__(self, f, indent, level):
        f.write(f'@{str(self)}')


class Quoted(str, Node):
    def __new__(cls, s):
        return super().__new__(cls, s.strip('"'))

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self)!r})'

    def __pretty__(self, f, indent, level):
        f.write(f'"{str(self)}"')

class Int(int, Node):
    def __new__(cls, x):
        return super().__new__(cls, x)

class Float(float, Node):
    def __new__(cls, x):
        return super().__new__(cls, x)
