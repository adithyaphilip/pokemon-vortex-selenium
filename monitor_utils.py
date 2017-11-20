import sys


def debug(msg: str):
    print("DEBUG: %s" % msg)


def warn(msg: str):
    print("WARNING: %s" % msg, file=sys.stderr)


def error(msg: str):
    print("ERROR: %s" % msg, file=sys.stderr)
