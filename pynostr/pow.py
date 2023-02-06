import time
from dataclasses import dataclass, field

from .event import Event
from .key import PrivateKey

BECH32_CHARS = '023456789acdefghjklmnpqrstuvwxyz'


def zero_bits(b: int) -> int:
    n = 0

    if b == 0:
        return 8

    while b >> 1:
        b = b >> 1
        n += 1

    return 7 - n


def count_leading_zero_bits(hex_str: str) -> int:
    total = 0
    for i in range(0, len(hex_str) - 2, 2):
        bits = zero_bits(int(hex_str[i : i + 2], 16))
        total += bits

        if bits != 8:
            break

    return total


def _guess_event(event: Event) -> Event:
    event.compute_id()
    num_leading_zero_bits = count_leading_zero_bits(event.id)
    return num_leading_zero_bits, event


def _guess_key():
    sk = PrivateKey()
    num_leading_zero_bits = count_leading_zero_bits(sk.public_key.hex())
    return num_leading_zero_bits, sk


def _guess_vanity_key():
    sk = PrivateKey()
    vk = sk.public_key.bech32()
    return vk, sk


@dataclass
class Pow:
    def __post_init__(self):
        self.count = 0
        self.results = []
        self.duration = 0
        self.mode = "key"
        self.num_leading_zero_bits = 0
        self.n_pattern = 0
        self.n_options = 2
        self.operation = None

    def get_hashrate(self):
        if self.duration > 0 and self.count > 0:
            return self.count / self.duration
        else:
            return 0

    def _stop_mining(self, count, max_count, duration, max_duration):
        if max_count > 0 and count > max_count:
            return True
        elif max_duration > 0 and duration > max_duration:
            return True
        return False

    def estimate_hashrate(self, n_guesses: int = 1e4, **operation_kwargs):
        if self.operation is None:
            return 0
        n_guesses = int(n_guesses)

        def _time_operation():
            start = time.perf_counter()
            self.operation(**operation_kwargs)
            end = time.perf_counter()
            return end - start

        t = sum([_time_operation() for _ in range(n_guesses)]) / n_guesses
        hashrate = 1 / t
        return hashrate

    def get_expected_guesses(self):
        p = 1 / self.n_options
        return 1 / (p**self.n_pattern)

    def stored_results(self):
        return f"{len(self.results)}. {self.results[-1]}"

    def print_results(self):
        if self.mode in ["key", "event"]:
            print(
                f"Found event with {self.num_leading_zero_bits} "
                f"zeros after {self.count} tries"
            )
        print(f"avg. hash rate {self.get_hashrate()} guesses per s")
        print(f"Total duration {self.duration} s")


@dataclass
class PowEvent(Pow):
    difficulty: int = 8
    event: Event = field(default_factory=Event)

    def __post_init__(self):
        self.mode = "event"
        self.operation = _guess_event
        self.n_options = 2
        self.n_pattern = self.difficulty
        self.reset()

    def reset(self):
        event = Event(
            content=self.event.content, pubkey=self.event.pubkey, kind=self.event.kind
        )
        all_tags = [["nonce", "1", str(self.difficulty)]]
        all_tags.extend(self.event.tags)
        event.tags = all_tags
        self.num_leading_zero_bits, self.event = self.operation(event)
        self.count = 1
        self.duration = 0
        self.results = []

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.n_pattern = self.difficulty
        self.event.tags[0][2] = str(self.difficulty)

    def increase_difficulty(self):
        self.set_difficulty(self.num_leading_zero_bits + 1)

    def mine(self, max_count: int = 0, max_duration: int = 0) -> Event:
        start = time.perf_counter()
        count = 0
        duration = 0
        num_leading_zero_bits = self.num_leading_zero_bits
        event = self.event
        while num_leading_zero_bits < self.difficulty and (
            not self._stop_mining(count, max_count, duration, max_duration)
        ):
            self.count += 1
            event.tags[0][1] = str(self.count)
            num_leading_zero_bits, event = self.operation(event)
            if num_leading_zero_bits > self.num_leading_zero_bits:
                self.event = event
                self.num_leading_zero_bits = num_leading_zero_bits
            count += 1
            duration = time.perf_counter() - start
        end = time.perf_counter()
        self.duration += end - start
        self.results.append((self.num_leading_zero_bits, self.event))
        return self.event

    def get_expected_time(self, hashrate=None) -> float:
        if hashrate is None:
            if self.count > 10000 and self.duration > 0:
                hashrate = self.get_hashrate()
            else:
                hashrate = self.estimate_hashrate(event=self.event)
        self.n_pattern = self.difficulty
        self.n_options = 2
        return self.get_expected_guesses() / hashrate


