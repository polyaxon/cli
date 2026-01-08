from parsimonious.exceptions import IncompleteParseError, ParseError

from polyaxon._pql.ast import AndNode, ExpressionNode, OrNode
from polyaxon._pql.grammar import parse_query
from polyaxon._utils.test_utils import BaseTestCase


class TestGrammarInvalidQueries(BaseTestCase):
    """Test that invalid queries raise parse errors - mirrors TestParser pattern."""

    def test_raises_for_empty_query(self):
        """Empty queries should raise."""
        with self.assertRaises(ParseError):
            parse_query("")

        with self.assertRaises(ParseError):
            parse_query("   ")

    def test_raises_for_missing_colon(self):
        """Queries without colon should raise."""
        with self.assertRaises(ParseError):
            parse_query("foo")

        with self.assertRaises(ParseError):
            parse_query("status")

    def test_raises_for_missing_field(self):
        """Queries with missing field should raise."""
        with self.assertRaises(ParseError):
            parse_query(":bar")

        with self.assertRaises(ParseError):
            parse_query(":value")

    def test_raises_for_missing_value(self):
        """Queries with missing value should raise."""
        with self.assertRaises(ParseError):
            parse_query("foo:")

        with self.assertRaises(ParseError):
            parse_query("status:")

    def test_raises_for_just_colon(self):
        """Just a colon should raise."""
        with self.assertRaises(ParseError):
            parse_query(":")

    def test_raises_for_incomplete_and(self):
        """AND without following expression should raise."""
        with self.assertRaises(IncompleteParseError):
            parse_query("status:running AND")

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running AND   ")

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running, metrics:0.5 AND")

    def test_raises_for_incomplete_or(self):
        """OR without following expression should raise."""
        with self.assertRaises(IncompleteParseError):
            parse_query("status:running OR")

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running OR   ")

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running OR status:failed OR")

    def test_raises_for_incomplete_comma(self):
        """Comma without following expression should raise."""
        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("status:running,")

        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("status:running,   ")

    def test_raises_for_unmatched_open_paren(self):
        """Unmatched opening parenthesis should raise."""
        with self.assertRaises(ParseError):
            parse_query("(status:running")

        with self.assertRaises(ParseError):
            parse_query("((status:running)")

        with self.assertRaises(ParseError):
            parse_query("status:running AND (metrics:0.5")

    def test_raises_for_unmatched_close_paren(self):
        """Unmatched closing parenthesis should raise."""
        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("status:running)")

        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("(status:running))")

    def test_raises_for_empty_parens(self):
        """Empty parentheses should raise."""
        with self.assertRaises(ParseError):
            parse_query("()")

        with self.assertRaises(ParseError):
            parse_query("status:running AND ()")

    def test_raises_for_leading_and(self):
        """Leading AND should raise."""
        with self.assertRaises(ParseError):
            parse_query("AND status:running")

    def test_raises_for_leading_or(self):
        """Leading OR should raise."""
        with self.assertRaises(ParseError):
            parse_query("OR status:running")

    def test_raises_for_double_and(self):
        """Double AND should raise."""
        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("status:running AND AND metrics:0.5")

    def test_raises_for_double_or(self):
        """Double OR should raise."""
        with self.assertRaises((ParseError, IncompleteParseError)):
            parse_query("status:running OR OR status:failed")

    def test_raises_for_leading_comma(self):
        """Leading comma should raise."""
        with self.assertRaises(ParseError):
            parse_query(", status:running")

        with self.assertRaises(ParseError):
            parse_query(",status:running")


