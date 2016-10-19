import ast


class EllipseReplace(ast.NodeTransformer):
    def __init__(self, replacement=None):
        self.replacement = replacement

    def visit_Ellipsis(self, node):
        return self.replacement

    def visit_Subscript(self, node):
        # Don't touch any slices.
        return node


def ellipsis_in_children(node, recursive=False):
    return any(
        isinstance(child, ast.Ellipsis) or
        (recursive is True and ellipsis_in_children(child, recursive=recursive))
        for child in ast.iter_child_nodes(node)
    )


class EllipsisPartialTransformer(ast.NodeTransformer):
    def __init__(self):
        self._counter = 0

    def _get_arg_name(self):
        """Return unique argument name for lambda."""
        try:
            return '_' * (self._counter + 1)
        finally:
            self._counter += 1

    def _replace(self, node, arg_name=None):
        return EllipseReplace(ast.Name(id=arg_name, ctx=ast.Load())).visit(node)

    def _visit(self, node, recursive=False):
        # Does this node's subtree contain an Ellipsis?
        if ellipsis_in_children(node, recursive=recursive):
            print('Found ellipsis in', node.__class__.__name__)

            # If so, wrap it in a lambda and replace all instances of Ellipsis in
            # the entire subtree with the same variable name.
            node = self._wrap_in_lambda(node)
            node = ast.fix_missing_locations(node)

        return self.generic_visit(node)

    def _wrap_in_lambda(self, node, arg_name=None):
        """Wrap call in lambda and replace ellipsis with argument."""
        if arg_name is None:
            arg_name = self._get_arg_name()

        return ast.Lambda(
            args=ast.arguments(
                args=[ast.arg(arg=arg_name, annotation=None)],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]),
            body=self._replace(node, arg_name))

    #
    #   Only explicitly defined visit_* functions will result
    #   in _visit being called on a given node.
    #
    #   The intention is to limit to *only* expression calls
    #   so that any transformations happen to (sub)expressions.
    #

    #
    #   Expressions
    #

    def visit_Call(self, node):
        return self._visit(node)

    def visit_UnaryOp(self, node):
        return self._visit(node)

    def visit_BinOp(self, node):
        return self._visit(node)

    def visit_BoolOp(self, node):
        return self._visit(node)

    def visit_Compare(self, node):
        return self._visit(node)

    def visit_IfExp(self, node):
        return self._visit(node)

    def visit_keyword(self, node):
        return self._visit(node)

    #
    #   Literals
    #

    def visit_List(self, node):
        return self._visit(node)

    def visit_Set(self, node):
        return self._visit(node)

    def visit_Dict(self, node):
        return self._visit(node)

    #
    #   Comprehensions
    #

    def visit_ListComp(self, node):
        return self._visit(node, recursive=True)

    def visit_SetComp(self, node):
        return self._visit(node, recursive=True)

    def visit_GeneratorExp(self, node):
        return self._visit(node, recursive=True)

    def visit_DictComp(self, node):
        return self._visit(node, recursive=True)


transformer = EllipsisPartialTransformer()

#   Ideas for a blog post/writeup
#
#   - Benefits of this expanded approach over the initial call-only transform: f(1, ...)
#   - Preserving existing uses of ... -- what are they, how are they affected?
#   - How does code like this get unit tested?
#   - Different replacements: some nodes need a single-depth of search before replacement
#     while some need recursive replacement (e.g. list comprehension)
#
#   https://mail.python.org/pipermail/python-ideas/2016-January/038135.html
