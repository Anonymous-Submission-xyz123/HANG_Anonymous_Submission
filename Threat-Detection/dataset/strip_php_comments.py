import os
from pathlib import Path

SRC = Path(__file__).resolve().parent / "php-webshells" / "Collection"
DST = Path(__file__).resolve().parent / "php-webshells" / "Collection_clean"


def strip_php_comments(src: str) -> str:
    """Remove //, # and /* */ comments from PHP source.

    Respects single-/double-quoted strings, heredoc, nowdoc, and #[ attribute syntax.
    Outside <?php ... ?> the content (usually HTML) is passed through unchanged.
    """
    out = []
    i = 0
    n = len(src)
    in_php = False
    state = None  # None | 'sq' | 'dq' | ('heredoc', ident) | ('nowdoc', ident)

    while i < n:
        # ----- Outside PHP -----
        if not in_php:
            if src.startswith("<?php", i):
                out.append("<?php"); i += 5; in_php = True; continue
            if src.startswith("<?=", i):
                out.append("<?="); i += 3; in_php = True; continue
            if src.startswith("<?", i):
                out.append("<?"); i += 2; in_php = True; continue
            out.append(src[i]); i += 1; continue

        # ----- Inside a string -----
        if state == "sq":
            out.append(src[i])
            if src[i] == "\\" and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if src[i] == "'":
                state = None
            i += 1; continue

        if state == "dq":
            out.append(src[i])
            if src[i] == "\\" and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if src[i] == '"':
                state = None
            i += 1; continue

        if isinstance(state, tuple) and state[0] in ("heredoc", "nowdoc"):
            ident = state[1]
            line_end = src.find("\n", i)
            if line_end == -1:
                line_end = n
            line = src[i:line_end]
            stripped = line.lstrip()
            if stripped.startswith(ident):
                rest = stripped[len(ident):]
                if rest == "" or not (rest[0].isalnum() or rest[0] == "_"):
                    out.append(line)
                    i = line_end
                    state = None
                    continue
            out.append(line)
            if line_end < n:
                out.append("\n"); i = line_end + 1
            else:
                i = n
            continue

        # ----- PHP code, not in a string -----
        c = src[i]

        if src.startswith("?>", i):
            out.append("?>"); i += 2; in_php = False; continue

        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue

        if c == "#" and (i + 1 >= n or src[i + 1] != "["):
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue

        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue

        if c == "'":
            state = "sq"; out.append(c); i += 1; continue
        if c == '"':
            state = "dq"; out.append(c); i += 1; continue

        if src.startswith("<<<", i):
            k = i + 3
            while k < n and src[k] in " \t":
                k += 1
            kind = "heredoc"
            if k < n and src[k] == "'":
                kind = "nowdoc"; k += 1
                start = k
                while k < n and src[k] != "'":
                    k += 1
                ident = src[start:k]; k += 1
            elif k < n and src[k] == '"':
                k += 1
                start = k
                while k < n and src[k] != '"':
                    k += 1
                ident = src[start:k]; k += 1
            else:
                start = k
                while k < n and (src[k].isalnum() or src[k] == "_"):
                    k += 1
                ident = src[start:k]
            while k < n and src[k] != "\n":
                k += 1
            out.append(src[i:k])
            i = k
            if ident:
                state = (kind, ident)
            continue

        out.append(c); i += 1

    return "".join(out)


def main():
    DST.mkdir(parents=True, exist_ok=True)
    ok = 0
    errs = 0
    for path in sorted(SRC.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(SRC)
        out_path = DST / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = path.read_text(encoding="utf-8", errors="replace")
            out_path.write_text(strip_php_comments(data), encoding="utf-8")
            ok += 1
        except Exception as e:
            print(f"[error] {rel}: {e}")
            errs += 1
    print(f"Processed {ok} files ({errs} errors) -> {DST}")


if __name__ == "__main__":
    main()
