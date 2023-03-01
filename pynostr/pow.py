import time
from dataclasses import dataclass

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
            print(f"Difficulty {self.num_leading_zero_bits} ")
        print(f"avg. hash rate {self.get_hashrate()} guesses per s")
        print(f"Total tries {self.count} s")
        print(f"Total duration {self.duration} s")


@dataclass
class PowEvent(Pow):
    difficulty: int = 8

    def __post_init__(self):
        self.mode = "event"
        self.operation = _guess_event
        self.n_options = 2
        self.n_pattern = self.difficulty
        self.reset()

    def reset(self):
        self.count = 1
        self.duration = 0
        self.results = []

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.n_pattern = self.difficulty

    def increase_difficulty(self):
        self.set_difficulty(self.difficulty + 1)

    def get_nonce_tag_pos(self, event: Event):
        tag_types = event.get_tag_types()
        tag_pos = 0
        if "nonce" not in tag_types:
            return -1
        for tt in tag_types:
            if tt == "nonce":
                break
            tag_pos += 1
        return tag_pos

    def calc_difficulty(self, event: Event):
        tag_pos = self.get_nonce_tag_pos(event)
        if tag_pos < 0:
            return 0
        return count_leading_zero_bits(event.id)

    def check_difficulty(self, event: Event):
        tag_pos = self.get_nonce_tag_pos(event)
        if tag_pos < 0:
            return False
        return (
            self.calc_difficulty(event) >= self.difficulty
            and int(event.tags[tag_pos][2]) >= self.difficulty
        )

    def mine(self, event: Event, max_count: int = 0, max_duration: int = 0) -> Event:
        start = time.perf_counter()
        count = 0
        duration = 0

        tag_pos = self.get_nonce_tag_pos(event)

        if tag_pos < 0:
            all_tags = [["nonce", "1", str(self.difficulty)]]
            all_tags.extend(event.tags)
            event.tags = all_tags
            tag_pos = 0
        elif event.tags[tag_pos][2] != str(self.difficulty):
            event.tags[tag_pos][2] = str(self.difficulty)
            event.tags[tag_pos][1] = "1"

        num_leading_zero_bits, event_pow = self.operation(event)
        num_leading_zero_bits_pow = num_leading_zero_bits
        while num_leading_zero_bits < self.difficulty and (
            not self._stop_mining(count, max_count, duration, max_duration)
        ):
            event.tags[tag_pos][1] = str(int(event.tags[tag_pos][1]) + 1)
            num_leading_zero_bits, event = self.operation(event)
            if num_leading_zero_bits > num_leading_zero_bits_pow:
                event_pow = event
                num_leading_zero_bits_pow = num_leading_zero_bits
            count += 1
            self.count += 1
            duration = time.perf_counter() - start
        end = time.perf_counter()
        self.duration += end - start
        if len(self.results) == 0:
            self.results.append((num_leading_zero_bits_pow, event_pow))
        elif self.results[-1][1].id != event_pow.id:
            self.results.append((num_leading_zero_bits_pow, event_pow))
        return event_pow

    def get_expected_time(self, hashrate=None) -> float:
        if hashrate is None:
            if self.count > 10000 and self.duration > 0:
                hashrate = self.get_hashrate()
            else:
                event = Event()
                hashrate = self.estimate_hashrate(event=event)
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
