'''
fix_paste_corruption.py — repair Python files mangled by markdown-quoting pastes

When Python source is pasted through a Markdown-rendering chat UI and then
committed without being opened in a plain-text editor, seven distinct
corruptions tend to land together. This script fixes all of them in one pass.

(Note: this docstring uses single-quote triple-delimiters because the
corruption pattern it describes involves literal `"""` sequences that would
otherwise terminate a double-quoted docstring.)

THE CORRUPTION PATTERN
----------------------

1. Smart quotes replace ASCII quotes throughout:
      U+201C "       → "
      U+201D "       → "
      U+2018 '       → '
      U+2019 '       → '
   Any triple-quoted docstring delimiter becomes invalid Python.

2. Literal markdown code fences (```) appear on their own lines where the
   rendered code blocks had fence separators. Inside a Python module they
   are parse errors — EXCEPT when they fall inside a docstring, where
   they are legitimate markdown content of the string. The repair tracks
   """ state while walking and only strips fences outside docstring regions.

3. Line 1 of the module is a comment-form docstring: `# """...` — the
   stray `#` converts the opening triple-quote into a comment, leaving
   the following docstring lines as loose statements that syntax-error
   on the first non-string expression.

4. The entry guard `if __name__ == "__main__":` is replaced by
   `if **name** == "**main**":` because the Markdown renderer interpreted
   the `__name__` / `__main__` underscores as bold markers.

5. Every class body has exactly one level (4 spaces) of indentation
   stripped. A `def method(self):` that was at column 4 is now at column 0;
   its body that was at column 8 is now at column 4; and so on. Nested
   indentation within each level is preserved, so only the OUTER strip
   needs to be undone.

6. Module-level function bodies (e.g. `def demo_xxx():` at the repo root)
   have the same one-level strip applied.

7. The body of `if __name__ == "__main__":` is also flush-left.

REPAIR STRATEGY
---------------

Phase 1: byte-level substitutions for the first four items.

Phase 2: a state-machine walk that tracks four boolean flags and re-adds
one indent level wherever the original had one stripped:

    in_class       — currently inside a class body
    in_enum        — inside `class X(..., Enum):` specifically, so that
                      ALL_CAPS = "value" lines are treated as enum members
                      (indented) rather than module-level constants
                      (which would wrongly end the class body)
    in_function    — inside a module-level def body
    in_main_guard  — inside the `if __name__ == "__main__":` body

Any of those four flags triggers a +4-space indent on subsequent lines
until a top-level marker resets the state. Resetting markers are:

    • another `class X:` declaration
    • `@dataclass` (signals the next top-level class)
    • a module-level `def foo(...)` that does NOT take `self` or `cls`
    • `if __name__ == "__main__":`
    • `import ...` / `from ... import ...`
    • an ALL_CAPS constant assignment that is NOT an enum member
    • a section-divider comment (five or more `=` or `-` characters)

KNOWN LIMITATIONS
-----------------

• The ALL_CAPS reset heuristic will misfire on a non-Enum class that
  defines UPPER_CASE class attributes. Enum classes are detected and
  excluded, but `class MyClass: CONSTANT = 1` will end the class body
  prematurely. None of the repo's audit files have hit this case so far.

• `try: / except ImportError:` blocks wrapping top-level imports are not
  handled. After the one-level strip, `import numpy as np` inside the
  try block looks identical to a top-level import, and the state machine
  resets on it. Files that use the optional-import pattern (e.g. the
  numpy/stdlib fallback in ocean_timber_sequestration_audit.py) will need
  manual re-indentation of the try/except block after the tool runs.
  None of the real corrupted pastes in this repo have used this pattern.

• Section-divider comments reset the state even if they were originally
  inside a class or function. This has not been observed to cause problems
  in practice because the paste source puts dividers between top-level
  sections, not inside methods.

• Decorators other than `@dataclass`, `@property`, `@classmethod`, and
  `@staticmethod` are passed through without state changes.

• The script does NOT fix imports that are no longer legal under the
  repo's pure-stdlib rule (e.g. `import numpy`). Those need manual
  follow-up edits after the indentation fix lands. See the commit
  history for examples of the minimal `np.mean` → local helper and
  `np.random.normal` → `random.gauss` swaps.

VERIFICATION
------------

The tool has been round-trip tested: a known-good committed file is
programmatically mangled with all seven corruption steps, then the tool
is run on the mangled copy and the result is checked for both `ast.parse`
success and behaviorally-equivalent execution output. See the commit
message for the specific file used.

USAGE
-----

    python tools/fix_paste_corruption.py FILE [FILE ...]

Each file is repaired in place. The script prints `OK` for successful
repairs and `LINE N: <error>` for files that still fail to parse after
the fix, so you can spot edge cases that need manual attention.

This is a maintenance tool, not framework code. It has no tests and is
not imported by any module. License: CC0.
'''
import ast
import re
import sys


