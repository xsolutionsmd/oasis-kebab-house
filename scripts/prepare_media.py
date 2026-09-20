"""Reproducible non-generative resizing of the restaurant's original images."""
from pathlib import Path
from PIL import Image,ImageOps
import hashlib,json,shutil
import subprocess
root=Path(__file__).resolve().parents[1]
source=root.parent/'research'/'assets'
target=root/'app'/'static'/'media'
target.mkdir(parents=True,exist_ok=True)
mapping={'platter':'CDFcEOjDS2g','interior':'CVsu8vdLwXW','samarkand':'CAtMtTmjMs0','samsa':'CVsvWw8L0YE','patio':'C9ApN0guIgQ','bread':'CAtMDuoDoN9','grill':'CcWhAdwrbpW','entrance':'CzfYlPdMIi-','shrimp':'CBPU9AxD6Uk','plov':'CzL_VFWLGnT'}
records=[]
for name,code in mapping.items():
    p=source/(code+'.jpg');im=ImageOps.exif_transpose(Image.open(p)).convert('RGB');im.thumbnail((1600,1600));out=target/(name+'.webp');im.save(out,'WEBP',quality=89,method=6)
    records.append(dict(file=out.name,source='https://www.instagram.com/p/'+code+'/',transformation='EXIF orientation, resize, WebP compression; no generated pixels',original_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
shutil.copyfile(source/'logo.png',target/'logo.png')
records.append(dict(file='logo.png',source='https://oasiskebabhouse.com/',transformation='Original logo, unchanged'))
(root/'docs'/'MEDIA_SOURCES.json').write_text(json.dumps(records,indent=2)+'\n')
video=source/'plov-original.mp4'
if video.exists() and video.stat().st_size>17000000:
    ffmpeg=shutil.which('ffmpeg') or 'C:/ffmpeg/bin/ffmpeg.exe'
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-ss','4','-i',str(video),'-t','28','-an','-vf','crop=720:990:0:0,scale=720:-2,fps=24','-c:v','libx264','-crf','27','-preset','medium','-movflags','+faststart','-y',str(target/'plov.mp4')],check=True)
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-ss','12','-i',str(video),'-vf','crop=720:990:0:0','-frames:v','1','-quality','90','-y',str(target/'plov.webp')],check=True)
    records=[r for r in records if r['file']!='plov.webp']
    for name in ('plov.mp4','plov.webp'):records.append(dict(file=name,source='https://www.instagram.com/p/C1z2xlPLGG9/',transformation='Original footage; fixed crop excludes bottom caption; silent 28-second video excerpt / poster frame at 12 seconds; no generated pixels',original_sha256=hashlib.sha256(video.read_bytes()).hexdigest()))
    (root/'docs'/'MEDIA_SOURCES.json').write_text(json.dumps(records,indent=2)+'\n')
print('Prepared',len(records),'authentic media assets')
