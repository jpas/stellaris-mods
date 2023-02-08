import copy
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

import stellaris.ast as ast
from stellaris.parser import parse, parse_template


__all__ = [
    'Patcher'
    'load',
    'load_glob',
    'parse',
    'parse_template',
    'mod'
    'build_mods',
]


class Patcher:
    def __init__(self, game_dir):
        self.game_dir = Path(game_dir).expanduser()
        self._pristine = {}
        self._scratch = {}
        self._localization = defaultdict(dict)

    def _prep_path(self, path):
        path = Path(path)
        if path.is_absolute():
            full_path = path
            path = full_path.relative_to(self.game_dir)
        else:
            full_path = self.game_dir/path

        return full_path, path

    def touch(self, path):
        full_path, path = self._prep_path(path)

        assert not full_path.exists()

        exps = self._scratch[path] = ast.Exps()
        return exps

    def override(self, path, *args):
        match args:
            case (label, value):
                pass
            case (value,):
                pass

    def load(self, path):
        full_path, path = self._prep_path(path)

        try:
            scratch = self._scratch[path]
        except KeyError:
            pristine = self._pristine[path] = parse(full_path.read_text())
            scratch = self._scratch[path] = copy.deepcopy(pristine)

        return scratch

    def load_glob(self, *globs):
        for glob in globs:
            for path in self.game_dir.glob(glob):
                yield path.relative_to(self.game_dir), self.load(path)

    def write_to_dir(self, out_dir, dry=False):
        written = []

        for path, scratch in sorted(self._scratch.items()):
            try:
                if self._pristine[path] == scratch:
                    continue
            except KeyError:
                pass

            path = out_dir/path
            written.append(path)
            if dry:
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(scratch.pretty())

        loc_dir = out_dir/'localisation/zz'

        for (prefix, language), keys in self._localization.items():
            path = loc_dir/f'{prefix}_l_{language}.yml'
            written.append(path)
            if dry:
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(mode='w', encoding='utf-8-sig') as f:
                f.write(f'l_{language}:\n')
                for key, loc in keys.items():
                    f.write(f' {key} "{loc}"\n')

        return written

    def localize(self, prefix, locs, language='english'):
        for key, loc in locs:
            self._localization[prefix, language][key] = loc


_patcher = Patcher('~/.local/share/Steam/steamapps/common/Stellaris')

touch = _patcher.touch
load = _patcher.load
load_glob = _patcher.load_glob
override = _patcher.override

known_mods = {}

def build_mods(args=None):
    p = ArgumentParser()
    p.add_argument('--dry', '-d', action='store_true')
    p.add_argument('--output', '-o', type=Path, default='.')
    args = p.parse_args(args)

    args.patcher = _patcher

    for _, m in known_mods.items():
        m.build(args)

    for path in args.patcher.write_to_dir(args.output, dry=args.dry):
        print(path)


def mod(name, deps=None):
    def wrapper(build_fn):
        return Mod(name, build_fn, deps=deps)
    return wrapper


class Mod:
    def __init__(self, name, build_fn, deps=None):
        self.name = name
        self.deps = deps if deps is not None else []

        self._build_fn = build_fn

        assert name not in known_mods
        for dep in self.deps:
            assert dep in known_mods

        known_mods[name] = self

    def build(self, args=None):
        return self._build_fn(args)
