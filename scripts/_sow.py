import json
v = json.load(open('data/sow.json'))['vscs']
for k, val in v.items():
    if isinstance(val, list):
        print(f"{k}: {len(val)} rows")
        for r in val[:4]:
            print("   ", json.dumps(r))
    else:
        print(f"{k}: {val}")
