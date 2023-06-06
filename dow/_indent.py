
def indent(t, p):
    def plines():
        for line in t.splitlines(True):
            yield (p + line if line.strip() else line)

    return "".join(plines())
