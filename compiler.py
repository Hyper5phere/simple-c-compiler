import os
import sys
import time
import argparse
import platform
import subprocess as sp 

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, "modules"))

from cparser import Parser
from scanner import Scanner, SymbolTableManager
from semantic_analyser import SemanticAnalyser
from code_gen import CodeGen, MemoryManager


# Maximal virtual memory for compiled program process (in bytes).
MAX_VIRTUAL_MEMORY = 50 * 1024 * 1024 # 50 MB

def limit_virtual_memory():
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, MAX_VIRTUAL_MEMORY))


def compile(args):
    print("Compiling", args.source_file)
    SymbolTableManager.init()
    MemoryManager.init()
    parser = Parser(args.source_file)
    start = time.time()
    parser.parse()
    stop = time.time() - start
    print(f"Compilation took {stop:.6f} s")
    if not SymbolTableManager.error_flag:
        print("Compilation successful!")
    else:
        print("Compilation failed due to the following errors:\n")
        print(parser.scanner.lexical_errors)
        print(parser.syntax_errors)
        print(parser.semantic_analyzer.semantic_errors)
    if args.abstract_syntax_tree:
        parser.save_parse_tree()
    if args.symbol_table:
        parser.scanner.save_symbol_table()
    if args.tokens:
        parser.scanner.save_tokens()
    if args.error_files:
        parser.save_syntax_errors()
        parser.scanner.save_lexical_errors()
        parser.semantic_analyzer.save_semantic_errors()
    parser.code_generator.save_output()
    if args.run and not SymbolTableManager.error_flag:
        print("Executing compiled program")
        plat = platform.system()
        if plat == "Windows":
            tester_file = os.path.join(script_dir, "interpreter", "tester_Windows.exe")
        elif plat == "Linux":
            tester_file = os.path.join(script_dir, "interpreter", "tester_Linux.out")
        elif plat == "Darwin":
            tester_file = os.path.join(script_dir, "interpreter", "tester_Mac.out")
        else:
            raise RuntimeError("Unsupported operating system for code execution!")
        output_file = os.path.join(script_dir, "output", "output.txt")
        output_dir = os.path.dirname(output_file)
        if os.path.exists(output_file):
            preexec_fn = limit_virtual_memory if plat == "Linux" else None
            stderr = sp.PIPE if not args.verbose else None
            start = time.time()
            try:
                tester_output = sp.check_output(tester_file, cwd=output_dir, 
                                                stderr=stderr, timeout=10, 
                                                preexec_fn=preexec_fn).decode("utf-8")
            except sp.TimeoutExpired:
                print("RuntimeError: Execution timed out!")
            else:
                if not args.verbose:
                    tester_output = "\n".join([line.replace("PRINT", "").strip() 
                                               for line in tester_output.splitlines()
                                               if line.startswith("PRINT")])
                stop = time.time() - start
                print(f"Execution took {stop:.6f} s")
            print("Program output:")
            print(tester_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple C Compiler written in Python')
    parser.add_argument("source_file", help="Path to C source file.")
    parser.add_argument('-r', '--run', action='store_true', help='Run the output program after compilation.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print all used three address codes.')
    parser.add_argument('-ef', '--error-files', action='store_true', help='Save compilation errors to text files.')
    parser.add_argument('-ast', '--abstract-syntax-tree', action='store_true', help='Save abstract syntax tree into a text file.')
    parser.add_argument('-st', '--symbol-table', action='store_true', help='Save symbol table into a text file.')
    parser.add_argument('-t', '--tokens', action='store_true', help='Save lexed tokens into a text file.')
    args = parser.parse_args()
    if not os.path.isabs(args.source_file):
        args.source_file = os.path.abspath(script_dir)
    args = parser.parse_args()
    compile(args)
