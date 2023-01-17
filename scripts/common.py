import json
import os
from functools import partial

open = partial(open, encoding="utf-8")


def ls(path):
    return [os.path.join(path, p) for p in os.listdir(path)]


def load_config(paths=["./config.json", "./config-default.json"]):
    cfgs = []
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, "r") as f:
            cfgs.append(json.load(f))
    final = cfgs[-1]
    for cfg in cfgs[:-1][::-1]:
        for key in cfg:
            final[key] = cfg[key]
    return final


if __name__ == "__main__":
    # Test
    print(load_config())