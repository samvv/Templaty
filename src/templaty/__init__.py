
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
import importlib.util

from sweetener import clone, warn

from .evaluator import evaluate, shared_context, load_context

def execute(filepath: Path, ctx={}, **kwargs) -> str:
    with open(filepath, 'r') as f:
        contents = f.read()
    return evaluate(contents, ctx, filename=str(filepath.relative_to(Path.cwd())), **kwargs)

helper_export_prefix = 'generate_'
helpers_dir_name = '_helpers'

def dynamic_import(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise RuntimeError(f'failed to load module on path {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert(spec.loader is not None)
    spec.loader.exec_module(module)
    return module

def strip_ext(name: str) -> str:
    chunks = name.split('.')[:-1]
    return '.'.join(chunks)

def execute_dir(dir: Path, dest_dir: Path, ctx: dict[str, Any] | None = None, force: bool = False, **kwargs) -> None:

    if ctx is None:
        ctx = {}

    def is_ignored(path: Path) -> bool:
        return path.name in [ '_helpers', '_helpers.py', '__pycache__' ]

    def visit_helpers(path: Path, ctx) -> None:
        if path.is_file():
            if path.suffixes and path.suffixes[-1] == '.py':
                with open(path, 'r') as f:
                    code = f.read()
                exec(compile(code, path, 'exec'), ctx)
            return
        if path.is_dir():
            for path in path.iterdir():
                visit_helpers(path, ctx)
            return
        warn(f'Skipping {path} because it is not a file nor a directory')

    def visit_code(path: Path, ctx) -> None:
        if is_ignored(path):
            return
        if path.is_file():
            if path.suffixes and path.suffixes[-1] == '.tply':
                with open(path, 'r') as f:
                    contents = f.read()
                result = evaluate(contents, ctx, filename=str(path.relative_to(Path.cwd())), **kwargs)
                dest_path = dest_dir / path.parent.relative_to(dir) / strip_ext(path.name)
                if not force and dest_path.exists():
                    warn(f'Skipping {dest_path} because it already exists')
                    return
                with open(dest_path, 'w') as f:
                    f.write(result)
            else:
                dest_path = dest_dir / path.relative_to(dir)
                if not force and dest_path.exists():
                    warn(f'Skipping {dest_path} because it already exists')
                    return
                shutil.copy2(path, dest_path)
            return
        if path.is_dir():
            dest_path = dest_dir / path.relative_to(dir)
            ctx = clone(ctx)
            helpers_file = path / (helpers_dir_name + '.py')
            if helpers_file.exists():
                visit_helpers(helpers_file, ctx)
            helpers_dir = path / helpers_dir_name
            if helpers_dir.exists():
                visit_helpers(helpers_dir, ctx)
            dest_path.mkdir(parents=True, exist_ok=True)
            for child_path in path.iterdir():
                if child_path.name == helpers_dir_name:
                    continue
                visit_code(child_path, ctx)
            return
        warn(f'Skipping {path} because it is not a file nor a directory')

    old_context = shared_context.value
    shared_context.value = ctx
    try:
        visit_code(dir, ctx)
    finally:
        shared_context.value = old_context

