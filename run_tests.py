import os
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_dir, "modules"))

import difflib
import argparse
import platform
from subprocess import check_output, PIPE, TimeoutExpired
from cparser import main as parse
from scanner import main as scan

'''
Expected folder structure for automatic testing

project_root
    ├── input.txt
    ├── scanner.py
    ├── parser.py
    ├── run_tests.py
    └── tests
        ├── T1
        │   ├── input.txt
        │   ├── parse_tree.txt
        │   └── syntax_errors.txt
        ├── T2
        │   ├── input.txt
        │   ├── parse_tree.txt
        │   └── syntax_errors.txt
        
        .
        .
        .

        └── TN
            ├── input.txt
            ├── parse_tree.txt
            └── syntax_errors.txt
'''

parser = argparse.ArgumentParser(description='Automatic test case runner for Compilers course exercises.')
parser.add_argument('-v', '--verbose', action='store_true', help='Print difference info between actual and model output.')
parser.add_argument('--from-test', type=int, default=0, help='Test number to start from')
parser.add_argument('--to-test', type=int, default=None, help='Test number to stop to')
args = parser.parse_args()

test_dir = os.path.join(script_dir, "tests")

passes = 0
tests = 0
i = 0

def check_diff(test_case, test_file, model_answer, output):
    if model_answer != output:
        if args.verbose:
            diff = difflib.ndiff(model_answer.splitlines(keepends=True), 
                                output.splitlines(keepends=True))
            print("".join(diff), end="")
            print("\n======")
        if test_file:
            print(f"{test_case}: {test_file} output differs from model output!")
        else:
            print(f"{test_case}: Tester output differs from model output!")
        print("------")
        return True
    return False


for test_case in sorted(os.listdir(test_dir)):
    if args.to_test and i >= args.to_test:
        break
    if i < args.from_test - 1:
        i += 1
        continue
    test_case_dir = os.path.join(test_dir, test_case)
    output_dir = os.path.join(script_dir, "output")
    test_files = list(os.listdir(test_case_dir))
    input_file = os.path.join(test_case_dir, test_files.pop(test_files.index("input.txt")))

    try:
        if test_case.startswith("TS"):
            scan(input_file)
        else:
            parse(input_file)
    except Exception as e:
        # raise e
        print("Execution failed:", str(e))
        fail = True
    else:
        fail = False

    if not fail:
        if test_case.startswith("TXX"):
            plat = platform.system()
            if plat == "Windows":
                tester_file = os.path.join(script_dir, "interpreter", "tester_Windows.exe")
            elif plat == "Linux":
                tester_file = os.path.join(script_dir, "interpreter", "tester_Linux.out")
            elif plat == "Darwin":
                tester_file = os.path.join(script_dir, "interpreter", "tester_Mac.out")
            else:
                raise RuntimeError("Unsupported operating system for code execution!")
            model_output_file = os.path.join(test_case_dir, "output.txt")
            output_file = os.path.join(script_dir, "output", "output.txt")
            if not os.path.exists(output_file):
                fail = True
            else:
                with open(model_output_file, "r", encoding="utf-8") as f:
                    model_output = f.read()

                with open(output_file, "r", encoding="utf-8") as f:
                    output = f.read()
                try:
                    model_tester_output = check_output(tester_file, cwd=test_case_dir, stderr=PIPE, timeout=5).decode("utf-8")
                    tester_output = check_output(tester_file, cwd=output_dir, stderr=PIPE, timeout=5).decode("utf-8")
                except TimeoutExpired:
                    print(f"{test_case}: Tester program execution timed out!")
                    fail = True
                else:
                    model_tester_output = "\n".join([line for line in model_tester_output.splitlines() 
                                                    if line.startswith("PRINT")])
                    tester_output = "\n".join([line for line in tester_output.splitlines()
                                                    if line.startswith("PRINT")])

                    fail = check_diff(test_case, None, model_tester_output.strip(), tester_output.strip())
        else:
            for test_file in test_files:
                model_answer_file = os.path.join(test_case_dir, test_file)
                if "error" in test_file:
                    output_file = os.path.join(script_dir, "errors", test_file)
                else:
                    output_file = os.path.join(script_dir, "output", test_file)
                if not os.path.exists(output_file):
                    open(output_file, "a").close()
                
                with open(model_answer_file, "r", encoding="utf-8") as f:
                    model_answer = f.read().lower().strip()

                with open(output_file, "r", encoding="utf-8") as f:
                    output = f.read().lower().strip()

                fail = fail or check_diff(test_case, test_file, model_answer, output)
                
    if fail:
        print(f"{test_case} failed!")
    else:
        print(f"{test_case} passed.")
        passes += 1

    tests += 1
    i += 1

print("------")
print(f"{passes}/{tests} test cases passed.")
