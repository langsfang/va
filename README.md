
```bash
# fist time
uv init

uv run python agent/runner.py ../lib/ ../mods/ out/
```

## build sts_lightspeed
```bash
cd 3rd/sts_lightspeed

git submodule init
git submodule update

mkdir build
cd build
cmake .. -DCMAKE_POLICY_VERSION_MINIMUM=3.5
```

## todo

- in potion reward, add a request to LLM if slot is full
- combat:
    - ask llm to use a potion or not at the beginning
    - if search is -1, ask llm for an action(maybe here is better place to use potion?)
- add a dataset of combat to evaluate search abilities
