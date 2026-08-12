import csv
with open("results_baseline_cot_forgery_no_tag_nemotron.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        print(f"--- SAMPLE {i} ---")
        print(f"IS_WEBSHELL: {row.get('is_webshell')}")
        print(f"REASONING:\n{row.get('reasoning')}")
        if i >= 2: break
