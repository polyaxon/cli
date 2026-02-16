from functools import reduce
from operator import and_, or_
from typing import Any, Dict, Iterable, List, Optional, Tuple

from polyaxon._pql.ast import AndNode, ASTNode, ExpressionNode, OrNode
from polyaxon._pql.builder import QueryCondSpec
from polyaxon._pql.grammar import parse_query
from polyaxon._pql.parser import parse_field, tokenize_query
from polyaxon.exceptions import PQLException


class LegacyQueryMixin:
    @classmethod
    def trans_field(
        cls,
        key: str,
        tokenized_query: Dict[str, Iterable],
        update_tokenized_query: Dict[str, Iterable],
    ):
        """[Legacy] Transform field names for the tokenized query.

        This is part of the legacy tokenize/parse/build pipeline.
        Used by tokenize() and apply_legacy().

        Args:
            key: The field key to transform
            tokenized_query: The source tokenized query dict
            update_tokenized_query: The target dict to update with transformed fields
        """
        field, suffix = parse_field(key)
        if field in cls.FIELDS_TRANS:
            field_trans = cls.FIELDS_TRANS[field]["field"]
            update_tokenized_query["{}_value".format(field_trans)] = tokenized_query[
                key
            ]
            update_tokenized_query["{}_name".format(field_trans)] = [suffix]
            if cls.FIELDS_TRANS[field].get("type"):
                update_tokenized_query[
                    "{}_type".format(field_trans)
                ] = cls.FIELDS_TRANS[field]["type"]  # fmt: skip
        else:
            update_tokenized_query[key] = tokenized_query[key]

    @classmethod
    def tokenize(cls, query_spec: str) -> Dict[str, Iterable]:
        """[Legacy] Tokenize a query string into field:operation mappings.

        This is part of the legacy tokenize/parse/build pipeline.
        Only supports AND (comma-separated) queries.

        Args:
            query_spec: The PQL query string

        Returns:
            Dict mapping field names to lists of operation strings
        """
        tokenized_query = tokenize_query(query_spec, default=cls.DEFAULT_FILTERS)
        results = {}
        for key in tokenized_query.keys():
            field, _ = parse_field(key)
            if field and (
                field not in cls.PARSERS_BY_FIELD
                or field not in cls.CONDITIONS_BY_FIELD
            ):
                raise PQLException(
                    "key `{}` is not supported by the query manager `{}`.".format(
                        key, cls.NAME
                    )
                )
            cls.trans_field(key, tokenized_query, results)

        return results

    @classmethod
    def parse(cls, tokenized_query: Dict[str, Iterable]) -> Dict[str, Iterable]:
        """[Legacy] Parse tokenized query into QueryOpSpec objects.

        This is part of the legacy tokenize/parse/build pipeline.
        Only supports AND (comma-separated) queries.

        Args:
            tokenized_query: Dict from tokenize() method

        Returns:
            Dict mapping field names to lists of QueryOpSpec objects
        """
        parsed_query = {}
        for key, expressions in tokenized_query.items():
            field, _ = parse_field(key)
            parsed_query[key] = [
                cls.PARSERS_BY_FIELD[field](exp) for exp in expressions
            ]
        return parsed_query

    @classmethod
    def build(cls, parsed_query: Dict[str, Iterable]) -> Dict[str, Iterable]:
        """[Legacy] Build query conditions from parsed query.

        This is part of the legacy tokenize/parse/build pipeline.
        Only supports AND (comma-separated) queries.

        Args:
            parsed_query: Dict from parse() method

        Returns:
            Dict mapping field names to lists of QueryCondSpec objects
        """
        built_query = {}
        for key, operations in parsed_query.items():
            field, _ = parse_field(key)
            built_query[key] = [
                QueryCondSpec(
                    cond=cls.CONDITIONS_BY_FIELD[field](
                        op=op_spec.op, negation=op_spec.negation
                    ),
                    params=op_spec.params,
                )
                for op_spec in operations
            ]
        return built_query

    @classmethod
    def handle_query(cls, query_spec: str) -> Dict[str, Iterable]:
        """[Legacy] Process a query through the tokenize/parse/build pipeline.

        This is the entry point for the legacy query processing pipeline.
        Only supports AND (comma-separated) queries.

        Args:
            query_spec: The PQL query string

        Returns:
            Dict mapping field names to lists of QueryCondSpec objects
        """
        tokenized_query = cls.tokenize(query_spec=query_spec)
        parsed_query = cls.parse(tokenized_query=tokenized_query)
        built_query = cls.build(parsed_query=parsed_query)
        return built_query

    @classmethod
    def apply_legacy(
        cls, query_spec: str, queryset: Any, request: Optional[Any] = None
    ) -> Any:
        """Legacy apply method using the old tokenize/parse/build pipeline.

        This method only supports AND (comma-separated) queries.
        Kept for backward compatibility and testing.

        Args:
            query_spec: The PQL query string
            queryset: The Django queryset to filter
            request: Optional request for callback conditions

        Returns:
            Filtered queryset
        """
        built_query = cls.handle_query(query_spec=query_spec)
        operators = []
        trigger_distinct = False
        for key, cond_specs in built_query.items():
            key = cls.proxy_field(key)
            if not trigger_distinct:
                trigger_distinct = cls.trigger_distinct(key)
            for cond_spec in cond_specs:
                try:
                    operator = cond_spec.cond.apply_operator(
                        name=key,
                        params=cond_spec.params,
                        query_backend=cls.QUERY_BACKEND,
                        timezone=cls.TIMEZONE,
                        request=request,
                    )
                except Exception as e:
                    raise PQLException(
                        "Error applying operator for key `%s` by the query manager `%s`. "
                        "%s" % (key, cls.NAME, e)
                    )
                if operator:
                    operators.append(operator)

        queryset = queryset.filter(*operators)
        if trigger_distinct:
            queryset = queryset.distinct()
        return queryset


