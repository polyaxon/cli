from datetime import date, datetime
import pytest

from polyaxon._flow.io.io import V1IO
from polyaxon._polyaxonfile.specs.libs.engine import (
    render_name_template,
    render_template,
    render_text_strict,
)
from polyaxon._polyaxonfile.specs.libs.parser import TextValue
from polyaxon.exceptions import PolyaxonSchemaError


pytestmark = pytest.mark.polyaxonfile_mark


@pytest.mark.parametrize(
    "template",
    [
        "{{ ''.__class__ }}",
        "{{ ''['__class__'] }}",
        "{{ '' | attr('__class__') }}",
        "{{ ''.__class__.__name__ }}",
    ],
)
def test_rejects_internal_attributes(template):
    with pytest.raises(PolyaxonSchemaError):
        render_template(template, {})


def test_rejects_context_function_without_calling_it():
    called = []

    def callback():
        called.append(True)

    with pytest.raises(PolyaxonSchemaError):
        render_template("{{ callback() }}", {"callback": callback})
    assert called == []


@pytest.mark.parametrize(
    "template,context",
    [
        ("{{ values.append(3) }}", {"values": [1, 2]}),
        ("{{ values.update({'x': 2}) }}", {"values": {"x": 1}}),
        ("{{ clear() }}", {"clear": {"x": 1}.clear}),
        ("{{ '{}'.format(value) }}", {"value": "test"}),
        ("{{ formatter(value) }}", {"formatter": "{}".format, "value": "test"}),
        ("{% set formatter = '{}' | attr('format') %}{{ formatter('test') }}", {}),
    ],
)
def test_rejects_mutation_and_direct_formatting(template, context):
    with pytest.raises(PolyaxonSchemaError):
        render_template(template, context)


def test_rejects_mutation_without_changing_context():
    values = [1, 2]
    mapping = {"x": 1}
    for template in ("{{ values.append(3) }}", "{{ mapping.update({'x': 2}) }}"):
        with pytest.raises(PolyaxonSchemaError):
            render_template(template, {"values": values, "mapping": mapping})
    assert values == [1, 2]
    assert mapping == {"x": 1}


@pytest.mark.parametrize(
    "template,context,expected",
    [
        ("{{ missing }}", {}, ""),
        ("{{ ' ABC '.strip().lower() }}", {}, "abc"),
        ("{{ value.upper() }}", {"value": TextValue("hello")}, "HELLO"),
        ("{{ ','.join(['a', 'b']) }}", {}, "a,b"),
        ("{{ value.get('key') }}", {"value": {"key": "yes"}}, "yes"),
        ("{{ value.isoformat() }}", {"value": date(2026, 1, 2)}, "2026-01-02"),
        (
            "{{ value.strftime('%Y-%m-%d') }}",
            {"value": datetime(2026, 1, 2, 3, 4)},
            "2026-01-02",
        ),
        ("{{ '%s-%s' | format('a', 'b') }}", {}, "a-b"),
        ("{{ 'hello' | map_format('value=%s') }}", {}, "value=hello"),
        (
            "{{ 'hello' | map_format('value=%(item)s', 'item') }}",
            {},
            "value=hello",
        ),
        ("{{ range(3) | list }}", {}, "[0, 1, 2]"),
        ("{{ dict(a=1).get('a') }}", {}, "1"),
        (
            "{% set ns = namespace(total=0) %}"
            "{% for item in range(3) %}{% set ns.total = ns.total + item %}{% endfor %}"
            "{{ ns.total }}",
            {},
            "3",
        ),
        ("{% macro say(x) %}Hi {{ x }}{% endmacro %}{{ say('Jo') }}", {}, "Hi Jo"),
    ],
)
def test_supported_template_features(template, context, expected):
    assert render_template(template, context) == expected


def test_parsed_schema_values_support_fields_and_properties():
    repo = V1IO(name="repo", type="git").validate_value({"revision": "dev"})
    image = V1IO(name="image", type="dockerfile").validate_value({"image": "image:tag"})
    assert render_template("{{ repo.revision }}", {"repo": repo}) == "dev"
    assert render_template("{{ image.image_tag }}", {"image": image}) == "tag"


