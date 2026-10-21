import sys
from PIL import Image, ImageDraw
names = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(f'preview/{n}.png') for n in names]
cols = 2
w = 640; hs = [im.height for im in ims]
rows = (len(ims)+cols-1)//cols
rowh = [max(hs[r*cols:(r+1)*cols]) + 22 for r in range(rows)]
sheet = Image.new('RGB', (cols*w + (cols+1)*10, sum(rowh)+10), (30,30,30))
d = ImageDraw.Draw(sheet); y = 10
for r in range(rows):
    for c in range(cols):
        i = r*cols+c
        if i >= len(ims): break
        x = 10 + c*(w+10)
        d.text((x, y), names[i], fill=(220,220,220))
        sheet.paste(ims[i], (x, y+14))
    y += rowh[r]
sheet.save(out)
