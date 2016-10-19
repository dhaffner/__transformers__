import ast
from importlib import import_module
from importlib.machinery import PathFinder, SourceFileLoader
import sys


class NodeVisitor(ast.NodeTransformer):
    def __init__(self):
        self._found = set()

    def visit_ImportFrom(self, node):
        if node.module == '__transformers__':
            self._found.update(
                name.name for name in node.names if name.name not in ('_loader', 'setup')
            )
        else:
            return node

    @classmethod
    def remove_transformers(cls, tree):
        visitor = cls()
        tree = visitor.visit(tree)
        return visitor._found, tree


def transform(tree):
    """Apply transformations to ast."""
    transformers, tree = NodeVisitor.remove_transformers(tree)

    for module_name in transformers:
        module = import_module('.{}'.format(module_name), '__transformers__')
        tree = module.transformer.visit(tree)

    return tree


class Finder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        spec = super(Finder, cls).find_spec(fullname, path, target)
        if spec is None:
            return None

        spec.loader = Loader(spec.loader.name, spec.loader.path)
        return None


class Loader(SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        try:
            tree = ast.parse(data)
            tree = transform(tree)
            return compile(tree, path, 'exec',
                           dont_inherit=True, optimize=_optimize)
        except ValueError:
            return compile(data, path, 'exec', dont_inherit=True, optimize=_optimize)


def setup():
    sys.meta_path.insert(0, Finder)
