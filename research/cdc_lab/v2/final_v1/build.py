"""Build a production-font preparation candidate; fail on formatting defects.

No author metadata is synthesized. A successful build is not submission approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output,tex_directory):
    source=Path(__file__).resolve().parent
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    tex_directory=Path(tex_directory).resolve()
    for package in ('libertine.sty','zi4.sty','newtxmath.sty'):
        if not subprocess.check_output(['kpsewhich',package],text=True).strip():
            raise RuntimeError('required ACM font package missing: '+package)
    for name in ('manuscript.tex','references.bib'):
        shutil.copy2(source/name,output/name)
    shutil.copytree(source/'figures',output/'figures')
    config=dict(os.environ,TEXINPUTS=str(tex_directory)+os.pathsep+os.environ.get('TEXINPUTS',''),BSTINPUTS=str(tex_directory)+os.pathsep+os.environ.get('BSTINPUTS',''))
    commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error','manuscript.tex'],['bibtex','manuscript']]+[['pdflatex','-interaction=nonstopmode','-halt-on-error','manuscript.tex']]*2
    with (output/'build.log').open('w') as log:
        for command in commands:subprocess.run(command,cwd=output,env=config,stdout=log,stderr=subprocess.STDOUT,check=True)
    pdf=output/'manuscript.pdf'
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    text=subprocess.check_output(['pdftotext','-layout',str(pdf),'-'],text=True)
    fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True)
    log=(output/'manuscript.log').read_text()
    pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
    if pages>4 or '612 x 792 pts (letter)' not in info:raise ValueError('page limit or US Letter failure')
    forbidden=('undefined references','undefined citations','Citation `','Overfull \\hbox','Overfull \\vbox','Missing character:','You do not have the')
    if any(x in log for x in forbidden):raise ValueError('unresolved citation, overflow, missing glyph or font')
    if 'Type 3' in fonts:raise ValueError('bitmap font detected')
    for line in fonts.splitlines()[2:]:
        if line.strip() and not re.search(r'\byes\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$',line):raise ValueError('unembedded font: '+line)
    if not all(x in fonts for x in ('LinLibertine','Inconsolata')):raise ValueError('ACM text/mono fonts not embedded')
    if re.search(r'TODO|TBD|placeholder|pending verification|Requirements unverified|Conference acronym|XXXX|Anon\.',text,re.I):raise ValueError('placeholder detected')
    if r'\documentclass[sigconf,9pt]{acmart}' not in (output/'manuscript.tex').read_text():raise ValueError('wrong class declaration')
    for name,body in (('pdfinfo.txt',info),('pdffonts.txt',fonts),('extracted.txt',text)):(output/name).write_text(body)
    report=dict(status='production_font_candidate_not_submission_ready',pages=pages,page_size='US Letter 612x792pt',class_options='sigconf,9pt',
        authors_present=False,blockers=['Verified owner author/affiliation/ORCID metadata missing; nonanonymous-track requirement unmet','Official CFP/template rules require current authoritative reconfirmation','Paper 1 submitted manuscript unavailable for overlap review'],
        hashes={name:digest(output/name) for name in ('manuscript.tex','references.bib','manuscript.pdf')},class_sha256=digest(tex_directory/'acmart.cls'),
        warnings=[line for line in log.splitlines() if 'Warning' in line],commands=commands)
    (output/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--tex-directory',type=Path,required=True)
    a=p.parse_args();build(a.output,a.tex_directory)
