import sys

from crax import Crax
from crax.commands import from_shell


app = Crax(settings="test_selenium.conf", debug=True)

if __name__ == "__main__":
    if sys.argv:
        from_shell(sys.argv, app.settings)
