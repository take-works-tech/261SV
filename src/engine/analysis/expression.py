"""The expression language, evaluated without an interpreter behind it.

The language of formula units, condition units and computed quantities (`specs/13_scripting.md`). One
evaluator, and **no `eval`**: an expression evaluates identically whether or not scripting is enabled,
and a workspace from an untrusted source can be opened and its formulas read without running anything
(XC-101, XC-102).

Three properties this module is built around.

**Units travel** (XC-242). Every value carries a dimension - exponents over mass, length, time and
temperature - so a length divided by a time is a velocity, and a length added to a time is refused
naming both units (INV-002). A unit that carries an offset may be added, subtracted and compared and
may not be multiplied: doubling 20 degC gives 313.15 K one way and 586.3 K the other, and the gap is the
offset (E-141), so there is no answer to return that the product would not have invented.

**A bare number is undeclared, never assumed to match** (XC-003). It may scale a declared quantity and
it may not be compared with one: `stress > 200` is refused, because a threshold with no unit is the
mistake that reads as correct - the comparison succeeds, the verdict prints, and whether it meant
200 Pa or 200 MPa is nowhere in the record.

**An unbound name is refused when the expression is written, not when it runs** (pipeline/AC-032).
`check` does that pass; a study that fails at midnight on a name somebody could have seen was wrong is
the failure this exists to remove.

The syntax is spelled the way the language table spells it: `and or not`, `**` for the power, and the
conditional as `X if C else Y`. Attribute access, indexing, imports and assignment are absent - each of
them is a door out of the language and into the object model.

Specification: XC-242, XC-101, XC-003, 13_scripting.md, pipeline/AC-030 to AC-033.
"""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from domain_core.dimension import DIMENSIONLESS, Dimension, parse_symbol, symbol_for
from domain_core.reported_value import UNDECLARED_MARKER
from domain_core.units import Kind, kind_of, unit


class ExpressionError(Exception):
    """Raised for an expression that cannot be read, cannot be resolved, or cannot be evaluated.

    One exception type on purpose: to the person who wrote the expression, "this does not parse" and
    "these units do not combine" are the same event - the formula is wrong and the message says how.
    """


@dataclass(frozen=True, slots=True)
class Value:
    """A number, truth value or text, with what it is a quantity *of*.

    `magnitude` is in the internal unit of its dimension, always. `declared` keeps the symbol the user
    wrote so a refusal can name it back to them; `absolute` marks a point on an affine scale - 20 degC -
    as opposed to an interval along one.
    """

    magnitude: Any
    dimension: Dimension = DIMENSIONLESS
    declared: str | None = None
    absolute: bool = False

    @property
    def unit_name(self) -> str:
        """The unit the magnitude is **in**, which is always the internal one - or the marker.

        A value with no `declared` symbol is one **nobody declared a unit for**, which is not the same
        as a quantity that genuinely has none. A ratio of two declared lengths is dimensionless and
        prints as `1`; `2 * 3` is a pair of bare numbers and prints as undeclared. Conflating them makes
        every safety factor look like a stress whose unit went missing (XC-003, `reported_value`).


        Not the symbol the user wrote. An earlier version of this returned `declared or ...`, and the
        difference of two temperatures then printed as "5 degC" while holding 5 K, and the larger of
        1 MPa and 200 kPa printed as "1e+06 MPa" while holding 1e6 Pa. Both are a number shown in one
        unit and labelled with another - the failure this product exists not to commit - and both came
        from one field answering two questions.
        """
        if self.declared is None:
            return UNDECLARED_MARKER
        return symbol_for(self.dimension) or UNDECLARED_MARKER

    @property
    def written_unit(self) -> str:
        """The symbol the user wrote, for quoting their own input back at them in a refusal."""
        return self.declared or self.unit_name

    def describe(self) -> str:
        if isinstance(self.magnitude, (bool, str)):
            return str(self.magnitude)
        return f"{self.magnitude:g} {self.unit_name}".strip()