class TestGrammarValidQueries(BaseTestCase):
    """Test that valid queries parse correctly - mirrors TestParser pattern."""

    def test_simple_expressions(self):
        """Test various simple field:value expressions."""
        # Basic
        assert parse_query("foo:bar") == ExpressionNode("foo", "bar")
        assert parse_query("status:running") == ExpressionNode("status", "running")

        # With comparison operators
        assert parse_query("foo:>=bar") == ExpressionNode("foo", ">=bar")
        assert parse_query("metrics:<=0.5") == ExpressionNode("metrics", "<=0.5")
        assert parse_query("duration:>100") == ExpressionNode("duration", ">100")
        assert parse_query("count:<10") == ExpressionNode("count", "<10")

        # With IN operator (pipe without space)
        assert parse_query("foo:bar|moo|boo") == ExpressionNode("foo", "bar|moo|boo")
        assert parse_query("status:running|building") == ExpressionNode(
            "status", "running|building"
        )

        # With range operator
        assert parse_query("foo:bar..moo") == ExpressionNode("foo", "bar..moo")
        assert parse_query("created_at:2024-01-01..2024-12-31") == ExpressionNode(
            "created_at", "2024-01-01..2024-12-31"
        )

        # With negation
        assert parse_query("foo:~bar") == ExpressionNode("foo", "~bar")
        assert parse_query("status:~running") == ExpressionNode("status", "~running")

        # Value with colons (like times)
        assert parse_query("foo:bar:moo") == ExpressionNode("foo", "bar:moo")
        assert parse_query("started_at:10:30:00") == ExpressionNode(
            "started_at", "10:30:00"
        )

    def test_expressions_with_spaces(self):
        """Test that whitespace is handled correctly."""
        assert parse_query(" foo: bar ") == ExpressionNode("foo", "bar")
        assert parse_query("foo :>=bar ") == ExpressionNode("foo", ">=bar")
        assert parse_query(" foo :bar|moo|boo") == ExpressionNode("foo", "bar|moo|boo")
        assert parse_query(" foo : bar..moo ") == ExpressionNode("foo", "bar..moo")
        assert parse_query(" foo : ~bar ") == ExpressionNode("foo", "~bar")
        assert parse_query(" foo : some test in the description ") == ExpressionNode(
            "foo", "some test in the description"
        )

    def test_expressions_with_datetimes(self):
        """Test datetime expressions."""
        assert parse_query("started_at:2016-10-01 10:10") == ExpressionNode(
            "started_at", "2016-10-01 10:10"
        )
        assert parse_query(
            " started_at : ~ 2016-10-00 .. 2016-10-01 10:10:00 "
        ) == ExpressionNode("started_at", "~ 2016-10-00 .. 2016-10-01 10:10:00")

    def test_dotted_field_names(self):
        """Test dotted field names like metrics.loss."""
        assert parse_query("metrics.loss:0.5") == ExpressionNode("metrics.loss", "0.5")
        assert parse_query("metrics.accuracy:>0.9") == ExpressionNode(
            "metrics.accuracy", ">0.9"
        )
        assert parse_query("outputs.result:foo") == ExpressionNode(
            "outputs.result", "foo"
        )

    def test_and_with_comma(self):
        """Test AND using comma separator."""
        result = parse_query("name:~tag1 | tag2| tag23, name2:foo")
        assert isinstance(result, AndNode)
        assert len(result.children) == 2

        result = parse_query("name1:foo, name2:bar, name3:baz")
        assert isinstance(result, AndNode)
        assert len(result.children) == 3

    def test_and_with_keyword(self):
        """Test AND using AND keyword."""
        result = parse_query("status:running AND metrics:0.5")
        assert isinstance(result, AndNode)
        assert len(result.children) == 2

        # Case insensitive
        result = parse_query("status:running and metrics:0.5")
        assert isinstance(result, AndNode)

        result = parse_query("status:running And metrics:0.5")
        assert isinstance(result, AndNode)

    def test_or_with_keyword(self):
        """Test OR using OR keyword."""
        result = parse_query("status:running OR status:failed")
        assert isinstance(result, OrNode)
        assert len(result.children) == 2

        # Case insensitive
        result = parse_query("status:running or status:failed")
        assert isinstance(result, OrNode)

        result = parse_query("status:running Or status:failed")
        assert isinstance(result, OrNode)

    def test_or_with_pipe_and_field(self):
        """Test OR using pipe followed by field:value."""
        result = parse_query("status:running | status:failed")
        assert isinstance(result, OrNode)
        assert len(result.children) == 2

    def test_pipe_without_field_is_in_operator(self):
        """Test that pipe followed by non-field is IN operator."""
        # This should be IN, not OR
        result = parse_query("kind:host_path | s3")
        assert isinstance(result, ExpressionNode)
        assert result.operation == "host_path | s3"

        # With comma
        result = parse_query("kind:host_path | s3, live_state:1")
        assert isinstance(result, AndNode)
        assert result.children[0].operation == "host_path | s3"

    def test_parentheses_grouping(self):
        """Test parentheses for grouping."""
        result = parse_query("(status:running)")
        assert isinstance(result, ExpressionNode)

        result = parse_query("(status:running OR status:failed)")
        assert isinstance(result, OrNode)

        result = parse_query("(status:running AND metrics:0.5)")
        assert isinstance(result, AndNode)

    def test_nested_parentheses(self):
        """Test nested parentheses."""
        result = parse_query("a:1, (b:2 | (c:3 AND d:4))")
        assert isinstance(result, AndNode)
        assert isinstance(result.children[1], OrNode)
        assert isinstance(result.children[1].children[1], AndNode)

    def test_operator_precedence(self):
        """Test that AND binds tighter than OR."""
        # a:1 AND b:2 OR c:3 should be (a:1 AND b:2) OR c:3
        result = parse_query("a:1 AND b:2 OR c:3")
        assert isinstance(result, OrNode)
        assert isinstance(result.children[0], AndNode)
        assert isinstance(result.children[1], ExpressionNode)


