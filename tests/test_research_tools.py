from app.tools.research_tools import calculate, generate_study_plan, get_current_date


def test_calculate_handles_basic_expression() -> None:
    assert calculate.invoke({"expression": "(3 + 5) * 2"}) == "计算结果：16"


def test_calculate_rejects_python_code() -> None:
    assert calculate.invoke({"expression": "__import__('os').system('dir')"}).startswith("无法计算：")


def test_get_current_date_uses_china_standard_time() -> None:
    assert "中国标准时间：" in get_current_date.invoke({})


def test_generate_study_plan_has_requested_weeks() -> None:
    result = generate_study_plan.invoke(
        {"topic": "LangGraph", "duration_weeks": 2, "hours_per_week": 5}
    )
    assert "第 1 周" in result and "第 2 周" in result
