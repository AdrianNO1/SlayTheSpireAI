import json, re

with open("reliclist.txt", "r") as f:
    lst = f.read().split("\n")
    current_relic = None
    jsonn = {}
    for x in lst:
        if x:
            l = x.split("\t")
            g = l[-1]
            g = g.replace("[E]", "energy")
            g = g.replace("[R]", "energy")
            g = g.replace(" .", ".")
            g = g.replace("energy energy", "energy")
            if l[0] in jsonn:
                print(f"Duplicate relic: {l[0]}")
            jsonn[l[0]] = g

with open("reliclist.json", "w") as f:
    f.write(json.dumps(jsonn, indent=4))