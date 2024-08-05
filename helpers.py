from datetime import datetime
from urllib.request import urlopen


def timer(function):
    def wrapper():
        start = datetime.now()
        function()
        end = datetime.now()
        time = end - start
        print(f"{function.__name__} took {round(time.seconds/60, 2)} minutes")

    return wrapper


def checkUrl(url):
    try:
        urlopen(url)
    except:
        return False
    return True


def printErr(msg): 
    print("\033[31;1;1m" + msg + "\033[0m")
