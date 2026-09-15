#!/usr/bin/env python3
"""Build a complete versioned paclet and verify every archived byte."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

root=Path(__file__).resolve().parent
source=root/'SSGReciprocalDatabase'
parser=argparse.ArgumentParser()
parser.add_argument('version')
args=parser.parse_args()
if not re.fullmatch(r'\d+\.\d+\.\d+',args.version):
    parser.error('version must have the form MAJOR.MINOR.PATCH')
manifest_text=(source/'PacletInfo.wl').read_text()
match=re.search(r'Version\s*->\s*"([^"]+)"',manifest_text)
if not match or match.group(1)!=args.version:
    raise SystemExit(f'PacletInfo version does not match {args.version}')
validation=json.loads((source/'Data/MagneticSpaceGroupIdentificationValidation.json').read_text())
assert validation['Status']=='PASS' and validation['Records']==67475
for name in ('identify_magnetic_space_groups.py','validate_magnetic_space_groups.py',
             'identify_standard_space_groups.py','test_magnetic_space_groups.py',
             'audit_magnetic_reference.py'):
    shutil.copy2(root/name,source/'Scripts'/name)
shutil.copy2(root/'MAGNETIC_SPACE_GROUP_IDENTIFICATION_ZH.md',source/'MAGNETIC_SPACE_GROUP_IDENTIFICATION_ZH.md')
shutil.copy2(root/'SSGReciprocalDatabase_UserGuide_EN.md',source/'SSGReciprocalDatabase_UserGuide_EN.md')
output=root/f'dist/SSGReciprocalDatabase-{args.version}.paclet'
temporary=output.with_suffix('.tmp')
files=[p for p in sorted(source.rglob('*')) if p.is_file()
       and '__pycache__' not in p.parts and p.name!='.DS_Store' and p.suffix!='.pyc']
paclet_info=source/'PacletInfo.wl'
files.remove(paclet_info)
files.insert(0,paclet_info)
prefix=f'SSGReciprocalDatabase-{args.version}/'
with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for path in files:
        archive.write(path,prefix+path.relative_to(source).as_posix())
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    for path in files:
        stored=archive.read(prefix+path.relative_to(source).as_posix())
        assert hashlib.sha256(stored).digest()==hashlib.sha256(path.read_bytes()).digest()
temporary.replace(output)
print(f'Verified {len(files)} files: {output}')
print('SHA256',hashlib.sha256(output.read_bytes()).hexdigest())
