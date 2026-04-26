"""Smoke test: graph compiles and has expected nodes."""


def test_graph_compiles():
    from src.graph import build_graph

    graph = build_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    from src.graph import build_graph

    graph = build_graph()
    node_names = set(graph.get_graph().nodes.keys())
    expected = {
        "intake", "dedupe_check", "qualify_company", "find_contact",
        "gather_signals", "extract_hooks", "load_memory",
        "draft_email", "evaluate", "reflect_on_failure",
        "human_review", "persist_episodic",
    }
    assert expected.issubset(node_names)


def test_qualify_routes_to_persist_on_failure():
    from src.graph import _route_after_qualify

    state = {"qualification_passed": False}
    assert _route_after_qualify(state) == "persist_episodic"


def test_qualify_routes_to_find_contact_on_pass():
    from src.graph import _route_after_qualify

    state = {"qualification_passed": True}
    assert _route_after_qualify(state) == "find_contact"


def test_eval_routes_to_retry_on_fail():
    from src.graph import _route_after_eval

    state = {"eval_passed": False, "attempt_count": 1}
    assert _route_after_eval(state) == "reflect_on_failure"


def test_eval_routes_to_human_review_when_max_attempts_reached():
    from src.graph import _route_after_eval

    state = {"eval_passed": False, "attempt_count": 3}
    assert _route_after_eval(state) == "human_review"


def test_eval_routes_to_human_review_on_pass():
    from src.graph import _route_after_eval

    state = {"eval_passed": True, "attempt_count": 1}
    assert _route_after_eval(state) == "human_review"
