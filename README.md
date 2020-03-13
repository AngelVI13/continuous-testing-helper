# zouk

<a href="https://travis-ci.org/eigenhombre/continuous-testing-helper"><img src="https://travis-ci.org/eigenhombre/continuous-testing-helper.svg?branch=master"></a>

Continuous task execution helper, forked from eigenhombre/continuous-testing-helper

**Any command supplied to the script will be run once and then
repeated any time a file in the current working directory changes,**
except for files excluded using `.zouk-excludes` as described below.

Note that ANY command you supply the script will be run, so be
careful.  You have been warned!

### Installation

    ./setup.py install  # from source
or

    pip install zouk  # use sudo if installing globally

### Usage examples

Create a zoukfile.py at the top level of the directory from which you are planning to execute zouk. The zoukfile should contain a dictionary with all the commands you wish to execute on a file change.

Example contents of a zoukfile.py:

    commands = {
        "black": "py -3 -m black {changed_files}",
        "flake8": "py -3 -m flake8 {changed_files}",
        "pytest": "py -3 -m pytest tests/",
    }

Then execute zouk from the same directory as the zoukfile.py

    zouk

Placing a file `.zouk-excludes` in the current working directory
will exclude subdirectories, e.g.:

    .svn$
    .git
    build
    vendor/elastic*
    install

will match files against the listed regular expressions and skip checking
for changes in those directories.  This can save quite a bit of time and CPU
during normal operation.

## Author

Angel ILIEV, [John Jacobsen](http://zerolib.com)

## License

Eclipse Public License

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF THIRD PARTY RIGHTS. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
