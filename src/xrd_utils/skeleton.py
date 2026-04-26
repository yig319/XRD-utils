"""Compatibility scaffold helpers for XRD-utils."""

from __future__ import annotations

import argparse


def fib(n: int) -> int:
    """Return the n-th Fibonacci number using the PyScaffold demo convention."""
    assert n > 0
    if n in (1, 2):
        return 1
    previous, current = 1, 1
    for _ in range(3, n + 1):
        previous, current = current, previous + current
    return current


def main(args=None) -> int:
    parser = argparse.ArgumentParser(description="Print a Fibonacci number.")
    parser.add_argument("n", type=int)
    parsed = parser.parse_args(args)
    value = fib(parsed.n)
    print(f"The {parsed.n}-th Fibonacci number is {value}")
    return 0


__all__ = ["fib", "main"]
