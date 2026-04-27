import json
import logging

from app.logging_config import JsonFormatter, request_id_var, timed, user_id_var


def test_formatter_emits_required_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    payload = json.loads(formatter.format(record))
    assert payload["severity"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "-"
    assert payload["user_id"] == "-"


def test_formatter_includes_extra_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname="", lineno=0, msg="m", args=(), exc_info=None
    )
    record.persona_id = "abc"
    record.duration_ms = 12.34
    payload = json.loads(formatter.format(record))
    assert payload["persona_id"] == "abc"
    assert payload["duration_ms"] == 12.34


def test_formatter_picks_up_context_vars():
    formatter = JsonFormatter()
    rid = request_id_var.set("rid-1")
    uid = user_id_var.set("user-2")
    try:
        record = logging.LogRecord(
            name="t", level=logging.INFO, pathname="", lineno=0, msg="m", args=(), exc_info=None
        )
        payload = json.loads(formatter.format(record))
        assert payload["request_id"] == "rid-1"
        assert payload["user_id"] == "user-2"
    finally:
        request_id_var.reset(rid)
        user_id_var.reset(uid)


def test_timed_logs_duration_on_success(caplog):
    log = logging.getLogger("app.timed.success")
    with caplog.at_level(logging.INFO, logger="app.timed.success"), timed(log, "op", k="v"):
        pass
    assert any(r.message == "op" for r in caplog.records)
    record = next(r for r in caplog.records if r.message == "op")
    assert hasattr(record, "duration_ms")
    assert record.k == "v"


def test_timed_logs_failure_and_reraises(caplog):
    log = logging.getLogger("app.timed.fail")

    class Boom(Exception):
        pass

    with caplog.at_level(logging.ERROR, logger="app.timed.fail"):
        try:
            with timed(log, "op"):
                raise Boom("nope")
        except Boom:
            pass

    assert any(r.message == "op_failed" for r in caplog.records)
