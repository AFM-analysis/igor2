"""Test the CLI entry points."""
from pathlib import Path
import sys
from unittest.mock import Mock

import numpy
import pytest

from igor2.cli import igorbinarywave, igorpackedexperiment, script


DATA = Path(__file__).parent / "data"
COMMANDS = [
    (igorbinarywave, "mac-double.ibw"),
    (igorpackedexperiment, "polar-graphs-demo.pxp"),
]


@pytest.fixture
def no_matplotlib(monkeypatch):
    monkeypatch.setattr(script, "pyplot", None)


@pytest.mark.parametrize("filename", ["mac-double.ibw", "win-double.ibw"])
@pytest.mark.parametrize("to_file", [False, True])
def test_wavescript(filename, to_file, no_matplotlib, monkeypatch,
                    capsys, tmp_path):
    args = ["igorbinarywave", "-f", str(DATA / filename)]
    outfile = tmp_path / "wave.txt"
    if to_file:
        args += ["-o", str(outfile)]
    monkeypatch.setattr(sys, "argv", args)

    igorbinarywave.main()

    output = capsys.readouterr().out
    if to_file:
        assert output == ""
        output = outfile.read_text()
    assert output == "5\n4\n3\n2\n1\n"


@pytest.mark.parametrize("to_file", [False, True])
def test_packedscript(to_file, no_matplotlib, monkeypatch, capsys, tmp_path):
    args = ["igorpackedexperiment", "-f",
            str(DATA / "polar-graphs-demo.pxp")]
    outfile = tmp_path / "records.txt"
    if to_file:
        args += ["-o", str(outfile)]
    monkeypatch.setattr(sys, "argv", args)

    igorpackedexperiment.main()

    output = capsys.readouterr().out
    if to_file:
        assert output == ""
        output = outfile.read_text()
    assert output.startswith("[<UnknownRecord-11 ")
    assert output.count("<WaveRecord ") == 8
    assert output.endswith(">]\n")


def test_empty_packedscript(no_matplotlib, monkeypatch, capsys, tmp_path):
    infile = tmp_path / "empty.pxp"
    infile.write_bytes(b"")
    args = ["igorpackedexperiment", "-f", str(infile)]
    monkeypatch.setattr(sys, "argv", args)

    igorpackedexperiment.main()

    assert capsys.readouterr().out == "[]\n"


@pytest.mark.parametrize("command,filename", COMMANDS)
def test_plot_requires_matplotlib(command, filename, no_matplotlib,
                                  monkeypatch):
    args = ["igor", "-f", str(DATA / filename), "-p"]
    monkeypatch.setattr(sys, "argv", args)

    with pytest.raises(ValueError, match="install `matplotlib` for plotting"):
        command.main()


@pytest.mark.parametrize("command,filename", COMMANDS)
@pytest.mark.parametrize("option", ["--help", "--version"])
def test_cli_information(command, filename, option, no_matplotlib,
                         monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["igor", option])

    with pytest.raises(SystemExit) as exc:
        command.main()

    assert exc.value.code == 0
    output = capsys.readouterr().out
    if option == "--help":
        assert "--plot" in output
    else:
        assert script.__version__ in output


@pytest.mark.parametrize("command,filename", COMMANDS)
def test_missing_input(command, filename, no_matplotlib, monkeypatch,
                       capsys, tmp_path):
    monkeypatch.setattr(sys, "argv", ["igor", "-f", str(tmp_path / filename)])

    with pytest.raises(FileNotFoundError):
        command.main()

    assert capsys.readouterr().out == ""


def test_wavescript_plot(monkeypatch, capsys):
    pyplot = Mock()
    monkeypatch.setattr(script, "pyplot", pyplot)
    args = ["igorbinarywave", "-p", "-f", str(DATA / "mac-double.ibw")]
    monkeypatch.setattr(sys, "argv", args)

    igorbinarywave.main()

    assert capsys.readouterr().out == "5\n4\n3\n2\n1\n"
    pyplot.figure.assert_called_once_with()
    axes = pyplot.figure.return_value.add_subplot.return_value
    values, style = axes.plot.call_args[0]
    numpy.testing.assert_array_equal(values, [5, 4, 3, 2, 1])
    assert style == "r."
    pyplot.show.assert_called_once_with()


def test_no_plot_does_not_show(monkeypatch, capsys):
    pyplot = Mock()
    monkeypatch.setattr(script, "pyplot", pyplot)
    args = ["igorbinarywave", "-f", str(DATA / "mac-double.ibw")]
    monkeypatch.setattr(sys, "argv", args)

    igorbinarywave.main()

    assert capsys.readouterr().out == "5\n4\n3\n2\n1\n"
    pyplot.figure.assert_not_called()
    pyplot.show.assert_not_called()