class TestPQLGrammar(BaseTestCase):
    """Tests for the PQL grammar parsing."""

    def test_simple_expression(self):
        """Test parsing a single expression."""
        result = parse_query("status:running")
        assert result == ExpressionNode("status", "running")

    def test_expression_with_dotted_field(self):
        """Test parsing expressions with dotted field names."""
        result = parse_query("metrics.loss:0.5")
        assert result == ExpressionNode("metrics.loss", "0.5")

        result = parse_query("metrics.accuracy:>0.9")
        assert result == ExpressionNode("metrics.accuracy", ">0.9")

    def test_expression_with_negation(self):
        """Test parsing expressions with negation modifier."""
        result = parse_query("status:~running")
        assert result == ExpressionNode("status", "~running")

    def test_expression_with_comparison(self):
        """Test parsing expressions with comparison operators."""
        result = parse_query("metrics.loss:<0.5")
        assert result == ExpressionNode("metrics.loss", "<0.5")

        result = parse_query("metrics.loss:<=0.5")
        assert result == ExpressionNode("metrics.loss", "<=0.5")

        result = parse_query("metrics.loss:>0.5")
        assert result == ExpressionNode("metrics.loss", ">0.5")

        result = parse_query("metrics.loss:>=0.5")
        assert result == ExpressionNode("metrics.loss", ">=0.5")

    def test_expression_with_range(self):
        """Test parsing expressions with range operator."""
        result = parse_query("created_at:2024-01-01..2024-12-31")
        assert result == ExpressionNode("created_at", "2024-01-01..2024-12-31")

    def test_expression_with_search(self):
        """Test parsing expressions with search patterns."""
        result = parse_query("name:%foo%")
        assert result == ExpressionNode("name", "%foo%")

        result = parse_query("name:foo%")
        assert result == ExpressionNode("name", "foo%")

        result = parse_query("name:%foo")
        assert result == ExpressionNode("name", "%foo")

    def test_expression_with_in_operator(self):
        """Test parsing expressions with IN operator (pipe without space)."""
        result = parse_query("status:running|building")
        assert result == ExpressionNode("status", "running|building")

        result = parse_query("tags:ml|ai|deep-learning")
        assert result == ExpressionNode("tags", "ml|ai|deep-learning")

    def test_expression_with_in_operator_with_spaces(self):
        """Test that pipe followed by non-field is IN operator, not OR."""
        # Pipe followed by value (no colon) should be IN, not OR
        result = parse_query("kind:host_path | s3")
        assert result == ExpressionNode("kind", "host_path | s3")

        # With additional AND expression
        result = parse_query("kind:host_path | s3,live_state:1")
        assert result == AndNode(
            [
                ExpressionNode("kind", "host_path | s3"),
                ExpressionNode("live_state", "1"),
            ]
        )

        # Pipe followed by field:value should still be OR
        result = parse_query("kind:host_path | kind:s3")
        assert result == OrNode(
            [
                ExpressionNode("kind", "host_path"),
                ExpressionNode("kind", "s3"),
            ]
        )

    def test_expression_with_negated_in(self):
        """Test parsing expressions with negated IN operator."""
        result = parse_query("status:~running|building")
        assert result == ExpressionNode("status", "~running|building")

    def test_and_with_comma(self):
        """Test parsing AND using comma."""
        result = parse_query("status:running, metrics.loss:<0.5")
        assert result == AndNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("metrics.loss", "<0.5"),
            ]
        )

    def test_and_with_keyword(self):
        """Test parsing AND using AND keyword."""
        result = parse_query("status:running AND metrics.loss:<0.5")
        assert result == AndNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("metrics.loss", "<0.5"),
            ]
        )

    def test_and_keyword_case_insensitive(self):
        """Test that AND keyword is case-insensitive."""
        result1 = parse_query("status:running AND metrics.loss:<0.5")
        result2 = parse_query("status:running and metrics.loss:<0.5")
        result3 = parse_query("status:running And metrics.loss:<0.5")

        expected = AndNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("metrics.loss", "<0.5"),
            ]
        )
        assert result1 == expected
        assert result2 == expected
        assert result3 == expected

    def test_or_with_keyword(self):
        """Test parsing OR using OR keyword."""
        result = parse_query("status:running OR status:failed")
        assert result == OrNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("status", "failed"),
            ]
        )

    def test_or_keyword_case_insensitive(self):
        """Test that OR keyword is case-insensitive."""
        result1 = parse_query("status:running OR status:failed")
        result2 = parse_query("status:running or status:failed")
        result3 = parse_query("status:running Or status:failed")

        expected = OrNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("status", "failed"),
            ]
        )
        assert result1 == expected
        assert result2 == expected
        assert result3 == expected

    def test_or_with_pipe(self):
        """Test parsing OR using pipe with whitespace."""
        result = parse_query("status:running | status:failed")
        assert result == OrNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("status", "failed"),
            ]
        )

    def test_parentheses_grouping(self):
        """Test parsing with parentheses grouping."""
        result = parse_query("(status:running OR status:failed)")
        assert result == OrNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("status", "failed"),
            ]
        )

    def test_mixed_and_or(self):
        """Test parsing mixed AND/OR (AND binds tighter)."""
        result = parse_query("status:running AND metrics.loss:<0.5 OR status:failed")
        # AND binds tighter: (status:running AND metrics.loss:<0.5) OR status:failed
        assert result == OrNode(
            [
                AndNode(
                    [
                        ExpressionNode("status", "running"),
                        ExpressionNode("metrics.loss", "<0.5"),
                    ]
                ),
                ExpressionNode("status", "failed"),
            ]
        )

    def test_mixed_with_grouping(self):
        """Test parsing mixed AND/OR with explicit grouping."""
        result = parse_query("(status:running AND metrics.loss:<0.5) OR status:failed")
        assert result == OrNode(
            [
                AndNode(
                    [
                        ExpressionNode("status", "running"),
                        ExpressionNode("metrics.loss", "<0.5"),
                    ]
                ),
                ExpressionNode("status", "failed"),
            ]
        )

    def test_nested_grouping(self):
        """Test parsing with nested parentheses."""
        result = parse_query(
            "project:ml, (status:running | (created_at:>2024-01-01 AND metrics.accuracy:>0.9))"
        )
        assert result == AndNode(
            [
                ExpressionNode("project", "ml"),
                OrNode(
                    [
                        ExpressionNode("status", "running"),
                        AndNode(
                            [
                                ExpressionNode("created_at", ">2024-01-01"),
                                ExpressionNode("metrics.accuracy", ">0.9"),
                            ]
                        ),
                    ]
                ),
            ]
        )

    def test_multiple_and(self):
        """Test parsing multiple AND expressions."""
        result = parse_query("a:1, b:2, c:3")
        assert result == AndNode(
            [
                ExpressionNode("a", "1"),
                ExpressionNode("b", "2"),
                ExpressionNode("c", "3"),
            ]
        )

    def test_multiple_or(self):
        """Test parsing multiple OR expressions."""
        result = parse_query("a:1 OR b:2 OR c:3")
        assert result == OrNode(
            [
                ExpressionNode("a", "1"),
                ExpressionNode("b", "2"),
                ExpressionNode("c", "3"),
            ]
        )

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result = parse_query("  status:running  ")
        assert result == ExpressionNode("status", "running")

        result = parse_query("status:running  ,  metrics.loss:<0.5")
        assert result == AndNode(
            [
                ExpressionNode("status", "running"),
                ExpressionNode("metrics.loss", "<0.5"),
            ]
        )

    def test_nil_operation(self):
        """Test parsing nil operation."""
        result = parse_query("status:nil")
        assert result == ExpressionNode("status", "nil")

        result = parse_query("status:~nil")
        assert result == ExpressionNode("status", "~nil")

    def test_complex_real_world_query(self):
        """Test a complex real-world query."""
        query = "(status:running OR status:building) AND metrics.loss:<0.5 AND created_at:>2024-01-01"
        result = parse_query(query)
        expected = AndNode(
            [
                OrNode(
                    [
                        ExpressionNode("status", "running"),
                        ExpressionNode("status", "building"),
                    ]
                ),
                ExpressionNode("metrics.loss", "<0.5"),
                ExpressionNode("created_at", ">2024-01-01"),
            ]
        )
        assert result == expected

    def test_incomplete_and_raises_error(self):
        """Test that incomplete AND query raises parse error."""
        from parsimonious.exceptions import IncompleteParseError

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running AND")

    def test_incomplete_or_raises_error(self):
        """Test that incomplete OR query raises parse error."""
        from parsimonious.exceptions import IncompleteParseError

        with self.assertRaises(IncompleteParseError):
            parse_query("status:running OR")

    def test_unmatched_paren_raises_error(self):
        """Test that unmatched parenthesis raises parse error."""
        from parsimonious.exceptions import ParseError

        with self.assertRaises(ParseError):
            parse_query("(status:running")

    def test_missing_colon_raises_error(self):
        """Test that missing colon raises parse error."""
        from parsimonious.exceptions import ParseError

        with self.assertRaises(ParseError):
            parse_query("status")