@pytest.mark.parametrize(
    "template,context",
    [
        ("{{ range(100001) | length }}", {}),
        ("{{ 2 ** 10000 }}", {}),
        ("{{ 2 ** power }}", {"power": 10000}),
        ("{{ (2 ** 4095) * 2 }}", {}),
        ("{{ 'x' * 100001 }}", {}),
        ("{{ 100001 * 'x' }}", {}),
        ("{{ [1] * count }}", {"count": 100001}),
    ],
)
def test_rejects_resource_guards(template, context):
    with pytest.raises(PolyaxonSchemaError):
        render_template(template, context)


@pytest.mark.parametrize(
    "template,expected",
    [
        ("{{ 2 ** 10 }}", "1024"),
        ("{{ (2 ** 4095) | string | length }}", "1233"),
        ("{{ ((2 ** 4094) * 2) | string | length }}", "1233"),
        ("{{ 2 ** -1 }}", "0.5"),
        ("{{ 0 ** 10000 }}", "0"),
        ("{{ 'x' * 3 }}", "xxx"),
        ("{{ 3 * 'x' }}", "xxx"),
        ("{{ 'x' * -1 }}", ""),
        ("{{ ('x' * 100000) | length }}", "100000"),
    ],
)
def test_allows_bounded_operations(template, expected):
    assert render_template(template, {}) == expected


@pytest.mark.parametrize(
    "template,context,expected",
    [
        (
            "train-{{ optimizer }}-{{ lr }}",
            {"optimizer": "adam", "lr": 0.01},
            "train-adam-0_01",
        ),
        (
            "{{ optimizer }} / {{ batch }}",
            {"optimizer": "adam", "batch": 32},
            "adam_32",
        ),
        ("-{{ value }}-", {"value": "experiment-a"}, "experiment-a"),
        # Param values are not rendered again
        ("run-{{ value }}", {"value": "{{ secret }}", "secret": "leak"}, "run-_secret"),
        ("{{ value }}", {"value": "a" * 128}, "a" * 128),
        # Longer names are cut to fit and end in `--`
        ("{{ value }}", {"value": "a" * 129}, "a" * 126 + "--"),
        ("{{ value }}", {"value": "a" * 125 + "-" + "b" * 9}, "a" * 125 + "--"),
        ("{{ range(3) | length }}", {}, "3"),
        ("{% set v = 'a' %}run-{{ v }}", {}, "run-a"),
        ("{{ cfg.missing | default('x') }}", {"cfg": {"a": 1}}, "x"),
    ],
)
def test_render_name_template(template, context, expected):
    assert render_name_template(template, context) == expected


def test_render_text_strict_keeps_text():
    assert render_text_strict("{{ value }}", {"value": "1e3"}, field="name") == "1e3"


@pytest.mark.parametrize(
    "template,context,message",
    [
        ("train-{{ lr }}", {}, "`name` uses unavailable variables: lr"),
        ("{{ lr | default('x') }}", {}, "unavailable variables: lr"),
        (
            "{% if lr is defined %}a{% else %}b{% endif %}",
            {},
            "unavailable variables: lr",
        ),
        ("{{ b }}-{{ a }}", {}, "unavailable variables: a, b"),
        ("{{ cfg.missing }}", {"cfg": {"a": 1}}, "has no attribute 'missing'"),
        ("train-{{ lr", {"lr": 1}, "Could not render `name`"),
        ("{{ lr | nope }}", {"lr": 1}, "Could not render `name`"),
        ("{{ ''.__class__ }}", {}, "Could not render `name`"),
        ("{{ 2 ** 10000 }}", {}, "Could not render `name`"),
        ("{{ 1 / 0 }}", {}, "Could not render `name`"),
        ("{{ value }}", {"value": ""}, "empty run name"),
        ("{{ value }}", {"value": " / ..."}, "empty run name"),
    ],
)
def test_render_name_template_errors(template, context, message):
    with pytest.raises(PolyaxonSchemaError, match=message):
        render_name_template(template, context)
