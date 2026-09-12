#!/usr/bin/env python3
"""Deterministic regression for the roll-photo/eye-overlay registration boundary."""

OFFSETS = {
    -25: (-32.5, 22.0), -20: (-30.0, 12.0), -15: (-24.0, 5.0),
    -10: (-16.5, 0.0), -5: (-9.5, -1.0), 0: (0.0, 0.0),
    5: (10.5, -29.0), 10: (22.0, -55.5), 15: (35.0, -77.5),
    20: (47.5, -97.0), 25: (62.5, -112.0),
}


def legacy_first_frame(old_roll, old_dx, old_dy, new_roll):
    dx, dy = OFFSETS[new_roll]
    return (
        old_roll + (new_roll - old_roll) * 0.4,
        old_dx + (dx - old_dx) * 0.4,
        old_dy + (dy - old_dy) * 0.4,
    )


def atomic_first_frame(new_roll):
    dx, dy = OFFSETS[new_roll]
    return float(new_roll), dx, dy


def mismatch(display, new_roll):
    dx, dy = OFFSETS[new_roll]
    r, x, y = display
    return abs(r - new_roll), abs(x - dx), abs(y - dy)


def main():
    # Every adjacent photo step becomes visible immediately in kopfRollTick().
    # Therefore the overlay must already be at the same measured state that frame.
    transitions = [(a, b) for a, b in zip(range(-25, 25, 5), range(-20, 30, 5))]
    legacy_nonzero = 0
    for old, new in transitions:
        ox, oy = OFFSETS[old]
        legacy = mismatch(legacy_first_frame(old, ox, oy, new), new)
        atomic = mismatch(atomic_first_frame(new), new)
        assert atomic == (0.0, 0.0, 0.0), (old, new, atomic)
        if any(v > 0 for v in legacy):
            legacy_nonzero += 1
        print(f"{old:+3d}->{new:+3d} legacy_mismatch={legacy} atomic_mismatch={atomic}")
    assert legacy_nonzero == len(transitions)

    # Concrete 0 -> +5 example: the old code leaves 60% of the required move
    # unapplied on the exact frame where the +5 photo is already visible.
    assert legacy_first_frame(0, 0.0, 0.0, 5) == (2.0, 4.2, -11.600000000000001)
    assert atomic_first_frame(5) == (5.0, 10.5, -29.0)
    print("PASS: atomic candidate has zero temporal registration error at every 5-degree photo step")


if __name__ == "__main__":
    main()
