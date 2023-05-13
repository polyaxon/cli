def set_build_fixture(config, owner):
    config["build"] = {
        "params": {
            "context": {"value": "/path/context"},
        },
        "runPatch": {
            "init": [
                {
                    "git": {"revision": "branch2"},
                    "connection": "connection-repo",
                }
            ]
        },
        "hubRef": f"{owner}/kaniko",
    }
    return config
