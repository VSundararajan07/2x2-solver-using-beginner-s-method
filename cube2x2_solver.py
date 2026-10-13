#!/usr/bin/env python3
"""
2x2 Rubik's Cube solver using the beginner's method.

Run it, then type in the colours of each face (2 rows of 2 letters per face).

Stages
  1. First layer   : place the 4 bottom-colour corners with R U R' U' (plus cube turns 'y')
  2. Orient last   : make the whole top face one colour (Sune / Anti-Sune)
  3. Permute last  : move corners to their spots (adjacent swap / diagonal swap)
  4. Align         : final U turns

Notation: R U F = clockwise face turns, ' = counter-clockwise, 2 = half turn,
y = turn the whole cube like a U turn.
"""
import itertools
import random

# ----------------------------------------------------------------------------
# Stored algorithms (the "case -> algorithm" knowledge)
# ----------------------------------------------------------------------------
SEXY = "R U R' U'"                                    # first-layer corner insert
SUNE = "R U R' U R U2 R'"                             # orientation
ADJ_SWAP = "R U R' U' R' F R2 U' R' U' R U R' F'"     # permutation (T-perm)

# ----------------------------------------------------------------------------
# Cube model: 24 stickers, each at (corner position, face normal)
# x = right, y = up, z = front
# ----------------------------------------------------------------------------
FACES = {"U": (1, 1), "D": (1, -1), "R": (0, 1), "L": (0, -1), "F": (2, 1), "B": (2, -1)}
NORMAL = {f: tuple(s if i == a else 0 for i in range(3)) for f, (a, s) in FACES.items()}
FACE_OF = {n: f for f, n in NORMAL.items()}
SOLVED_COLORS = {"U": "Y", "D": "W", "F": "G", "B": "B", "R": "O", "L": "R"}  # only for tests

POSITIONS = list(itertools.product((-1, 1), repeat=3))
STICKERS = [(p, tuple(p[i] if i == a else 0 for i in range(3)))
            for p in POSITIONS for a in range(3)]
INDEX = {s: i for i, s in enumerate(STICKERS)}
CORNER_FACES = {p: [FACE_OF[n] for q, n in STICKERS if q == p] for p in POSITIONS}

DFR, UFR, DFL = (1, -1, 1), (1, 1, 1), (-1, -1, 1)
TOP = [(1, 1, 1), (-1, 1, 1), (-1, 1, -1), (1, 1, -1)]


def rot(v, axis, turns):
    """Rotate vector v by 90 degrees * turns about +axis (right-hand rule)."""
    x, y, z = v
    for _ in range(turns % 4):
        if axis == 0:
            x, y, z = x, -z, y
        elif axis == 1:
            x, y, z = z, y, -x
        else:
            x, y, z = -y, x, z
    return (x, y, z)


def _permutation(axis, sign, turns, whole_cube):
    perm = []
    for pos, nor in STICKERS:
        if whole_cube or pos[axis] == sign:
            new = (rot(pos, axis, turns), rot(nor, axis, turns))
        else:
            new = (pos, nor)
        perm.append(INDEX[new])
    return perm


MOVES = {}
for _f, (_a, _s) in FACES.items():                   # clockwise as seen from outside
    MOVES[_f] = _permutation(_a, _s, -_s, False)
for _r, _f in zip("xyz", "RUF"):                     # whole-cube rotations
    _a, _s = FACES[_f]
    MOVES[_r] = _permutation(_a, _s, -_s, True)

TURNS = {"": 1, "2": 2, "'": 3}
SUFFIX = {1: "", 2: "2", 3: "'"}

# ----------------------------------------------------------------------------
# Input layout: each face is a 2x2 grid [[a, b], [c, d]] drawn in the usual net
#
#            U
#          L F R B
#            D
#
# U: back edge at the top of the grid.   L, F, R, B: U edge at the top.
# D: front edge at the top of the grid.
# ----------------------------------------------------------------------------
FACE_ORDER = ["U", "L", "F", "R", "B", "D"]


def grid_position(face, row, col):
    """Corner position of the sticker at (row, col) of a face grid."""
    top, left = row == 0, col == 0
    y = 1 if top else -1
    if face == "F":
        return (-1 if left else 1, y, 1)
    if face == "B":
        return (1 if left else -1, y, -1)
    if face == "R":
        return (1, y, 1 if left else -1)
    if face == "L":
        return (-1, y, -1 if left else 1)
    x = -1 if left else 1
    if face == "U":
        return (x, 1, -1 if top else 1)
    return (x, -1, 1 if top else -1)          # D


