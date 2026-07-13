"""Small, deterministic tools for the first Agent milestone."""

import ast
import operator
from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CHINA_STANDARD_TIME = timezone(timedelta(hours=8))


def _evaluate_expression(node: ast.expr) -> int | float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_expression(node.left)
        right = _evaluate_expression(node.right)
        if isinstance(node.op, ast.Pow) and (abs(left) > 1_000 or abs(right) > 10):
            raise ValueError("幂运算的数值过大。")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_expression(node.operand))
    raise ValueError("只支持数字、括号和 + - * / // % ** 运算符。")


@tool
def calculate(expression: str) -> str:
    """计算一个只含数字、括号和基本算术运算符的数学表达式。"""
    if len(expression) > 200:
        return "表达式过长，最多允许 200 个字符。"
    try:
        tree = ast.parse(expression, mode="eval")
        value = _evaluate_expression(tree.body)
    except (SyntaxError, ValueError, ZeroDivisionError) as error:
        return f"无法计算：{error}"
    return f"计算结果：{value}"


@tool
def get_current_date() -> str:
    """获取中国标准时间（UTC+8）下的当前日期和星期。"""
    now = datetime.now(_CHINA_STANDARD_TIME)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"中国标准时间：{now:%Y-%m-%d}，{weekdays[now.weekday()]}"


@tool
def generate_study_plan(topic: str, duration_weeks: int = 4, hours_per_week: int = 6) -> str:
    """为一个主题生成按周划分的基础学习计划。适合学习计划、阅读安排和复习计划。"""
    topic = topic.strip()
    if not topic:
        return "学习主题不能为空。"
    if not 1 <= duration_weeks <= 12:
        return "学习周期需在 1 到 12 周之间。"
    if not 1 <= hours_per_week <= 40:
        return "每周学习时长需在 1 到 40 小时之间。"
    stages = ["建立基础与关键词", "精读核心材料", "实践与整理笔记", "复盘与输出"]
    items = [
        f"第 {week} 周（约 {hours_per_week} 小时）：{stages[(week - 1) % len(stages)]}，围绕「{topic}」完成一个可检查的小产出。"
        for week in range(1, duration_weeks + 1)
    ]
    return "基础学习计划：\n" + "\n".join(items)


RESEARCH_TOOLS = [calculate, get_current_date, generate_study_plan]
