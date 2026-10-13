"""Build a versioned ACM-class preview. This does not verify venue compliance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def build(output,tex_directory):
    source=Path(__file__).resolve().parent
    output=Path(output).resolve()
    tex_directory=Path(tex_directory).resolve()
    output.mkdir(parents=True,exist_ok=False)
    for name in ('manuscript.tex','references.bib'):
        shutil.copy2(source/name,output/name)
    shutil.copytree(source/'figures',output/'figures')
    config=dict(os.environ)
    config['TEXINPUTS']=str(tex_directory)+os.pathsep+config.get('TEXINPUTS','')
    config['BSTINPUTS']=str(tex_directory)+os.pathsep+config.get('BSTINPUTS','')
    commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error','manuscript.tex'],
              ['bibtex','manuscript'],
              ['pdflatex','-interaction=nonstopmode','-halt-on-error','manuscript.tex'],
              ['pdflatex','-interaction=nonstopmode','-halt-on-error','manuscript.tex']]
    with (output/'build.log').open('w') as log:
        for command in commands:
            subprocess.run(command,cwd=output,env=config,stdout=log,stderr=subprocess.STDOUT,check=True)
    info=subprocess.check_output(['pdfinfo',str(output/'manuscript.pdf')],text=True)
    pages=int(next(line.split(':',1)[1].strip() for line in info.splitlines() if line.startswith('Pages:')))
    warnings=[line for line in (output/'manuscript.log').read_text().splitlines() if 'Warning' in line]
    report=dict(status='preview_only_not_submission_ready',pages=pages,
                pdf_sha256=hashlib.sha256((output/'manuscript.pdf').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256((source/'manuscript.tex').read_bytes()).hexdigest(),
                class_sha256=hashlib.sha256((tex_directory/'acmart.cls').read_bytes()).hexdigest(),
                warnings=warnings,venue_requirements_verified=False)
    (output/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--tex-directory',required=True,type=Path)
    args=parser.parse_args();build(args.output,args.tex_directory)