class Cube:
    def __init__(self, state=None):
        self.s = state[:] if state else [SOLVED_COLORS[FACE_OF[n]] for _, n in STICKERS]

    @classmethod
    def from_faces(cls, faces):
        state = [None] * 24
        for face, grid in faces.items():
            for r in range(2):
                for c in range(2):
                    state[INDEX[(grid_position(face, r, c), NORMAL[face])]] = grid[r][c]
        return cls(state)

    def to_faces(self):
        return {f: [[self.at(grid_position(f, r, c), f) for c in range(2)] for r in range(2)]
                for f in FACE_ORDER}

    def copy(self):
        return Cube(self.s)

    def apply(self, alg):
        for tok in alg.split():
            perm = MOVES[tok[0]]
            for _ in range(TURNS[tok[1:]]):
                new = self.s[:]
                for i, j in enumerate(perm):
                    new[j] = self.s[i]
                self.s = new
        return self

    def at(self, pos, face):
        return self.s[INDEX[(pos, NORMAL[face])]]

    def colors(self, pos):
        return {self.at(pos, f) for f in CORNER_FACES[pos]}

    def find(self, colors):
        """Position of the corner piece made of exactly these colours."""
        return next(p for p in POSITIONS if self.colors(p) == colors)

    def is_solved(self):
        return all(len({self.s[i] for i, (_, n) in enumerate(STICKERS) if n == NORMAL[f]}) == 1
                   for f in FACES)


def opposite_colors(cube):
    """Opposite pairs = colours that never share a corner. Raises ValueError if the input is impossible."""
    colors = sorted(set(cube.s))
    if len(colors) != 6 or any(cube.s.count(c) != 4 for c in colors):
        raise ValueError("You need exactly 6 colours, each used on exactly 4 stickers.")
    touching = {c: set() for c in colors}
    pieces = set()
    for p in POSITIONS:
        cs = cube.colors(p)
        if len(cs) != 3:
            raise ValueError("A corner has the same colour twice - that can't happen on a real cube.")
        pieces.add(frozenset(cs))
        for a, b in itertools.permutations(cs, 2):
            touching[a].add(b)
    if len(pieces) != 8:
        raise ValueError("Two corners have the same colours - check for a typo.")
    opp = {}
    for c in colors:
        rest = set(colors) - touching[c] - {c}
        if len(rest) != 1:
            raise ValueError("These colours don't form a valid cube - check for a typo.")
        opp[c] = rest.pop()
    if any(opp[opp[c]] != c for c in colors):
        raise ValueError("These colours don't form a valid cube - check for a typo.")
    return opp


# ----------------------------------------------------------------------------
# Solver
# ----------------------------------------------------------------------------
class Solver:
    def __init__(self, cube, bottom="W"):
        self.cube = cube
        self.stages = {}
        self.opp = opposite_colors(cube)
        if bottom not in self.opp:
            raise ValueError("No white found - use the letter W for the white stickers.")
        self.bottom = bottom
        self.top = self.opp[bottom]

    def do(self, stage, alg):
        self.cube.apply(alg)
        self.stages.setdefault(stage, []).extend(alg.split())

    def apply_cases(self, stage, algs, is_done, max_depth=3):
        """Try the stored algorithms (each preceded by a U turn to line up the case)
        until `is_done` holds. Shortest sequence of up to `max_depth` algorithms wins."""
        if is_done(self.cube):
            return
        options = [f"{pre} {alg}" for alg in algs for pre in ("", "U", "U2", "U'")]
        for depth in range(1, max_depth + 1):
            for seq in itertools.product(options, repeat=depth):
                trial = self.cube.copy()
                for step in seq:
                    trial.apply(step)
                if is_done(trial):
                    for step in seq:
                        self.do(stage, step)
                    return
        raise RuntimeError(f"{stage}: no sequence found")

    # ---- stage 1: first layer ---------------------------------------------
    def bottom_down(self):
        return self.cube.at(DFR, "D") == self.bottom

    def insert_corner(self, target):
        """Bring the corner made of `target` colours into DFR, bottom colour facing down."""
        c = self.cube
        for _ in range(12):
            pos = c.find(target)
            if pos == DFR and self.bottom_down():
                return
            if pos[1] == -1:                         # stuck in the bottom layer: pop it out
                m = next(m for m in range(4) if rot(pos, 1, 3 * m) == DFR)
                to = ["", "y", "y2", "y'"][m]
                back = ["", "y'", "y2", "y"][m]
                self.do("First layer", f"{to} {SEXY} {back}")
                continue
            while c.find(target) != UFR:             # top layer: line it up above the slot
                self.do("First layer", "U")
            for _ in range(6):                       # repeat R U R' U' until it drops in
                self.do("First layer", SEXY)
                if c.find(target) == DFR and self.bottom_down():
                    return
        raise RuntimeError("could not insert a first-layer corner")

    def first_layer(self, first):
        c = self.cube
        for k in range(4):
            if k == 0:
                target = first
            else:  # next corner is determined by the solved one now sitting at DFL
                target = {self.bottom, c.at(DFL, "F"), self.opp[c.at(DFL, "L")]}
            self.insert_corner(target)
            if k < 3:
                self.do("First layer", "y")          # move solved corners out of the way

    def best_first_corner(self):
        """Try each bottom-colour corner as the starting corner; keep the cheapest."""
        best = None
        for p in POSITIONS:
            colors = self.cube.colors(p)
            if self.bottom not in colors:
                continue
            trial = Solver(self.cube.copy(), self.bottom)
            trial.first_layer(colors)
            cost = len(simplify(trial.stages.get("First layer", [])))
            if best is None or cost < best[0]:
                best = (cost, colors)
        return best[1]

    # ---- stage 2: orient the last layer -----------------------------------
    def oriented(self, cube):
        return sum(cube.at(p, "U") == self.top for p in TOP)

    def orient_last_layer(self):
        self.apply_cases("Orient last layer", (SUNE,),
                         lambda cube: self.oriented(cube) == 4)

    # ---- stage 3: permute the last layer ----------------------------------
    def headlights(self, cube):
        """Number of side faces whose two top stickers match."""
        n = 0
        for f in "FRBL":
            axis, sign = FACES[f]
            a, b = [p for p in TOP if p[axis] == sign]
            n += cube.at(a, f) == cube.at(b, f)
        return n

    def permute_last_layer(self):
        self.apply_cases("Permute last layer", (ADJ_SWAP,),
                         lambda cube: self.headlights(cube) == 4)

    # ---- stage 4: final alignment -----------------------------------------
    def align(self):
        for _ in range(4):
            if self.cube.is_solved():
                return
            self.do("Final alignment", "U")
        raise RuntimeError("cube not solved")

    def solve(self):
        if not self.cube.is_solved():
            self.first_layer(self.best_first_corner())
            self.orient_last_layer()
            self.permute_last_layer()
            self.align()
        return {k: simplify(v) for k, v in self.stages.items()}


