from polyaxon._flow import V1HpRange, V1MatrixKind, V1RunKind


def get_fxt_grid_with_inputs_outputs():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "run",
        "tags": ["key1", "value1"],
        "params": {"image": {"value": "test"}, "lr": {"value": 0.001}},
        "matrix": {
            "kind": V1MatrixKind.GRID,
            "params": {
                "param1": {"kind": "choice", "value": ["test1", "test2"]},
                "param2": V1HpRange(value=[1, 2, 1]).to_dict(),
            },
        },
        "component": {
            "name": "experiment-template",
            "description": "experiment to predict something",
            "tags": ["key", "value"],
            "inputs": [
                {"name": "lr", "type": "float", "value": 0.1, "isOptional": True},
                {"name": "image", "type": "str"},
                {"name": "param1", "type": "str", "argFormat": "value: {{ param1 }}"},
                {"name": "param2", "type": "int"},
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
                    "args": ["--lr={{ lr }}", "{{ params.param1.as_arg }}"],
                    "resources": {"requests": {"cpu": 1}},
                },
            },
        },
    }
