SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd; )
PAWPYRUS=$( realpath "${SCRIPT_DIR}/../pawpyrus"; )
TESTFILE=$( realpath "${SCRIPT_DIR}/data/The_Old_Man_and_the_Sea.txt.gz"; )
TESTOUTPUT=$( realpath "${SCRIPT_DIR}/output/The_Old_Man_and_the_Sea_encoded.pdf"; )
JOBNAME="The Old Man and the Sea by Ernest Hemingway"

pawpyrus Encode -n "${JOBNAME}" -i "${TESTFILE}" -o "${TESTOUTPUT}" -c 7 -r 10