def simplify(tokens):
    """Merge neighbouring turns of the same face: U U -> U2, R R' -> nothing."""
    out = []
    for tok in tokens:
        face, n = tok[0], TURNS[tok[1:]]
        if out and out[-1][0] == face:
            n = (out.pop()[1] + n) % 4
            if n == 0:
                continue
        out.append((face, n))
    return [f + SUFFIX[n] for f, n in out]


# ----------------------------------------------------------------------------
# Input / output
# ----------------------------------------------------------------------------
INSTRUCTIONS = """\
Enter the colours of each face. Use one letter per colour (e.g. W Y G B O R).
Each face is 2 rows of 2 letters, drawn like this (hold the cube with U on top, F facing you):

            U
          L F R B
            D

  U: look from above, with the B side at the top of your drawing
  L, F, R, B: look straight at the face, with U at the top
  D: look from below, with the F side at the top of your drawing

Example for a solved cube:  U = YY / YY,  L = RR / RR,  F = GG / GG, ...
"""


def read_cube():
    faces = {}
    for f in FACE_ORDER:
        rows = []
        for r in (1, 2):
            while True:
                raw = input(f"{f} face, row {r}: ").replace(" ", "").upper()
                if len(raw) == 2:
                    break
                print("  Please enter exactly 2 letters, e.g. WY")
            rows.append(list(raw))
        faces[f] = rows
    return Cube.from_faces(faces)


def main():
    print(INSTRUCTIONS)
    while True:
        cube = read_cube()
        try:
            stages = Solver(cube).solve()
            break
        except (ValueError, RuntimeError) as err:
            print(f"\nProblem: {err}\nThat cube can't be solved as entered - let's try again.\n")

    print("\nHold the cube with U on top and F facing you. 'y' = turn the whole cube like a U turn.\n")
    if not stages:
        print("Already solved!")
        return
    for stage, moves in stages.items():
        print(f"{stage + ':':<22}{' '.join(moves)}")
    total = sum(1 for m in stages.values() for t in m if t[0] != "y")
    print(f"\n{total} face turns in total.")


# ----------------------------------------------------------------------------
# Optional self-test (call from a Python shell: self_test(500))
# ----------------------------------------------------------------------------
def random_scramble(length=20, faces="URFDLB"):
    moves, prev = [], ""
    for _ in range(length):
        f = random.choice([x for x in faces if x != prev])
        moves.append(f + random.choice(["", "2", "'"]))
        prev = f
    return " ".join(moves)


def self_test(n=500):
    letters = list("WYGBOR")
    for _ in range(n):
        random.shuffle(letters)               # any colour scheme should work
        names = dict(zip("WYGBOR", letters))
        cube = Cube().apply(random_scramble())
        relabelled = {f: [[names[x] for x in row] for row in g] for f, g in cube.to_faces().items()}
        cube = Cube.from_faces(relabelled)
        Solver(cube).solve()
        assert cube.is_solved()
    print(f"{n} random scrambles solved.")


if __name__ == "__main__":
    main()