def quantity(magnitude: float, symbol: str | None = None, *, declaration: object = None) -> Value:
    """Build a bound value from a number and the unit somebody declared for it.

    `declaration` is anything carrying a `kind` - a @Variable, a @Field, a mapping read from a document -
    and it is read through `units.kind_of`, so absolute and difference are decided in one place
    (INV-028) rather than at each call.
    """
    if symbol is None:
        return Value(float(magnitude))
    known = unit(symbol)
    difference = kind_of(declaration) is Kind.DIFFERENCE
    internal = float(magnitude) * known.to_internal + (0.0 if difference else known.offset)
    return Value(
        internal, parse_symbol(symbol).dimension, symbol, absolute=bool(known.offset) and not difference
    )


# --------------------------------------------------------------------------------------------------
# Reading the text

_TOKEN = re.compile(
    r"(?P<space>\s+)"
    r"|(?P<number>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<text>'[^']*'|\"[^\"]*\")"
    r"|(?P<name>[A-Za-z_][A-Za-z_0-9]*)"
    r"|(?P<op>\*\*|==|!=|<=|>=|[-+*/%<>(),])"
)

#: Words the language spells for itself. A name may not be one of them, and a unit symbol may not
#: either - which is why the unit-after-a-number rule below has to check.
KEYWORDS = frozenset({"and", "or", "not", "if", "else", "true", "false"})


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    text: str
    at: int


def _tokens(source: str) -> list[_Token]:
    found: list[_Token] = []
    position = 0
    while position < len(source):
        match = _TOKEN.match(source, position)
        if match is None:
            raise ExpressionError(
                f"{position + 1} 文字目の '{source[position]}' はこの言語にない記号です：{source}"
            )
        position = match.end()
        if match.lastgroup == "space":
            continue
        found.append(_Token(match.lastgroup or "", match.group(), match.start()))
    return found


# --------------------------------------------------------------------------------------------------
# The tree


@dataclass(frozen=True, slots=True)
class Literal:
    value: Value


@dataclass(frozen=True, slots=True)
class Name:
    name: str
    at: int


@dataclass(frozen=True, slots=True)
class Unary:
    operator: str
    operand: Any


@dataclass(frozen=True, slots=True)
class Binary:
    operator: str
    left: Any
    right: Any


@dataclass(frozen=True, slots=True)
class Conditional:
    when_true: Any
    condition: Any
    when_false: Any


@dataclass(frozen=True, slots=True)
class Call:
    function: str
    arguments: tuple[Any, ...]
    at: int


