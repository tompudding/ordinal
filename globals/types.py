import math, os


class FatalError(Exception):
    pass


def floordiv(a, b):
    return a // b


def floatdiv(a, b):
    return a / b


class Point(object):
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y
        self.iter_pos = 0

    def __add__(self, other_point):
        return Point(self.x + other_point.x, self.y + other_point.y)

    def __sub__(self, other_point):
        return Point(self.x - other_point.x, self.y - other_point.y)

    def __mul__(self, other_point):
        if isinstance(other_point, Point):
            return Point(self.x * other_point.x, self.y * other_point.y)
        else:
            return Point(self.x * other_point, self.y * other_point)

    def __truediv__(self, factor):
        op = floordiv
        if any((isinstance(item, float) for item in (self.x, self.y))):
            op = floatdiv
        if hasattr(factor, "x"):
            if any((isinstance(item, float) for item in (factor.x, factor.y))):
                op = floatdiv

            return Point(op(self.x, factor.x), op(self.y, factor.y))

        return Point(op(self.x, factor), op(self.y, factor))

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def __setitem__(self, index, value):
        setattr(self, ("x", "y")[index], value)

    def __iter__(self):
        return self

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "(%.2f,%.2f)" % (self.x, self.y)

    def __cmp__(self, other):
        try:
            # a = cmp(abs(self.x*self.y),abs(other.x*other.y))
            # if a != 0:
            #    return a
            a = cmp(self.x, other.x)
            if a != 0:
                return a
            return cmp(self.y, other.y)
        except AttributeError:
            return -1  # It's not equal if it's not a point

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def to_float(self):
        return Point(float(self.x), float(self.y))

    def to_int(self):
        return Point(int(self.x), int(self.y))

    def __next__(self):
        try:
            out = (self.x, self.y)[self.iter_pos]
            self.iter_pos += 1
        except IndexError:
            self.iter_pos = 0
            raise StopIteration
        return out

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def SquareLength(self):
        return self.x ** 2 + self.y ** 2

    def unit_vector(self):
        return self / self.length()

    def DistanceHeuristic(self, other):
        # return (other-self).diaglength()
        diff = other - self
        return (abs(diff.x) + abs(diff.y)) * 20
        # return diff.x**2 + diff.y**2

    def diaglength(self):
        return max(abs(self.x), abs(self.y))


class Directories:
    def __init__(self, base):
        self.resource = base
        for name in "tiles", "sprites", "foreground", "maps", "fonts":
            setattr(self, name, os.path.join(base, name))
