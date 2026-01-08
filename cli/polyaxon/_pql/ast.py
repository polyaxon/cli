"""AST (Abstract Syntax Tree) representation for PQL boolean expressions.

This module provides AST node types to represent complex boolean queries
with AND/OR operators and parentheses grouping.

Example:
    Query: "status:running AND (tags:ml OR metrics.loss:<0.5)"
    AST:
        AndNode([
            ExpressionNode("status", "running"),
            OrNode([
                ExpressionNode("tags", "ml"),
                ExpressionNode("metrics.loss", "<0.5")
            ])
        ])
"""

from typing import Any, List, Union


class ASTNode:
    """Base class for all AST nodes."""

    pass


class ExpressionNode(ASTNode):
    """Represents a single field:operation expression.

    Attributes:
        field: The field name (e.g., "status", "metrics.loss")
        operation: The operation string (e.g., "running", "<0.5", "~tag1|tag2")
    """

    def __init__(self, field: str, operation: str):
        self.field = field
        self.operation = operation

    def __repr__(self) -> str:
        return f"ExpressionNode({self.field!r}, {self.operation!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ExpressionNode):
            return False
        return self.field == other.field and self.operation == other.operation


class AndNode(ASTNode):
    """Represents an AND combination of AST nodes.

    Attributes:
        children: List of child AST nodes to be ANDed together
    """

    def __init__(self, children: List[ASTNode]):
        self.children = children

    def __repr__(self) -> str:
        return f"AndNode({self.children!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, AndNode):
            return False
        return self.children == other.children


class OrNode(ASTNode):
    """Represents an OR combination of AST nodes.

    Attributes:
        children: List of child AST nodes to be ORed together
    """

    def __init__(self, children: List[ASTNode]):
        self.children = children

    def __repr__(self) -> str:
        return f"OrNode({self.children!r})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, OrNode):
            return False
        return self.children == other.children


# Type alias for any AST node
QueryAST = Union[ExpressionNode, AndNode, OrNode]
