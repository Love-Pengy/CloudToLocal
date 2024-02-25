from datetime import datetime

def timer(function): 
    def wrapper(): 
        start = datetime.now()
        function()
        end = datetime.now()
        time = end - start
        print(f"{function.__name__} took {round(time.seconds/60, 2)} minutes")
    return wrapper