class _Parser:
    """Precedence climbing, lowest binding first.

    Comparisons are **not** chainable. `a < b < c` reads as a range to a person and as `(a < b) < c` in
    the language this syntax is borrowed from, and the two disagree; refusing it costs a pair of
    parentheses and removes a silent wrong answer.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens = _tokens(source)
        self.position = 0

    def parse(self) -> Any:
        if not self.tokens:
            raise ExpressionError("式が空です")
        tree = self._conditional()
        if self.position < len(self.tokens):
            raise ExpressionError(
                f"式の末尾に余分な '{self.tokens[self.position].text}' があります：{self.source}"
            )
        return tree

    def _conditional(self) -> Any:
        tree = self._or()
        if self._at_keyword("if"):
            self.position += 1
            condition = self._or()
            if not self._at_keyword("else"):
                raise ExpressionError(f"条件式には else が必要です（X if C else Y）：{self.source}")
            self.position += 1
            return Conditional(tree, condition, self._conditional())
        return tree

    def _or(self) -> Any:
        tree = self._and()
        while self._at_keyword("or"):
            self.position += 1
            tree = Binary("or", tree, self._and())
        return tree

    def _and(self) -> Any:
        tree = self._not()
        while self._at_keyword("and"):
            self.position += 1
            tree = Binary("and", tree, self._not())
        return tree

    def _not(self) -> Any:
        if self._at_keyword("not"):
            self.position += 1
            return Unary("not", self._not())
        return self._comparison()

    def _comparison(self) -> Any:
        tree = self._sum()
        if self._at_op("==", "!=", "<", "<=", ">", ">="):
            operator = self.tokens[self.position].text
            self.position += 1
            tree = Binary(operator, tree, self._sum())
            if self._at_op("==", "!=", "<", "<=", ">", ">="):
                raise ExpressionError(
                    "比較は連ねられません。a < b < c は人には範囲に読め、言語には (a < b) < c と"
                    "読めます — 括弧で意図を書いてください"
                )
        return tree

    def _sum(self) -> Any:
        tree = self._product()
        while self._at_op("+", "-"):
            operator = self.tokens[self.position].text
            self.position += 1
            tree = Binary(operator, tree, self._product())
        return tree

    def _product(self) -> Any:
        tree = self._unary()
        while self._at_op("*", "/", "%"):
            operator = self.tokens[self.position].text
            self.position += 1
            tree = Binary(operator, tree, self._unary())
        return tree

    def _unary(self) -> Any:
        if self._at_op("-", "+"):
            operator = self.tokens[self.position].text
            self.position += 1
            return Unary(operator, self._unary())
        return self._power()

    def _power(self) -> Any:
        tree = self._atom()
        if self._at_op("**"):
            self.position += 1
            return Binary("**", tree, self._unary())
        return tree

    def _atom(self) -> Any:
        if self.position >= len(self.tokens):
            raise ExpressionError(f"式が途中で終わっています：{self.source}")
        token = self.tokens[self.position]
        self.position += 1

        if token.kind == "number":
            return Literal(self._with_unit(float(token.text)))
        if token.kind == "text":
            return Literal(Value(token.text[1:-1]))
        if token.kind == "op" and token.text == "(":
            tree = self._conditional()
            if not self._at_op(")"):
                raise ExpressionError(f"括弧が閉じていません：{self.source}")
            self.position += 1
            return tree
        if token.kind == "name":
            if token.text in ("true", "false"):
                return Literal(Value(token.text == "true"))
            if token.text in KEYWORDS:
                raise ExpressionError(f"'{token.text}' はここには置けません：{self.source}")
            if self._at_op("("):
                self.position += 1
                return Call(token.text, tuple(self._arguments()), token.at)
            return Name(token.text, token.at)
        raise ExpressionError(f"'{token.text}' はここには置けません：{self.source}")

    def _with_unit(self, magnitude: float) -> Value:
        """A number, and the unit written straight after it if there is one.

        An identifier immediately after a number can only be a unit: this language has no implicit
        multiplication, so `2 x` has no other reading. An unknown symbol in that position is refused
        rather than quietly taken as a name and multiplied by nothing.
        """
        if self.position < len(self.tokens):
            following = self.tokens[self.position]
            if following.kind == "name" and following.text not in KEYWORDS:
                self.position += 1
                try:
                    known = unit(following.text)
                except Exception as error:  # UndeclaredUnitError, already naming the symbol
                    raise ExpressionError(str(error)) from None
                return Value(
                    magnitude * known.to_internal + known.offset,
                    parse_symbol(following.text).dimension,
                    following.text,
                    absolute=bool(known.offset),
                )
        return Value(magnitude)

    def _arguments(self) -> Iterable[Any]:
        collected: list[Any] = []
        if self._at_op(")"):
            self.position += 1
            return collected
        while True:
            collected.append(self._conditional())
            if self._at_op(","):
                self.position += 1
                continue
            if self._at_op(")"):
                self.position += 1
                return collected
            raise ExpressionError(f"関数の引数が閉じていません：{self.source}")

    def _at_op(self, *texts: str) -> bool:
        token = self.tokens[self.position] if self.position < len(self.tokens) else None
        return token is not None and token.kind == "op" and token.text in texts

    def _at_keyword(self, word: str) -> bool:
        token = self.tokens[self.position] if self.position < len(self.tokens) else None
        return token is not None and token.kind == "name" and token.text == word


def parse(source: str) -> Any:
    """The expression as a tree, or a refusal saying where it stopped reading."""
    return _Parser(source).parse()


# --------------------------------------------------------------------------------------------------
# What the functions do to a unit

#: name -> (least arguments, most arguments or None for any number)
ARITY: dict[str, tuple[int, int | None]] = {
    "abs": (1, 1),
    "min": (1, None),
    "max": (1, None),
    "sum": (1, None),
    "mean": (1, None),
    "median": (1, None),
    "std": (2, None),
    "sqrt": (1, 1),
    "exp": (1, 1),
    "log": (1, 1),
    "log10": (1, 1),
    "sin": (1, 1),
    "cos": (1, 1),
    "tan": (1, 1),
    "atan2": (2, 2),
    "floor": (1, 1),
    "ceil": (1, 1),
    "round": (1, 2),
    "clamp": (3, 3),
}

#: The functions an affine value may be passed to. Everything else would multiply it somewhere
#: (E-141), or would return a number whose offset nobody can account for.
AFFINE_SAFE = frozenset({"abs", "min", "max", "clamp"})

#: Functions whose argument must be a plain number, because the series that defines them adds powers of
#: it together and only a dimensionless quantity may be added to its own square.
DIMENSIONLESS_ONLY = frozenset({"exp", "log", "log10", "sin", "cos", "tan"})

#: Functions over several values that require every one of them to be the same quantity.
SAME_UNIT = frozenset({"min", "max", "sum", "mean", "median", "std", "clamp", "atan2"})


def _number(value: Value, where: str) -> float:
    if isinstance(value.magnitude, (bool, str)):
        raise ExpressionError(f"{where} には数値が要ります（{value.describe()} が来ました）")
    return float(value.magnitude)


def _same_dimension(left: Value, right: Value, operation: str) -> None:
    if left.dimension == right.dimension:
        return
    raise ExpressionError(
        f"{operation} で単位が合いません：{left.written_unit} と {right.written_unit}。"
        "どちらかを換算するか、宣言を直してください（INV-002）"
    )


def _not_affine(value: Value, operation: str) -> None:
    if not value.absolute:
        return
    raise ExpressionError(
        f"{value.written_unit} はゼロ点をずらした単位なので {operation} できません。"
        "20 degC を 2 倍すると、先に倍にすれば 313.15 K、先に換算すれば 586.3 K になり、"
        "差の 273.15 K はオフセットそのものです（E-141）。"
        "差として扱う値は difference と宣言するか、K で書いてください"
    )


def _declared_against_bare(left: Value, right: Value, operation: str) -> None:
    """A bare number may scale a quantity and may not be compared or added to one (XC-003)."""
    if left.dimension.is_dimensionless == right.dimension.is_dimensionless:
        return
    declared = left if not left.dimension.is_dimensionless else right
    raise ExpressionError(
        f"{operation} の片側だけに単位があります（{declared.written_unit} と 単位なし）。"
        f"裸の数値は単位が宣言されていないものとして扱います — {declared.written_unit} を付けてください"
        "（XC-003）"
    )


# --------------------------------------------------------------------------------------------------
# Evaluating


def evaluate(source: str, bindings: Mapping[str, Value] | None = None) -> Value:
    """Evaluate an expression against the names bound at this point.

    Names are flat: a @Variable, a recorded quantity of the case in scope and the loop index are all
    reached by name, because attribute access is the door into the object model and this language does
    not have one.
    """
    return evaluate_tree(parse(source), bindings)


def evaluate_tree(tree: Any, bindings: Mapping[str, Value] | None = None) -> Value:
    bound = dict(bindings or {})

    def walk(node: Any) -> Value:
        if isinstance(node, Literal):
            return node.value
        if isinstance(node, Name):
            if node.name not in bound:
                raise ExpressionError(_unbound(node.name, bound))
            return bound[node.name]
        if isinstance(node, Unary):
            return _unary(node.operator, walk(node.operand))
        if isinstance(node, Conditional):
            condition = walk(node.condition)
            if not isinstance(condition.magnitude, bool):
                raise ExpressionError(
                    f"条件式の条件が真偽値ではありません（{condition.describe()}）"
                )
            return walk(node.when_true) if condition.magnitude else walk(node.when_false)
        if isinstance(node, Binary):
            if node.operator in ("and", "or"):
                return _boolean(node.operator, walk(node.left), walk(node.right))
            return _binary(node.operator, walk(node.left), walk(node.right))
        if isinstance(node, Call):
            return _call(node.function, [walk(argument) for argument in node.arguments])
        raise ExpressionError(f"評価できない節点です：{node!r}")

    return walk(tree)


def _unbound(name: str, bound: Mapping[str, Value]) -> str:
    known = "、".join(sorted(bound)) or "（この位置では何も束縛されていません）"
    return f"'{name}' はこの位置で束縛されていません。使えるのは：{known}"


def _unary(operator: str, operand: Value) -> Value:
    if operator == "not":
        if not isinstance(operand.magnitude, bool):
            raise ExpressionError(f"not は真偽値にのみ使えます（{operand.describe()}）")
        return Value(not operand.magnitude)
    if operator == "+":
        return operand
    _not_affine(operand, "符号反転")
    return Value(-_number(operand, "符号反転"), operand.dimension, operand.declared)


def _boolean(operator: str, left: Value, right: Value) -> Value:
    for side in (left, right):
        if not isinstance(side.magnitude, bool):
            raise ExpressionError(f"{operator} は真偽値にのみ使えます（{side.describe()}）")
    if operator == "or":
        return Value(bool(left.magnitude) or bool(right.magnitude))
    return Value(bool(left.magnitude) and bool(right.magnitude))


def _binary(operator: str, left: Value, right: Value) -> Value:
    if operator in ("==", "!="):
        if isinstance(left.magnitude, str) or isinstance(right.magnitude, str):
            if type(left.magnitude) is not type(right.magnitude):
                raise ExpressionError(
                    f"文字列と数値は比較できません（{left.describe()} と {right.describe()}）"
                )
            same = left.magnitude == right.magnitude
            return Value(same if operator == "==" else not same)

    if operator in ("==", "!=", "<", "<=", ">", ">="):
        _declared_against_bare(left, right, "比較")
        _same_dimension(left, right, "比較")
        a, b = _number(left, "比較"), _number(right, "比較")
        return Value(
            {"==": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[operator]
        )

    if operator == "+":
        _declared_against_bare(left, right, "加算")
        _same_dimension(left, right, "加算")
        if left.absolute and right.absolute:
            raise ExpressionError(
                f"{left.written_unit} の絶対値どうしは足せません（{left.describe()} + {right.describe()}）。"
                "点と点の和には意味がありません — 差を足すか、K で書いてください（INV-028）"
            )
        return Value(
            _number(left, "加算") + _number(right, "加算"),
            left.dimension,
            left.declared or right.declared,
            absolute=left.absolute or right.absolute,
        )

    if operator == "-":
        _declared_against_bare(left, right, "減算")
        _same_dimension(left, right, "減算")
        if right.absolute and not left.absolute:
            raise ExpressionError(
                f"絶対温度を差から引くことはできません（{left.describe()} - {right.describe()}）"
            )
        return Value(
            _number(left, "減算") - _number(right, "減算"),
            left.dimension,
            left.declared or right.declared,
            # absolute - absolute is an interval: the offsets cancel, and the result is a difference.
            absolute=left.absolute and not right.absolute,
        )

    if operator in ("*", "/", "%"):
        _not_affine(left, "乗除")
        _not_affine(right, "乗除")
        a, b = _number(left, "乗除"), _number(right, "乗除")
        declared = left.declared is not None and right.declared is not None
        if operator == "*":
            return _derived(a * b, left.dimension.times(right.dimension), from_declared=declared)
        if b == 0.0:
            raise ExpressionError("0 で割ることはできません")
        if operator == "/":
            return _derived(a / b, left.dimension.over(right.dimension), from_declared=declared)
        _same_dimension(left, right, "剰余")
        return Value(math.fmod(a, b), left.dimension, left.declared)

    if operator == "**":
        _not_affine(left, "べき乗")
        exponent = _number(right, "べき乗")
        if not right.dimension.is_dimensionless:
            raise ExpressionError(f"指数に単位は付けられません（{right.describe()}）")
        if exponent != int(exponent):
            if not left.dimension.is_dimensionless:
                raise ExpressionError(
                    f"{left.written_unit} を整数でない指数で累乗すると、この製品が表記できない単位に"
                    "なります。整数の指数か、無単位の値にしてください"
                )
            return Value(_number(left, "べき乗") ** exponent)
        return _derived(
            _number(left, "べき乗") ** int(exponent), left.dimension.power(int(exponent)),
            from_declared=left.declared is not None,
        )

    raise ExpressionError(f"演算子 '{operator}' はこの言語にありません")


def _derived(magnitude: float, dimension: Dimension, *, from_declared: bool) -> Value:
    """A value whose unit nobody wrote: the dimension names it, or nobody declared one.

    `from_declared` is whether the operands carried units. A ratio of two declared lengths is a declared
    dimensionless quantity and prints as `1`; a product of two bare numbers is still undeclared, and
    giving it `1` would be this module declaring a unit on somebody's behalf.
    """
    if not dimension.is_dimensionless:
        return Value(magnitude, dimension, symbol_for(dimension))
    return Value(magnitude, dimension, "1" if from_declared else None)


def _call(function: str, arguments: list[Value]) -> Value:
    if function not in ARITY:
        raise ExpressionError(
            f"関数 '{function}' はこの言語にありません。使えるのは：{'、'.join(sorted(ARITY))}"
        )
    least, most = ARITY[function]
    if len(arguments) < least or (most is not None and len(arguments) > most):
        wanted = f"{least} 個" if most == least else f"{least} 個以上"
        raise ExpressionError(f"{function} には引数が {wanted}要ります（{len(arguments)} 個来ました）")

    if function not in AFFINE_SAFE:
        for argument in arguments:
            _not_affine(argument, f"{function} に渡す")
    if function in SAME_UNIT:
        for other in arguments[1:]:
            _same_dimension(arguments[0], other, function)
    if function in DIMENSIONLESS_ONLY and not arguments[0].dimension.is_dimensionless:
        raise ExpressionError(
            f"{function} は無単位の値にのみ使えます（{arguments[0].written_unit} が来ました）"
        )

    numbers = [_number(argument, function) for argument in arguments]
    first = arguments[0]

    if function == "abs":
        return Value(abs(numbers[0]), first.dimension, first.declared, first.absolute)
    if function in ("min", "max"):
        chosen = min(numbers) if function == "min" else max(numbers)
        return Value(chosen, first.dimension, first.declared, first.absolute)
    if function == "sum":
        return Value(math.fsum(numbers), first.dimension, first.declared)
    if function == "mean":
        return Value(statistics.fmean(numbers), first.dimension, first.declared)
    if function == "median":
        return Value(statistics.median(numbers), first.dimension, first.declared)
    if function == "std":
        return Value(statistics.stdev(numbers), first.dimension, first.declared)
    if function == "sqrt":
        if numbers[0] < 0.0:
            raise ExpressionError(f"負の値の平方根は求められません（{first.describe()}）")
        halved = first.dimension.root()
        if halved is None:
            raise ExpressionError(
                f"{first.written_unit} の平方根は指数が半端になり、この製品に表記できる単位がありません"
            )
        return _derived(math.sqrt(numbers[0]), halved, from_declared=first.declared is not None)
    if function in DIMENSIONLESS_ONLY:
        if function in ("log", "log10") and numbers[0] <= 0.0:
            raise ExpressionError(f"{function} には正の値が要ります（{numbers[0]:g}）")
        return Value(getattr(math, function)(numbers[0]))
    if function == "atan2":
        return Value(math.atan2(numbers[0], numbers[1]))
    if function in ("floor", "ceil"):
        rounded = math.floor(numbers[0]) if function == "floor" else math.ceil(numbers[0])
        return Value(float(rounded), first.dimension, first.declared)
    if function == "round":
        digits = int(numbers[1]) if len(numbers) == 2 else 0
        return Value(round(numbers[0], digits), first.dimension, first.declared)
    if function == "clamp":
        low, high = numbers[1], numbers[2]
        if low > high:
            raise ExpressionError(f"clamp の下限が上限を超えています（{low:g} > {high:g}）")
        return Value(
            min(max(numbers[0], low), high), first.dimension, first.declared, first.absolute
        )
    raise ExpressionError(f"関数 '{function}' の実装がありません")


# --------------------------------------------------------------------------------------------------
# Refusing before it runs


def names_in(tree: Any) -> tuple[str, ...]:
    """Every name an expression references, in the order it first mentions them."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, Name):
            if node.name not in found:
                found.append(node.name)
        elif isinstance(node, Unary):
            walk(node.operand)
        elif isinstance(node, Binary):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, Conditional):
            walk(node.condition)
            walk(node.when_true)
            walk(node.when_false)
        elif isinstance(node, Call):
            for argument in node.arguments:
                walk(argument)

    walk(tree)
    return tuple(found)


