from net import Net
from pathlib import Path
from subprocess import run as run_process, PIPE
from typing import NamedTuple, Callable, Dict, Tuple, Iterable, List
import random 
import re
import math

N = 4

BENCHES = {}
SPEED_RANGE = list(range(1, 250, 25))

RE_RESULT = re.compile(rb'(?s).*finished:\s*(\d+)\naverage Delay:\s*(\S+)\n')

class Result(NamedTuple):
    finished: int
    delay: float
    hot: List[int]

def run_net(name: str, net: Net) -> Result:
    assert net.n == N

    path = Path('./nets') / name
    net.save(path, overwrite=True)

    args = [
        './popnet',
        '-A', str(net.n),
        '-c', '2',
        '-V', '3',
        '-B', '12',
        '-O', '12',
        '-F', '4',
        '-L', '1000',
        '-T', '1000',
        '-r', '1',
        '-I', str(path / name),
        '-R', '0',
    ]
    sub = run_process(args, check=True, stdout=PIPE, stderr=PIPE)
    m = RE_RESULT.match(sub.stdout)
    hot = [0] * (net.n * net.n)
    for route_log in sub.stderr.decode().split('\n'):
        if route_log:
            x, y, cnt = map(int, route_log.split(' '))
            idx = x * net.n + y
            assert hot[idx] == 0
            hot[idx] = cnt

    return Result(
        finished=int(m[1]),
        delay=float(m[2]),
        hot=hot,
    )

def bench(name: str, speeds: List[int]):
    def decorator(gen: Callable[[int], Net]) -> Callable[[int], Net]:
        def bench_runner():
            print(f'Benching {name}: ', end='', flush=True)
            with open(Path('./result') / f'{name}.txt', 'w') as f:
                n = len(speeds)
                for i, speed in enumerate(speeds):
                    fmt = f'{i}/{n} '
                    print(fmt + '\b' * len(fmt), end='', flush=True)
                    net = gen(speed)
                    ret = run_net(name, net)
                    f.write(f'{speed} {ret.finished} {ret.delay}\n')
                    f.write(' '.join(str(cnt) for cnt in ret.hot))
                    f.write('\n')
                    f.flush()
            print('Done ')
        assert name not in BENCHES
        BENCHES[name] = bench_runner
        return gen
    return decorator

# i -> random[0, n * n)
@bench('base', SPEED_RANGE)
def gen_base_net(pkts_per_sec: int) -> Net:
    net = Net(N)
    cnt = pkts_per_sec * N * N
    for t in range(pkts_per_sec):
        for i in range(N * N):
            j = i
            while j == i:
                j = random.randint(0, N * N - 1)
            net.add(t / cnt, (i // N, i % N), (j // N, j % N), 5)
    return net

# i -> n - 1 - i
@bench('reverse', SPEED_RANGE)
def gen_reverse_net(pkts_per_sec: int) -> Net:
    net = Net(N)
    cnt = pkts_per_sec * N * N
    for t in range(pkts_per_sec):
        for i in range(N * N):
            j = N * N - 1 - i
            net.add(t / cnt, (i // N, i % N), (j // N, j % N), 5)
    return net

# i -> reverse_bit(i)
@bench('butterfly', SPEED_RANGE)
def gen_butterfly_net(pkts_per_sec: int) -> Net:
    net = Net(N)
    cnt = pkts_per_sec * N * N
    N2 = N * N
    assert (N2 & -N2) == N2
    BITS = int(math.log2(N2) + 1e-9)
    for t in range(pkts_per_sec):
        for i in range(N * N):
            t = i
            j = 0
            for _ in range(BITS):
                j = (j << 1) | (t & 1)
                t >>= 1
            net.add(t / cnt, (i // N, i % N), (j // N, j % N), 5)
    return net

# i -> random[80% => 0, 20% => random[1, n * n)]
@bench('some_most', SPEED_RANGE)
def gen_some_most_net(pkts_per_sec: int) -> Net:
    net = Net(N)
    cnt = pkts_per_sec * N * N
    for t in range(pkts_per_sec):
        for i in range(N * N):
            j = 0 if random.random() < 0.8 else random.randint(1, N * N - 1)
            net.add(t / cnt, (i // N, i % N), (j // N, j % N), 5)
    return net

def main():
    for bench in BENCHES.values():
        bench()

if __name__ == '__main__':
    main()
