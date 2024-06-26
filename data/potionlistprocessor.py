import json, re

with open("potionlist.txt", "r") as f:
    lst = f.read().split("\n")
    jsonn = {}
    pattern = r'\bIcon\s+\w+'
    pattern2 = r'\(SacredBark.*?\)'
    for x in lst:
        if x and len(x.split("\t")) > 1:
            l = x.split("\t")
            g = l[2]
            g = re.sub(pattern, '', g)
            g = re.sub(pattern2, '', g)
            g = g.replace("  ", " ")
            g = g.replace("  ", " ")
            if l[0] in jsonn:
                print(f"Duplicate potion: {l[0]}")
            jsonn[l[0]] = g

with open("potionlist.json", "w") as f:
    f.write(json.dumps(jsonn, indent=4))