import json, re

#with open("data\\cardlist.txt", "r") as f:
#    lst = f.read().split("\n")
#    current_card = None
#    jsonn = {}
#    pattern = r'\(Obtained.*?\)'
#    pattern2 = r'\b Icon\s+\w+\b'
#    for x in lst:
#        if x:
#            if x.split("\t")[0] in ["Defend", "Strike", "Dagger Throw"] or len(x.split("\t")) > 1 and x.split("\t")[0].replace(" ", "").lower() == x.split("\t")[1].replace(" ", "").lower().strip("-0"):
#                if current_card:
#                    jsonn[current_card] = jsonn[current_card].replace("..", ".").strip()
#                current_card = x.split("\t")[0]
#                if current_card in jsonn and current_card not in ["Defend", "Strike"]:
#                    print("Duplicate card found:", current_card)
#                jsonn[current_card] = ""
#            else:
#                if x.count("\t") > 2:
#                    jsonn[current_card] += re.sub(pattern2, '', re.sub(pattern, '', x.split("\t")[-1] + "\n").strip())
#                else:
#                    jsonn[current_card] += re.sub(pattern2, '', re.sub(pattern, '', x + "\n").strip()).strip("Status\t")
#
#with open("data\\cardlist.json", "w") as f:
#    f.write(json.dumps(jsonn, indent=4))

# go through the json file and check if each key has an upgraded version of itself, if not create one with the same value as the original
with open("data\\cardlist.json", "r") as f:
    data = json.load(f)
    keys = list(data.keys())
    for k in keys:
        if "+" not in k and k + "+" not in data:
            data[k + "+"] = data[k]
                                   
with open("data\\cardlist.json", "w") as f:
    f.write(json.dumps(data, indent=4))