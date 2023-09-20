from polyaxon._flow import (
    V1HpRange,
    V1HpUniform,
    V1MatrixKind,
    V1Optimization,
    V1RunKind,
)


def get_fxt_bo_with_inputs_outputs(tuner=None):
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "run",
        "tags": ["key1", "value1"],
        "params": {"image": {"value": "test"}, "lr": {"value": 0.001}},
        "matrix": {
            "kind": V1MatrixKind.BAYES,
            "tuner": {"hubRef": tuner} if tuner else None,
            "numInitialRuns": 5,
            "maxIterations": 5,
            "metric": {"name": "loss", "optimization": V1Optimization.MINIMIZE},
            "params": {
                "param1": {"kind": "choice", "value": ["test1", "test2"]},
                "param2": V1HpRange(value=[1, 2, 1]).to_dict(),
                "param3": V1HpUniform(value=[0, 0.9]).to_dict(),
            },
        },
        "component": {
            "name": "experiment-template",
            "description": "experiment to predict something",
            "tags": ["key", "value"],
            "inputs": [
                {"name": "lr", "type": "float", "value": 0.1, "isOptional": True},
                {"name": "image", "type": "str"},
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
                {"name": "param3", "type": "float"},
            ],
            "outputs": [
                {"name": "result1", "type": "str"},
                {
                    "name": "result2",
                    "type": "str",
                    "isOptional": True,
                    "value": "{{ image }}",
                },
            ],
            "termination": {"maxRetries": 2},
            "run": {
                "kind": V1RunKind.JOB,
                "environment": {
                    "nodeSelector": {"polyaxon": "experiments"},
                    "serviceAccountName": "service",
                    "imagePullSecrets": ["secret1", "secret2"],
                },
                "container": {
                    "image": "{{ image }}",
                    "command": ["python3", "main.py"],
                    "args": "--lr={{ lr }}",
                    "resources": {"requests": {"cpu": 1}},
                },
            },
        },
    }


def get_fxt_bo_with_run_patch():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "params": {"image": {"value": "test"}},
        "matrix": {
            "kind": V1MatrixKind.BAYES,
            "numInitialRuns": 5,
            "maxIterations": 5,
            "metric": {"name": "loss", "optimization": V1Optimization.MINIMIZE},
            "params": {
                "param1": {"kind": "choice", "value": ["test1", "test2"]},
                "param2": V1HpRange(value=[1, 2, 1]).to_dict(),
                "param3": V1HpUniform(value=[0, 0.9]).to_dict(),
            },
        },
        "termination": {"maxRetries": 2},
        "runPatch": {
            "kind": V1RunKind.JOB,
            "environment": {
                "nodeSelector": {"polyaxon": "experiments"},
                "serviceAccountName": "service",
                "imagePullSecrets": ["secret1", "secret2"],
            },
        },
        "component": {
            "name": "experiment-template",
            "inputs": [
                {"name": "image", "type": "str"},
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
                {"name": "param3", "type": "float"},
            ],
            "tags": ["tag1", "tag2"],
            "run": {
                "kind": V1RunKind.JOB,
                "container": {"image": "{{ image }}"},
                "init": [{"connection": "foo", "git": {"revision": "dev"}}],
            },
        },
    }