def check(source: str, *, bound: Iterable[str] = ()) -> tuple[str, ...]:
    """Refuse an expression at edit time, or return the names it uses (pipeline/AC-032).

    Checked here: that it parses, that every function exists and is called with a workable number of
    arguments, and that **every name is bound at this point**. Not checked here: whether the units
    combine - that needs the values, and this pass has only the names.

    Refusing at edit time rather than at run time is the whole point. An expression that names something
    which is not there fails at midnight on a forty-case study, and the name was visible the moment
    somebody typed it.
    """
    tree = parse(source)
    available = set(bound)
    missing = [name for name in names_in(tree) if name not in available]
    if missing:
        listed = "、".join(f"'{name}'" for name in missing)
        known = "、".join(sorted(available)) or "（この位置では何も束縛されていません）"
        raise ExpressionError(
            f"{listed} はこの位置で束縛されていません。使えるのは：{known}。"
            "実行時ではなく書いた時点で拒否しています — 深夜の一括実行で落ちるのは名前の誤りとして"
            "最も高くつきます（AC-032）"
        )
    _check_calls(tree)
    return names_in(tree)


def _check_calls(node: Any) -> None:
    if isinstance(node, Call):
        if node.function not in ARITY:
            raise ExpressionError(
                f"関数 '{node.function}' はこの言語にありません。"
                f"使えるのは：{'、'.join(sorted(ARITY))}"
            )
        least, most = ARITY[node.function]
        if len(node.arguments) < least or (most is not None and len(node.arguments) > most):
            wanted = f"{least} 個" if most == least else f"{least} 個以上"
            raise ExpressionError(
                f"{node.function} には引数が {wanted}要ります（{len(node.arguments)} 個来ました）"
            )
        for argument in node.arguments:
            _check_calls(argument)
    elif isinstance(node, Unary):
        _check_calls(node.operand)
    elif isinstance(node, Binary):
        _check_calls(node.left)
        _check_calls(node.right)
    elif isinstance(node, Conditional):
        _check_calls(node.condition)
        _check_calls(node.when_true)
        _check_calls(node.when_false)
