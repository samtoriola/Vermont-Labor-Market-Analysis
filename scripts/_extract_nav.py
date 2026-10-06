"""Read the section ids and labels straight out of the views."""
import pathlib, re, json
V = pathlib.Path('components/views')
VIEWS = [('overview','Overview','Overview.js'), ('regions','Regions','Q7.js'),
         ('structure','Employment','Q1.js'), ('wage','Wage quality','Q2.js'),
         ('demand','Demand & growth','Q3.js'), ('pathways','Pathways','Q4.js'),
         ('opportunity','Opportunities','Q5.js'), ('alignment','VSCS alignment','Q6.js'),
         ('about','About','About.js'), ('methods','Methods','Methods.js')]
out = {}
for vid, label, fn in VIEWS:
    s = (V/fn).read_text(encoding='utf-8')
    items = re.findall(r"id: '([^']+)',\s*\n\s*label: '([^']*)'", s)
    out[vid] = {'label': label, 'items': [{'id': a, 'label': b} for a, b in items]}
    print(f"{vid:12s} {label:16s} {len(items)} sections")
    for a, b in items:
        print(f"              - {a:28s} {b}")
pathlib.Path('/tmp/nav.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print("\nwrote /tmp/nav.json")
