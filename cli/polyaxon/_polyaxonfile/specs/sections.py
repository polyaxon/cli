class Sections:
    VERSION = "version"
    KIND = "kind"
    NAME = "name"
    COST = "cost"
    DESCRIPTION = "description"
    TAGS = "tags"
    IS_APPROVED = "isApproved"
    IS_PRESET = "isPreset"
    PRESETS = "presets"
    PATCH_STRATEGY = "patchStrategy"
    TEMPLATE = "template"
    QUEUE = "queue"
    CACHE = "cache"
    PLUGINS = "plugins"
    NAMESPACE = "namespace"
    BUILD = "build"
    HOOKS = "hooks"
    EVENTS = "events"
    TERMINATION = "termination"
    INPUTS = "inputs"
    OUTPUTS = "outputs"
    CONTEXTS = "contexts"
    PARAMS = "params"
    CONNECTIONS = "connections"
    RUN = "run"
    RUN_PATCH = "runPatch"
    MATRIX = "matrix"
    JOINS = "joins"
    OPERATIONS = "operations"
    COMPONENTS = "components"
    SCHEDULE = "schedule"
    DEPENDENCIES = "dependencies"
    TRIGGER = "trigger"
    CONDITIONS = "conditions"
    SKIP_ON_UPSTREAM_SKIP = "skipOnUpstreamSkip"
    HUB_REF = "hubRef"
    DAG_REF = "dagRef"
    PATH_REF = "pathRef"
    URL_REF = "urlRef"
    COMPONENT = "component"

    SECTIONS = (
        VERSION,
        KIND,
        NAME,
        COST,
        DESCRIPTION,
        TAGS,
        IS_APPROVED,
        PARAMS,
        IS_PRESET,
        PRESETS,
        PATCH_STRATEGY,
        TEMPLATE,
        CACHE,
        QUEUE,
        PLUGINS,
        NAMESPACE,
        BUILD,
        HOOKS,
        EVENTS,
        TERMINATION,
        CONNECTIONS,
        MATRIX,
        JOINS,
        OPERATIONS,
        SCHEDULE,
        DEPENDENCIES,
        TRIGGER,
        CONDITIONS,
        SKIP_ON_UPSTREAM_SKIP,
        HUB_REF,
        DAG_REF,
        PATH_REF,
        URL_REF,
        COMPONENT,
        INPUTS,
        OUTPUTS,
        CONTEXTS,
        RUN,
        RUN_PATCH,
    )

    PARSING_SECTIONS = (
        IS_APPROVED,
        MATRIX,
        PRESETS,
        COST,
        QUEUE,
        CACHE,
        CONNECTIONS,
        PLUGINS,
        NAMESPACE,
        TERMINATION,
        SCHEDULE,
        DEPENDENCIES,
        TRIGGER,
        CONDITIONS,
        SKIP_ON_UPSTREAM_SKIP,
        PATCH_STRATEGY,
    )

    REQUIRED_SECTIONS = (VERSION, KIND)
    OPERATORS = set([])

    # OPERATORS = {ForConfig.IDENTIFIER: ForConfig, IfConfig.IDENTIFIER: IfConfig}
