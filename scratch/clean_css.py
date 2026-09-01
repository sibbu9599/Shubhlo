import os

with open('static/master.css', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('\\n', '\n').replace('\\"', '"')
if c.startswith('"'):
    c = c[1:]
if c.endswith('"'):
    c = c[:-1]

with open('static/master.css', 'w', encoding='utf-8') as out:
    out.write(c)

print("Master CSS successfully cleaned!")
