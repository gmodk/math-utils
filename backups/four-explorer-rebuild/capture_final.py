from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'validation-results/four-explorer-changes.txt'
out.touch(exist_ok=True)
parts=[]
for args in [('status','--short'),('diff','--stat'),('status','--short','--untracked-files=all')]:
    result=subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
    parts.append('git '+' '.join(args)+'\n'+result.stdout)
parts.append('Incoming deletions were preserved; no new deletion of legacy explorer files was performed.\n'
             'The replacement correlation HTML was already untracked. Backup and test artifacts are retained.\n'
             'The diff statistic covers tracked files only; the full status above also lists new engines, UI assets, tests and fixtures.\n')
out.write_text('\n'.join(parts),encoding='utf-8')
print('\n'.join(parts[:2]))
