import json
with open("papers_metadata.jsonl",'a') as f, open("temp.json",'r') as f1:
    data = json.load(f1)
    for j in data:
        f.write(json.dumps(j, ensure_ascii=False)+'\n')
