import json

with open('template_dump.json', 'r', encoding='utf-8') as f:
    slides = json.load(f)

for s in slides:
    print(f"\n================ SLIDE {s['slide_index']} ================")
    for sh in s['shapes']:
        name = sh['name']
        stype = sh['type']
        if 'paragraphs' in sh and sh['paragraphs']:
            texts = [p['text'].strip() for p in sh['paragraphs'] if p['text'].strip()]
            if texts:
                runs = sh['paragraphs'][0]['runs']
                font_info = f"{runs[0].get('font_name')}, {runs[0].get('font_size')}pt, #{runs[0].get('color')}" if runs else "default"
                print(f"  Shape '{name}' ({stype}) [Font: {font_info}]:")
                for t in texts:
                    print(f"    - {t[:120]}")
        elif 'table' in sh:
            print(f"  Shape '{name}' (TABLE):")
            for row in sh['table']:
                print(f"    - {' | '.join(row)}")
        else:
            print(f"  Shape '{name}' ({stype}) [No text]")
