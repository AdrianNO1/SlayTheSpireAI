import json, re

with open("powerlist.txt", "r") as f:
    lst = f.read().split("\n")
    current_power = None
    jsonn = {}
    pattern = r'\bIcon\s+\w+'
    pattern2 = r'\[.*?\]'
    for x in lst:
        if x and len(x.split("\t")) > 1:
            l = x.split("\t")
            g = l[-2]
            g = re.sub(pattern, '', g)
            g = re.sub(pattern2, '', g)
            g = g.replace("  ", " ")
            if l[0] in jsonn:
                print(f"Duplicate power: {l[0]}")
            jsonn[l[1]] = g

with open("powerlist.json", "w") as f:
    f.write(json.dumps(jsonn, indent=4))