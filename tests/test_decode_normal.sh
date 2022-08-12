SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd; )
TESTDIR=$( realpath "${SCRIPT_DIR}/data/Hemingway_Scans_300dpi"; )
TESTOUTPUT=$( realpath "${SCRIPT_DIR}/output/The_Old_Man_and_the_Sea_decoded.txt.gz"; )
DEBUGDIR=$( realpath "${SCRIPT_DIR}/output/debug"; )

rm -r "${DEBUGDIR}"
pawpyrus Decode -i "${TESTDIR}/1.JPG" "${TESTDIR}/2.JPG" "${TESTDIR}/3.JPG" "${TESTDIR}/4.JPG" "${TESTDIR}/5.JPG" "${TESTDIR}/6.JPG" "${TESTDIR}/7.JPG" "${TESTDIR}/8.JPG" "${TESTDIR}/9.JPG" -t "${TESTDIR}/unrecognized.txt" -o "${TESTOUTPUT}" -d "${DEBUGDIR}"
gzip -f -d "${TESTOUTPUT}"
