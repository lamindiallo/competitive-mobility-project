"""Bundle the v2 site (generator sources + index-encoded inputs) into one xz tar, base64, split into chunks with SHA-1s."""
import json, io, tarfile, lzma, base64, hashlib, sys, os, subprocess
SRC, PACK, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
subprocess.run([sys.executable, '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pack_inputs.py'), PACK, OUT + '/inputs.json'], check=True)
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w') as t:
    for f in ['build.py', 'model.py', 'unpack.py', 'live.js', 'style.css', 'about.html.part', 'compare.html.part', 'live.html.part', 'corrections.html.part']:
        ti = t.gettarinfo(os.path.join(SRC, f), 'src/' + f); ti.mtime = 0; ti.uid = ti.gid = 0; ti.uname = ti.gname = ''
        t.addfile(ti, open(os.path.join(SRC, f), 'rb'))
    ti = t.gettarinfo(OUT + '/inputs.json', 'inputs.json'); ti.mtime = 0; ti.uid = ti.gid = 0; ti.uname = ti.gname = ''; t.addfile(ti, open(OUT + '/inputs.json', 'rb'))
raw = lzma.compress(buf.getvalue(), preset=9 | lzma.PRESET_EXTREME); b = base64.b64encode(raw).decode()
n = 8; k = -(-len(b) // n); sha = {}
for i in range(n):
    part = b[i * k:(i + 1) * k]; open(f'{OUT}/d{i}.b64', 'w').write(part); sha[f'd{i}.b64'] = hashlib.sha1(part.encode()).hexdigest()
json.dump(sha, open(f'{OUT}/chunks.json', 'w'), separators=(',', ':')); os.remove(OUT + '/inputs.json'); print(len(raw), 'bytes xz;', len(b), 'base64 in', n, 'chunks')
