import globals

def info(*args, **kwargs):
    if (not globals.QUIET):
        print("'\033[94m")
        print("ⓘ  ", end="")
        print(*args, **kwargs)
        print("\033[0m")


def warning(*args, **kwargs):
    print("\033[93m")
    print("⚠️", end="")
    print(*args, **kwargs)
    print("\033[0m")
    if (globals.FAIL_ON_WARNING):
        exit()


def success(*args, **kwargs):
    if(not globals.QUIET):
        print("\033[92m")
        print("✅", end="")
        print(*args, **kwargs)
        print("\033[0m")


def error(*args, **kwargs):
    print("\033[91m")
    print("❌", end="")
    print(*args, **kwargs)
    print("\033[0m")
    exit()
