import threading

def worker():
    print("Thread started")

t = threading.Thread(target=worker)
t.start()
t.join()
