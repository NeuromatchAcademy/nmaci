from subprocess import run
from pytest import fixture


@fixture
def cmd():
    return ["python", "scripts/process_notebooks.py"]


def test_raises_not_implemented_error(cmd):

    nb = "tutorials/raises_notimplemented_error.ipynb"
    cmdline = cmd + ["--check-only", "--execute", nb]
    res = run(cmdline, capture_output=True)
    assert not res.returncode
    assert nb in res.stdout.decode("utf-8")


def test_raises_name_error(cmd):

    nb = "tutorials/raises_name_error.ipynb"
    cmdline = cmd + ["--check-only", "--execute", nb]
    res = run(cmdline, capture_output=True)
    assert res.returncode
    assert nb in res.stdout.decode("utf-8")
    assert nb in res.stderr.decode("utf-8")
    assert "NameError" in res.stderr.decode("utf-8")


def test_executed_out_of_order(cmd):

    nb = "tutorials/executed_out_of_order.ipynb"
    cmdline = cmd + ["--check-only", nb]
    res = run(cmdline, capture_output=True)
    assert res.returncode
    assert nb in res.stderr.decode("utf-8")
    assert "not sequentially executed" in res.stderr.decode("utf-8")


def test_executed_partially(cmd):

    nb = "tutorials/executed_partially.ipynb"
    cmdline = cmd + ["--check-only", "--check-execution", nb]
    res = run(cmdline, capture_output=True)
    assert res.returncode
    assert nb in res.stderr.decode("utf-8")
    assert "has unexecuted code cell(s)" in res.stderr.decode("utf-8")


def test_executed_with_error(cmd):

    nb = "tutorials/executed_with_error.ipynb"
    cmdline = cmd + ["--check-only", "--check-execution", nb]
    res = run(cmdline, capture_output=True)
    assert res.returncode
    assert nb in res.stderr.decode("utf-8")
    assert "NameError" in res.stderr.decode("utf-8")


def test_executed_successfully(cmd):

    nb = "tutorials/executed_successfully.ipynb"
    cmdline = cmd + ["--check-only", "--check-execution", nb]
    res = run(cmdline, capture_output=True)
    assert not res.returncode
    assert nb in res.stdout.decode("utf-8")