@dataclass
class PowKey(Pow):
    difficulty: int = 8

    def __post_init__(self):
        self.mode = "key"
        self.operation = _guess_key
        self.n_options = 2
        self.n_pattern = self.difficulty
        self.reset()

    def reset(self):
        self.num_leading_zero_bits, self.sk = self.operation()
        self.count = 0
        self.duration = 0
        self.results = []

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.n_pattern = difficulty

    def increase_difficulty(self):
        self.set_difficulty(self.num_leading_zero_bits + 1)

    def mine(self, max_count: int = 0, max_duration: int = 0) -> PrivateKey:
        start = time.perf_counter()
        count = 0
        duration = 0
        num_leading_zero_bits = self.num_leading_zero_bits
        while num_leading_zero_bits < self.difficulty and (
            not self._stop_mining(count, max_count, duration, max_duration)
        ):
            num_leading_zero_bits, sk = self.operation()
            if num_leading_zero_bits > self.num_leading_zero_bits:
                self.sk = sk
                self.num_leading_zero_bits = num_leading_zero_bits
            count += 1
            duration = time.perf_counter() - start
        self.count += count
        end = time.perf_counter()
        self.duration += end - start
        self.results.append((self.num_leading_zero_bits, self.sk))
        return self.sk

    def get_expected_time(self, hashrate=None) -> float:
        if hashrate is None:
            if self.count > 10000 and self.duration > 0:
                hashrate = self.get_hashrate()
            else:
                hashrate = self.estimate_hashrate()
        self.n_pattern = self.difficulty
        self.n_options = 2
        return self.get_expected_guesses() / hashrate


@dataclass
class PowVanityKey(Pow):
    prefix: str = None
    suffix: str = None

    def __post_init__(self):
        self.n_pattern = 0
        self.operation = _guess_vanity_key
        self.n_options = len(BECH32_CHARS)
        self.mode = "vanity_key"
        if self.prefix is None and self.suffix is None:
            raise ValueError("Expected at least one of 'prefix' or 'suffix' arguments")

        for pattern in [self.prefix, self.suffix]:
            if pattern is not None:
                self.n_pattern += len(pattern)
                missing_chars = [c for c in pattern if c not in BECH32_CHARS]
                if len(missing_chars) > 0:
                    raise ValueError(
                        f"{missing_chars} not in valid "
                        f"list of bech32 chars: ({BECH32_CHARS})"
                    )
        self.reset()

    def reset(self):
        self.count = 0
        self.duration = 0
        self.results = []

    def _check_vanity(self):
        if (
            self.prefix is not None
            and not self.vk[5 : 5 + len(self.prefix)] == self.prefix
        ):
            return False
        if self.suffix is not None and not self.vk[-len(self.suffix) :] == self.suffix:
            return False
        return True

    def mine(self, max_count: int = 0, max_duration: int = 0) -> PrivateKey:
        start = time.perf_counter()
        count = 0
        duration = 0
        self.vk, self.sk = self.operation()
        while not self._check_vanity() and (
            not self._stop_mining(count, max_count, duration, max_duration)
        ):
            self.vk, self.sk = self.operation()
            count += 1
            duration = time.perf_counter() - start
        self.count += count
        end = time.perf_counter()
        self.duration += end - start
        if self._check_vanity():
            self.results.append((self.vk, self.sk))
        return self.sk

    def get_expected_time(self, hashrate=None):
        if hashrate is None:
            if self.count > 10000 and self.duration > 0:
                hashrate = self.get_hashrate()
            else:
                hashrate = self.estimate_hashrate()
        return self.get_expected_guesses() / hashrate