class TestASTNodes(BaseTestCase):
    """Tests for AST node classes."""

    def test_expression_node_equality(self):
        """Test ExpressionNode equality."""
        node1 = ExpressionNode("status", "running")
        node2 = ExpressionNode("status", "running")
        node3 = ExpressionNode("status", "failed")

        assert node1 == node2
        assert node1 != node3

    def test_and_node_equality(self):
        """Test AndNode equality."""
        node1 = AndNode([ExpressionNode("a", "1"), ExpressionNode("b", "2")])
        node2 = AndNode([ExpressionNode("a", "1"), ExpressionNode("b", "2")])
        node3 = AndNode([ExpressionNode("a", "1")])

        assert node1 == node2
        assert node1 != node3

    def test_or_node_equality(self):
        """Test OrNode equality."""
        node1 = OrNode([ExpressionNode("a", "1"), ExpressionNode("b", "2")])
        node2 = OrNode([ExpressionNode("a", "1"), ExpressionNode("b", "2")])
        node3 = OrNode([ExpressionNode("a", "1")])

        assert node1 == node2
        assert node1 != node3

    def test_node_repr(self):
        """Test node __repr__ methods."""
        expr = ExpressionNode("status", "running")
        assert "ExpressionNode" in repr(expr)
        assert "status" in repr(expr)
        assert "running" in repr(expr)

        and_node = AndNode([expr])
        assert "AndNode" in repr(and_node)

        or_node = OrNode([expr])
        assert "OrNode" in repr(or_node)
