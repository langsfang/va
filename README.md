
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
