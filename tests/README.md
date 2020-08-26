# CRAX Tests
## Explanation of Crax Framework testing 
Here explained what is Crax tests, how you should launch test, what have been tested,
what was missed and why and finally here described tests structure.

### Test files
The entry point to launch tests is `launch_tests.sh` script. It is simple bash script
file that launches tests one by one. Crax is supposed to be able to work with several
database backends e.g. `MySQL`, `PostgreSQL` and `SQLite`. Thus all tests have to run
against all of backends listed above. Launcher starts test files in right order for all
database backend. If any errors found on any step launcher stops it's job and 
exited. What does `right order` mean: First is to check all database depended stuff.
Tests that written to check commands are chained to prepare python executables for
next part of tests. For example `command_two.py` runs it's tests and prepares files
for `command_three.py`. All sources for this kind of tests are placed in
 `app_*` directories. It is necessary to run something like migration tests. All
test files that will be launched by `launch_tests.sh` are stored in `test_files` 
directory. First will be called all of `command_?.py` files. All commands will be
tested against all of database backends. Next step is to test `authentication` against
all of database backends. And finally will be launched common tests which are
database independent. Why so? It is about ability to work without database backend
at all. Any Crax application could be built without database, models, authentication
and so on. 

### Config files
All config files for all common tests. Config files for command testing are placed
in `app_*` directories.

### Test app auth
All source files for testing authentication backend. However config files are in
`config_files` directory.

### Test app common
All files that serves common application tests are stored here. Also here placed
python file named `urls_two_apps.py` - it is file with all common test urls including
nested apps tests.

### Test app nested
It is a part of common tests that shows how nested apps, namespaces and url resolving
for nested applications should work. Another one goal is to show that does not matter
how some of files are named. Three levels of this directory contain crax applications
with files like `controllers.py`, `handlers.py` or `views.py` that do the same things.