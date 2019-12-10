from pathlib import Path
from typing import Tuple, List, NamedTuple
import subprocess

class Packet(NamedTuple):
    time: float
    dest: Tuple[int, int]
    src: Tuple[int, int]
    length: int

class Net(object):
    def __init__(self, n: int):
        self.n = n
        self.arr = [[] for _ in range(n * n)]
        pass

    def _idx(self, tup: Tuple[int, int]):
        x, y = tup
        assert 0 <= x < self.n
        assert 0 <= y < self.n
        return x * self.n + y

    def add(self, time: float, src: Tuple[int, int], dest: Tuple[int, int], length: int):
        assert length >= 0
        self.arr[self._idx(src)].append(Packet(time, src, dest, length))

    def _save_file(self, path: Path, pkts: List[Packet]):
        with open(path, 'w') as f:
            pkts.sort(key=lambda xs: xs.time)
            for time, (x1, y1), (x2, y2), length in pkts:
                f.write(f'{time} {x1} {y1} {x2} {y2} {length}\n')

    def save(self, path: Path, overwrite: bool = False):
        name = path.name

        if path.is_dir():
            if not overwrite:
                raise FileExistsError(f'Directory exists: {path}')
            subprocess.run(['trash', str(path)], check=True)
        
        path.mkdir()

        for i in range(self.n):
            for j in range(self.n):
                self._save_file(path / f'{name}.{i}.{j}', self.arr[self._idx((i, j))])

        self._save_file(path / name, [pkt for pkts in self.arr for pkt in pkts])
