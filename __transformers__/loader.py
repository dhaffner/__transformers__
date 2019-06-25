import ast
from importlib import import_module
from importlib.machinery import PathFinder, SourceFileLoader
import sys
import logging


class NodeVisitor(ast.NodeTransformer):
    def __init__(self):
        self._found = set()
        logging.debug('NodeVisitor.__init__()')

    def visit_ImportFrom(self, node):
        logging.debug('NodeVisitor....ImportFrom')
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
    logging.debug('transform()')
    """Apply transformations to ast."""
    transformers, tree = NodeVisitor.remove_transformers(tree)

    for module_name in transformers:
        module = import_module('.{}'.format(module_name), '__transformers__')
        logging.debug('xx', module_name)
        tree = module.transformer.visit(tree)

    return tree


class Finder(PathFinder):
    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        logging.debug('find_spec(%s, path=%s, target=%s)', fullname, path, target)
        
        spec = super(Finder, cls).find_spec(fullname, path, target)
        if spec is None:
            return None

        spec.loader = Loader(spec.loader.name, spec.loader.path)
        logging.debug('find_spec(%s, path=%s, target=%s): loader was set', fullname, path, target)
        return spec


class Loader(SourceFileLoader):
    def source_to_code(self, data, path, *, _optimize=-1):
        logging.debug('source_to_code: WTF')
        try:
            logging.debug('source_to_code:try')
            tree = ast.parse(data)
            tree = transform(tree)
            return compile(tree, path, 'exec',
                           dont_inherit=True, optimize=_optimize)
        except ValueError:
            logging.debug('source_to_code:except')
            return compile(data, path, 'exec', dont_inherit=True, optimize=_optimize)


def setup():
    sys.meta_path.insert(0, Finder)
    logging.debug('setup(): sys.meta_path=%s', sys.meta_path)
