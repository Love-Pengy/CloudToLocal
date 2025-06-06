VERBOSE = False
FAIL_ON_WARNING = False


def pinfo(*args, **kwargs):
    if (VERBOSE):
        print("'\033[94m")
        print("ⓘ  ", end="")
        print(*args, **kwargs)
        print("\033[0m")


def pwarning(*args, **kwargs):
    print("\033[93m")
    print("⚠️", end="")
    print(*args, **kwargs)
    print("\033[0m")
    if (FAIL_ON_WARNING):
        exit()


def psuccess(*args, **kwargs):
    print("\033[92m")
    print("✅", end="")
    print(*args, **kwargs)
    print("\033[0m")


def perror(*args, **kwargs):
    print("\033[91m")
    print("❌", end="")
    print(*args, **kwargs)
    print("\033[0m")
    exit()
