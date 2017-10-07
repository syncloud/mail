import time


def retry_func(func, message="something", retries=0, sleep=1):
    retry = 0
    while True:
        try:
            echo "running: {0}".format(message)
            return func()
        except Exception, e:
            if retry >= retries:
                raise e
            retry += 1
            time.sleep(sleep)
            print('retrying {0}'.format(retry))
