from typing import Any, Dict, Iterable, Optional

from polyaxon._pql.builder import QueryCondSpec
from polyaxon._pql.parser import parse_field, tokenize_query
from polyaxon.exceptions import PQLException


class PQLManager:
    NAME = None
    FIELDS_USE_UUID = None
    FIELDS_USE_STATE = None
    FIELDS_USE_NAME = None
    FIELDS_PROXY = {}
    FIELDS_TRANS = {}
    FIELDS_ORDERING = None
    FIELDS_ORDERING_PROXY = None
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
    def trans_field(
        cls,
        key: str,
        tokenized_query: Dict[str, Iterable],
        update_tokenized_query: Dict[str, Iterable],
    ):
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
                ] = cls.FIELDS_TRANS[field]["type"]
        else:
            update_tokenized_query[key] = tokenized_query[key]

    @classmethod
    def trigger_distinct(cls, key: str):
        if cls.FIELDS_DISTINCT and key in cls.FIELDS_DISTINCT:
            return True
        return False

    @classmethod
    def tokenize(cls, query_spec: str) -> Dict[str, Iterable]:
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
        parsed_query = {}
        for key, expressions in tokenized_query.items():
            field, _ = parse_field(key)
            parsed_query[key] = [
                cls.PARSERS_BY_FIELD[field](exp) for exp in expressions
            ]
        return parsed_query

    @classmethod
    def build(cls, parsed_query: Dict[str, Iterable]) -> Dict[str, Iterable]:
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
        tokenized_query = cls.tokenize(query_spec=query_spec)
        parsed_query = cls.parse(tokenized_query=tokenized_query)
        built_query = cls.build(parsed_query=parsed_query)
        return built_query

    @classmethod
    def apply(
        cls, query_spec: str, queryset: Any, request: Optional[Any] = None
    ) -> Any:
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