def fix_file(path):
    with open(path, 'rb') as f:
        text = f.read().decode('utf-8')

    # ── Phase 1: byte-level substitutions ──
    text = (text
            .replace('\u201C', '"').replace('\u201D', '"')
            .replace('\u2018', "'").replace('\u2019', "'")
            .replace('**name**', '__name__')
            .replace('**main**', '__main__'))

    lines = text.split('\n')

    # Line-1 `# """` -> `"""` (stray # commented out the docstring opener)
    if lines and lines[0].lstrip().startswith('# "'):
        lines[0] = lines[0].replace('# "', '"', 1)

    # Remove lone markdown code fences, but ONLY when they are NOT inside
    # a docstring. Remote files sometimes embed ``` fences inside class
    # docstrings as markdown formatting, and those are legitimate content.
    # Walk the lines tracking """ state so we can distinguish.
    filtered = []
    in_docstring = False
    for line in lines:
        # Count unescaped triple-double-quotes on this line (naive but
        # sufficient for repair — repaired files will get a proper parse
        # check afterward)
        triple_count = line.count('"""')
        is_fence = (line.strip() == '```')

        if is_fence and not in_docstring:
            # Stray paste-artifact fence — drop it
            continue

        filtered.append(line)

        # Toggle docstring state AFTER the drop decision. A line with an
        # odd number of """ flips the state.
        if triple_count % 2 == 1:
            in_docstring = not in_docstring

    lines = filtered

    # ── Phase 2: state-machine indentation repair ──
    out = []
    in_class = False
    in_enum = False
    in_function = False
    in_main_guard = False

    def is_method_def(s):
        m = re.match(r'def\s+\w+\s*\(\s*([^,\s:)]+)', s)
        if not m:
            return False
        return m.group(1).strip() in ('self', 'cls')

    def extra_indent():
        return 4 if (in_class or in_function or in_main_guard) else 0

    for line in lines:
        stripped = line.lstrip()

        if stripped == '':
            out.append(line)
            continue

        leading = len(line) - len(stripped)

        if leading > 0:
            # Already nested — still needs +4 if inside a class or function
            out.append(' ' * extra_indent() + line)
            continue

        if stripped.startswith('class '):
            in_class = True
            in_function = False
            # Detect Enum subclass so enum members aren't misread as
            # module-level constants.
            in_enum = bool(re.search(r'\(\s*[^)]*\bEnum\b', stripped))
            out.append(line)
            continue

        if stripped.startswith('@'):
            tag = stripped.split('(')[0].lstrip('@').strip()
            if tag == 'dataclass':
                in_class = False
                in_enum = False
                in_function = False
                out.append(line)
            elif in_class and tag in ('property', 'classmethod', 'staticmethod'):
                out.append('    ' + line)
            else:
                in_function = False
                out.append(line)
            continue

        if stripped.startswith('def '):
            if is_method_def(stripped) and in_class:
                # Method — indent to col 4. Body follows in_class rule.
                out.append('    ' + line)
            else:
                # Module-level function — stays at col 0, body needs +4
                in_class = False
                in_enum = False
                in_function = True
                out.append(line)
            continue

        if stripped.startswith('if __name__'):
            in_class = False
            in_enum = False
            in_function = False
            in_main_guard = True
            out.append(line)
            continue

        if stripped.startswith(('import ', 'from ')):
            in_class = False
            in_enum = False
            in_function = False
            in_main_guard = False
            out.append(line)
            continue

        if re.match(r'^[A-Z_][A-Z_0-9]*\s*[:=]', stripped):
            if in_enum:
                # Enum member — treat as class attribute, not a reset marker
                out.append('    ' + line)
                continue
            in_class = False
            in_enum = False
            in_function = False
            out.append(line)
            continue

        if stripped.startswith('#'):
            if '=' * 5 in stripped or '-' * 5 in stripped:
                in_class = False
                in_enum = False
                in_function = False
                out.append(line)
            elif extra_indent():
                out.append('    ' + line)
            else:
                out.append(line)
            continue

        # Everything else: body content — indent if inside class or function
        if extra_indent():
            out.append('    ' + line)
        else:
            out.append(line)

    fixed = '\n'.join(out)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed)

    try:
        ast.parse(fixed)
        return 'OK'
    except SyntaxError as e:
        txt = e.text.rstrip() if e.text else ''
        return f'LINE {e.lineno}: {e.msg} :: {txt}'


def main(argv):
    if len(argv) < 2 or argv[1] in ('-h', '--help'):
        print("usage: python tools/fix_paste_corruption.py FILE [FILE ...]",
              file=sys.stderr)
        print("",
              file=sys.stderr)
        print("Repairs markdown-paste corrupted Python files in place.",
              file=sys.stderr)
        print("See the module docstring for the corruption pattern and",
              file=sys.stderr)
        print("repair strategy.", file=sys.stderr)
        return 1

    rc = 0
    for path in argv[1:]:
        result = fix_file(path)
        print(f"{path}: {result}")
        if result != 'OK':
            rc = 2
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv))
