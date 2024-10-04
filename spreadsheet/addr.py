class Addr:
    col: str
    row: int

    def __init__(self, addr: str):
        i = 0
        while not addr[i].isdigit():
            i += 1

        self.col = addr[:i]
        self.row = int(addr[i:])
