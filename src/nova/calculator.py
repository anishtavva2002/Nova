"""Restricted arithmetic evaluator. Never uses eval or exec."""
import ast
import operator

_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class CalculationError(ValueError):
    pass


def calculate(expression: str) -> int | float:
    if len(expression) > 120:
        raise CalculationError("Expression is too long.")
    try:
        root = ast.parse(expression, mode="eval")
        result = _visit(root.body, 0)
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise CalculationError("I couldn't calculate that expression.") from exc
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise CalculationError("Only numeric arithmetic is supported.")
    if abs(result) > 1e100:
        raise CalculationError("Result is outside the supported range.")
    return result


def _visit(node: ast.AST, depth: int) -> int | float:
    if depth > 20:
        raise CalculationError("Expression is too complex.")
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) > 1e100:
            raise CalculationError("Number is outside the supported range.")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _visit(node.left, depth + 1), _visit(node.right, depth + 1)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise CalculationError("Exponent is too large.")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_visit(node.operand, depth + 1))
    raise CalculationError("Only numbers and +, -, *, /, //, %, **, and parentheses are allowed.")
