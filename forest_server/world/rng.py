"""mulberry32 as specified by the master plan. Scatter and landmarks only."""


def mulberry32(seed: int):
    a = seed & 0xFFFFFFFF

    def next_f() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        mixed = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
        t = (t ^ ((t + mixed) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return (t ^ (t >> 14)) / 4294967296

    return next_f
