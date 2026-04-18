from multiprocessing import Process, Value, Lock


def wrong_increment(counter):
    for _ in range(100000):
        counter.value += 1


def right_increment(counter, lock):
    for _ in range(100000):
        with lock:
            counter.value += 1


if __name__ == "__main__":
    counter = Value("i", 0)

    processes = [Process(target=wrong_increment, args=(counter,)) for _ in range(4)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print("Ожидаемое значение: 400000")
    print("Wrong значение:", counter.value)

    counter = Value("i", 0)
    lock = Lock()

    processes = [Process(target=right_increment, args=(counter, lock,)) for _ in range(4)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print("Right значение:", counter.value)