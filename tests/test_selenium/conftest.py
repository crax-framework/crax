from pytest import fixture


def pytest_addoption(parser):
    parser.addoption("--threads", action="store")
    parser.addoption("--delay", action="store")
    parser.addoption("--executable", action="store")


@fixture()
def threads(request):
    return request.config.getoption("--threads")

@fixture()
def delay(request):
    return request.config.getoption("--delay")

@fixture()
def executable(request):
    return request.config.getoption("--executable")
