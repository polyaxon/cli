"""PQL Grammar using parsimonious.

This module defines the PQL grammar for parsing boolean queries with AND/OR
operators and parentheses grouping.

Grammar design:
- AND operators: `,` or `AND` keyword (case-insensitive)
- OR operators: `OR` keyword or `|` with whitespace (case-insensitive)
- Parentheses for grouping: `(` and `)`
- Expressions: `field:operation` where operation can contain `|` for IN operator

Operator precedence: AND binds tighter than OR (standard boolean precedence)

Examples:
    "status:running"
    "status:running, metrics.loss:<0.5"
    "status:running AND metrics.loss:<0.5"
    "status:running OR status:failed"
    "(status:running AND metrics.loss:<0.5) OR status:failed"
    "status:running|building"  # `|` is IN operator, not OR
"""

from typing import List, Union

from parsimonious.grammar import Grammar
from parsimonious.nodes import Node, NodeVisitor

from polyaxon._pql.ast import AndNode, ASTNode, ExpressionNode, OrNode

# PQL Grammar Definition
# Note: Order matters in PEG grammars - more specific rules must come first
PQL_GRAMMAR = Grammar(
    r"""
    query           = ws or_expr ws

    or_expr         = and_expr (or_op and_expr)*
    and_expr        = primary (and_op primary)*

    primary         = group / expression
    group           = "(" ws or_expr ws ")"

    expression      = field ws ":" ws operation

    field           = ~r"[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?"

    operation       = ~r"[^,()]+?(?=\s*(,|\s+AND\s|\s+AND$|\s+OR\s|\s+OR$|\s+\|\s+(\(|[a-zA-Z_][a-zA-Z0-9_.]*:)|\)|\s*$))"i

    or_op           = ws (or_keyword / pipe_or) ws
    or_keyword      = ~r"OR"i
    pipe_or         = "|" &(ws ("(" / ~r"[a-zA-Z_][a-zA-Z0-9_.]*:"))

    and_op          = ws (and_keyword / comma) ws
    and_keyword     = ~r"AND"i
    comma           = ","

    ws              = ~r"\s*"
    """
)


class PQLVisitor(NodeVisitor):
    """Visitor that transforms the parse tree into an AST."""

    def visit_query(self, node: Node, visited_children: List) -> ASTNode:
        """Visit the root query node."""
        _, expr, _ = visited_children
        return expr

    def visit_or_expr(self, node: Node, visited_children: List) -> ASTNode:
        """Visit OR expression - combines children with OrNode if multiple."""
        first, rest = visited_children
        if not rest:
            return first

        # Flatten into list of children
        children = [first]
        for item in rest:
            # item is [or_op, and_expr]
            children.append(item[1])

        if len(children) == 1:
            return children[0]
        return OrNode(children)

    def visit_and_expr(self, node: Node, visited_children: List) -> ASTNode:
        """Visit AND expression - combines children with AndNode if multiple."""
        first, rest = visited_children
        if not rest:
            return first

        # Flatten into list of children
        children = [first]
        for item in rest:
            # item is [and_op, primary]
            children.append(item[1])

        if len(children) == 1:
            return children[0]
        return AndNode(children)

    def visit_primary(self, node: Node, visited_children: List) -> ASTNode:
        """Visit primary - either a group or expression."""
        return visited_children[0]

    def visit_group(self, node: Node, visited_children: List) -> ASTNode:
        """Visit group - extract the inner expression."""
        _, _, expr, _, _ = visited_children
        return expr

    def visit_expression(self, node: Node, visited_children: List) -> ExpressionNode:
        """Visit expression - create ExpressionNode from field:operation."""
        # expression = field ws ":" ws operation
        field, _, _, _, operation = visited_children
        return ExpressionNode(field.strip(), operation.strip())

    def visit_field(self, node: Node, visited_children: List) -> str:
        """Visit field - return the field name."""
        return node.text

    def visit_operation(self, node: Node, visited_children: List) -> str:
        """Visit operation - return the operation string."""
        return node.text

    def generic_visit(self, node: Node, visited_children: List) -> Union[List, str]:
        """Generic visitor for nodes we don't explicitly handle."""
        return visited_children or node.text


def parse_query(query: str) -> ASTNode:
    """Parse a PQL query string into an AST.

    Args:
        query: The PQL query string

    Returns:
        The root AST node representing the query

    Raises:
        ParseError: If the query is syntactically invalid
    """
    tree = PQL_GRAMMAR.parse(query)
    visitor = PQLVisitor()
    return visitor.visit(tree)
