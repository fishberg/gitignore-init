# gitignore-init

A command-line tool that helps you copy a `.gitignore` from the official GitHub repo:
- https://github.com/github/gitignore

## Install
Install cloned repo:
```
pip install -e .
```

Install directly from GitHub:
```
pip install git+https://github.com/fishberg/gitignore-init
```

## Usage
```
gitignore-init
```

## TODOs?
- Rename installed callable script to `gitignore` or `gitignore_init` instead of `gitignore-init`
- If `.gitignore` already exists, open in `$EDITOR`
- Providing CLI argument allows you to create a file with different name than `.gitignore`
- Allow variable that sets repo location somewhere other than `~/.local`
