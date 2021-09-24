import os,time
import multiprocessing as mp
import random


def sub_process(name, delay):
    while True:
        time.sleep(delay)
        print(f'我是子进程{name}, 进程id是{os.getpid()}')


#queue
mp.Queue(10)

#pipe
def sub_process_A(pipe):
    aim = random.randint(0,128)
    pipe.send('我想好了一个[0,128)的数，你猜是几?')
    print('A: 我想好了一个[0,128)的数，你猜是几?')
    while True:
        guess = pipe.recv()
        time.sleep(0.5+0.5*random.random())
        if guess == aim:
            pipe.send('恭喜你猜中了')
            print('恭喜你猜中了')
            break
        elif guess < aim:
            pipe.send('猜小了')
            print('A: 不对，猜小了')
        else:
            pipe.send('猜大了')
            print('A：不对，猜大了')

def sub_process_B(pipe):
    result = pipe.recv()
    n_min, n_mix = 0,127
    while True:
        time.sleep(0.5 + 0.5 * random.random())
        guess = n_min + (n_mix-n_min)//2
        pipe.send(guess)
        print(f'B: 我猜是{guess}')
        result =  pipe.recv()
        if result == '恭喜你猜中了':
            print('B: 哈哈被我猜中了')
            break
        elif result == '猜小了':
            n_min, n_mix = guess+1, 127
        else:
            n_min, n_mix = n_min, guess


#共享内存Value, Array
def sub_process_A1(flag, data):
    while True:
        if flag.value == '0':
            time.sleep(1)
            for i in range(len(data)):
                data[i] +=2
            flag.value = 1
            print([item for item in data])

def sub_process_B1(flag, data):
    while True:
        if flag.value == '1':
            time.sleep(1)
            for i in range(len(data)):
                data[i] -=1
            flag.value = 0
            print([item for item in data])
#进程池
def power(x, a=2):
    time.sleep(1)
    print(f'{x}的{a}次方等于{pow(x,a)}')

#MaprReduce模型
from functools import reduce



if __name__ == '__main__':
    # print(f'主进程{os.getpid()}开始，按任意键结束本进程')
    # p_a = mp.Process(target=sub_process, args=('A', 1))
    # p_b = mp.Process(target=sub_process, args=('B', 2))
    # p_a.daemon = True
    # p_a.start()
    # p_b.daemon = True
    # p_b.start()
    # input()

    #pipe
    # pipe_enda, pipe_endb = mp.Pipe()
    # p_a = mp.Process(target=sub_process_A, args=(pipe_enda,))
    # p_a.daemon=True
    # p_a.start()
    # p_b = mp.Process(target=sub_process_B, args=(pipe_endb,))
    # p_b.daemon=True
    # p_b.start()
    # p_a.join()
    # p_b.join()

    #共享内存
    # flag = mp.Value('i', 0)
    # data = mp.Array('d', range(5))
    # p_a = mp.Process(target=sub_process_A1, args=(flag,data))
    # p_a.daemon=True
    # p_a.start()
    # p_b = mp.Process(target=sub_process_B1, args=(flag,data))
    # p_b.daemon=True
    # p_b.start()
    # input()

    # 进程池
    # mpp=mp.Pool(processes=4)
    # for item in [2,3,4,5,6,7,8,9]:
    #
    #     mpp.apply_async(power, (item,))
    #     mpp.apply(power, (item, ))
    # mpp.close()
    # mpp.join()

    #MapReduce模型

    mp.freeze_support()
    print('开始计算。。。')
    t0 = time.time()
    with mp.Pool(processes=8) as mpp:
        result_map = mpp.map(power, range(100))
        result = reduce(lambda result, x: result+x, result_map, 0)