class PQLManager:
    """PQL Manager using AST-based parsing for full boolean expression support."""

    NAME = None
    FIELDS_USE_UUID = None
    FIELDS_USE_STATE = None
    FIELDS_USE_NAME = None
    FIELDS_PROXY = {}
    FIELDS_TRANS = {}
    FIELDS_ORDERING = None
    FIELDS_ORDERING_PROXY = None  # Do not set a field on both field and proxy
    FIELDS_DEFAULT_ORDERING = None
    FIELDS_DISTINCT = None
    CHECK_ALIVE = True
    PARSERS_BY_FIELD = {}
    CONDITIONS_BY_FIELD = {}
    DEFAULT_FILTERS = {}
    QUERY_BACKEND = None
    TIMEZONE = None

    @classmethod
    def proxy_field(cls, field: str) -> str:
        field, suffix = parse_field(field)
        if field in cls.FIELDS_PROXY:
            field = cls.FIELDS_PROXY[field]
        if cls.FIELDS_USE_UUID and not suffix and field in cls.FIELDS_USE_UUID:
            suffix = "uuid"
        if cls.FIELDS_USE_UUID and field in cls.FIELDS_USE_UUID and suffix == "id":
            suffix = "uuid"
        if cls.FIELDS_USE_STATE and not suffix and field in cls.FIELDS_USE_STATE:
            suffix = "state"
        if cls.FIELDS_USE_STATE and field in cls.FIELDS_USE_STATE and suffix == "id":
            suffix = "state"
        if cls.FIELDS_USE_NAME and not suffix and field in cls.FIELDS_USE_NAME:
            suffix = "name"
        if cls.FIELDS_USE_NAME and field in cls.FIELDS_USE_NAME and suffix == "id":
            suffix = "name"
        return "{}__{}".format(field, suffix) if suffix else field

    @classmethod
    def trigger_distinct(cls, key: str):
        if cls.FIELDS_DISTINCT and key in cls.FIELDS_DISTINCT:
            return True
        return False

    @classmethod
    def apply(
        cls, query_spec: str, queryset: Any, request: Optional[Any] = None
    ) -> Any:
        """Apply a PQL query to a queryset.

        This method supports AND/OR operators and parentheses grouping.
        It uses AST-based parsing for full boolean expression support.

        Args:
            query_spec: The PQL query string
            queryset: The Django queryset to filter
            request: Optional request for callback conditions

        Returns:
            Filtered queryset
        """
        return cls.apply_ast(query_spec, queryset, request)

    @classmethod
    def _validate_field(cls, field: str) -> None:
        """Validate that a field is supported by this query manager."""
        base_field, _ = parse_field(field)
        if base_field and (
            base_field not in cls.PARSERS_BY_FIELD
            or base_field not in cls.CONDITIONS_BY_FIELD
        ):
            raise PQLException(
                "key `{}` is not supported by the query manager `{}`.".format(
                    field, cls.NAME
                )
            )

    @classmethod
    def _transform_expression(cls, field: str, operation: str) -> List[Tuple[str, str]]:
        """Transform a field:operation into potentially multiple transformed fields.

        Handles FIELDS_TRANS transformations that expand a single expression
        into multiple fields (e.g., metrics.loss -> outputs_value, outputs_name).

        Returns:
            List of (transformed_field, operation) tuples
        """
        base_field, suffix = parse_field(field)

        if base_field in cls.FIELDS_TRANS:
            trans_config = cls.FIELDS_TRANS[base_field]
            field_trans = trans_config["field"]
            result = [
                ("{}_value".format(field_trans), operation),
                ("{}_name".format(field_trans), suffix),
            ]
            if trans_config.get("type"):
                result.append(("{}_type".format(field_trans), trans_config["type"][0]))
            return result
        return [(field, operation)]

    @classmethod
    def _build_expression_q(
        cls,
        field: str,
        operation: str,
        request: Optional[Any] = None,
    ) -> Tuple[Any, bool]:
        """Build a Q object from a single field:operation expression.

        Args:
            field: The field name
            operation: The operation string
            request: Optional request for callback conditions

        Returns:
            Tuple of (Q object, trigger_distinct flag)
        """
        cls._validate_field(field)
        transformed = cls._transform_expression(field, operation)

        q_objects = []
        trigger_distinct = False

        for trans_field, trans_operation in transformed:
            base_field, _ = parse_field(trans_field)
            proxied_field = cls.proxy_field(trans_field)

            if not trigger_distinct:
                trigger_distinct = cls.trigger_distinct(proxied_field)

            # Parse the operation using the existing parser
            parser = cls.PARSERS_BY_FIELD[base_field]
            op_spec = parser(trans_operation)

            # Build the condition using the existing condition class
            condition_cls = cls.CONDITIONS_BY_FIELD[base_field]
            cond = condition_cls(op=op_spec.op, negation=op_spec.negation)

            try:
                q = cond.apply_operator(
                    name=proxied_field,
                    params=op_spec.params,
                    query_backend=cls.QUERY_BACKEND,
                    timezone=cls.TIMEZONE,
                    request=request,
                )
            except Exception as e:
                raise PQLException(
                    "Error applying operator for key `%s` by the query manager `%s`. "
                    "%s" % (trans_field, cls.NAME, e)
                )

            if q is not None:
                q_objects.append(q)

        # Combine multiple Q objects (from transforms) with AND
        if not q_objects:
            return None, trigger_distinct
        if len(q_objects) == 1:
            return q_objects[0], trigger_distinct
        return reduce(and_, q_objects), trigger_distinct

    @classmethod
    def _build_ast_q(
        cls,
        node: ASTNode,
        request: Optional[Any] = None,
    ) -> Tuple[Any, bool]:
        """Recursively build a Q object from an AST node.

        Args:
            node: The AST node (ExpressionNode, AndNode, or OrNode)
            request: Optional request for callback conditions

        Returns:
            Tuple of (Q object, trigger_distinct flag)
        """
        trigger_distinct = False

        if isinstance(node, ExpressionNode):
            if node.operation.strip() == "_any_":
                return None, False
            return cls._build_expression_q(node.field, node.operation, request)

        elif isinstance(node, AndNode):
            q_objects = []
            for child in node.children:
                q, distinct = cls._build_ast_q(child, request)
                trigger_distinct = trigger_distinct or distinct
                if q is not None:
                    q_objects.append(q)
            if not q_objects:
                return None, trigger_distinct
            if len(q_objects) == 1:
                return q_objects[0], trigger_distinct
            return reduce(and_, q_objects), trigger_distinct

        elif isinstance(node, OrNode):
            q_objects = []
            for child in node.children:
                q, distinct = cls._build_ast_q(child, request)
                trigger_distinct = trigger_distinct or distinct
                if q is not None:
                    q_objects.append(q)
            if not q_objects:
                return None, trigger_distinct
            if len(q_objects) == 1:
                return q_objects[0], trigger_distinct
            return reduce(or_, q_objects), trigger_distinct

        else:
            raise PQLException("Unknown AST node type: {}".format(type(node).__name__))

    @classmethod
    def _get_default_filters_q(
        cls,
        ast: ASTNode,
        request: Optional[Any] = None,
    ) -> Tuple[Optional[Any], bool]:
        """Build Q objects for default filters not already in the query.

        Default filters are applied unless the field is explicitly mentioned
        in the query or the special value '_any_' is used.

        Args:
            ast: The parsed AST
            request: Optional request for callback conditions

        Returns:
            Tuple of (Q object for defaults, trigger_distinct flag)
        """
        if not cls.DEFAULT_FILTERS:
            return None, False

        # Collect all fields mentioned in the AST
        mentioned_fields = set()

        def collect_fields(node: ASTNode) -> None:
            if isinstance(node, ExpressionNode):
                base_field, _ = parse_field(node.field)
                mentioned_fields.add(base_field)
                # Check for _any_ value which disables default
                if node.operation.strip() == "_any_":
                    mentioned_fields.add(node.field)
            elif isinstance(node, (AndNode, OrNode)):
                for child in node.children:
                    collect_fields(child)

        collect_fields(ast)

        # Build Q objects for defaults not in query
        q_objects = []
        trigger_distinct = False

        for field, default_value in cls.DEFAULT_FILTERS.items():
            base_field, _ = parse_field(field)
            if base_field not in mentioned_fields:
                q, distinct = cls._build_expression_q(field, default_value, request)
                trigger_distinct = trigger_distinct or distinct
                if q is not None:
                    q_objects.append(q)

        if not q_objects:
            return None, trigger_distinct
        if len(q_objects) == 1:
            return q_objects[0], trigger_distinct
        return reduce(and_, q_objects), trigger_distinct

    @classmethod
    def apply_ast(
        cls, query_spec: str, queryset: Any, request: Optional[Any] = None
    ) -> Any:
        """Apply a PQL query to a queryset using AST-based parsing.

        This method supports AND/OR operators and parentheses grouping.

        Args:
            query_spec: The PQL query string
            queryset: The Django queryset to filter
            request: Optional request for callback conditions

        Returns:
            Filtered queryset
        """
        # Parse query into AST
        try:
            ast = parse_query(query_spec)
        except Exception as e:
            raise PQLException("Failed to parse query `{}`: {}".format(query_spec, e))

        # Build Q from AST
        q, trigger_distinct = cls._build_ast_q(ast, request)

        # Add default filters
        default_q, default_distinct = cls._get_default_filters_q(ast, request)
        trigger_distinct = trigger_distinct or default_distinct

        # Combine query Q with default Q
        if q is not None and default_q is not None:
            final_q = q & default_q
        elif q is not None:
            final_q = q
        elif default_q is not None:
            final_q = default_q
        else:
            final_q = None

        # Apply to queryset
        if final_q is not None:
            queryset = queryset.filter(final_q)

        if trigger_distinct:
            queryset = queryset.distinct()

        return queryset
