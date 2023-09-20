from polyaxon._contexts import keys

INPUTS = "inputs"
OUTPUTS = "outputs"
INPUTS_OUTPUTS = "io"
ARTIFACTS = "artifacts"
GLOBALS = "globals"

CONTEXTS = {
    INPUTS,
    OUTPUTS,
    INPUTS_OUTPUTS,
    ARTIFACTS,
}
CONTEXTS_WITH_NESTING = {
    INPUTS,
    OUTPUTS,
    ARTIFACTS,
    GLOBALS,
}
GLOBALS_CONTEXTS = {
    keys.OWNER_NAME,
    keys.PROJECT_NAME,
    keys.PROJECT_UNIQUE_NAME,
    keys.PROJECT_UUID,
    keys.RUN_INFO,
    keys.NAME,
    keys.UUID,
    keys.STATUS,
    keys.NAMESPACE,
    keys.ITERATION,
    keys.CONTEXT_PATH,
    keys.ARTIFACTS_PATH,
    keys.CREATED_AT,
    keys.COMPILED_AT,
    keys.SCHEDULE_AT,
    keys.STARTED_AT,
    keys.FINISHED_AT,
    keys.DURATION,
    keys.CLONING_KIND,
    keys.ORIGINAL_UUID,
    keys.IS_INDEPENDENT,
}
