'''
Semantic Analyser module of the Simple C Compiler

Author:             Pasi Pyrrö
Date:               16 March 2020
'''

import os
from scanner import SymbolTableManager
from code_gen import MemoryManager

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SemanticAnalyser(object):
    def __init__(self):
        # routines
        self.semantic_checks = {
            "#SA_INC_SCOPE" : self.inc_scope_routine,
            "#SA_DEC_SCOPE" : self.dec_scope_routine,

            "#SA_SAVE_MAIN" : self.save_main_routine,
            "#SA_MAIN_POP" : self.pop_main_routine,
            "#SA_MAIN_CHECK" : self.check_main_routine,

            "#SA_SAVE_TYPE" : self.save_type_routine,
            "#SA_ASSIGN_TYPE" : self.assign_type_routine,
            "#SA_ASSIGN_FUN_ROLE" : self.assign_fun_role_routine,
            "#SA_ASSIGN_VAR_ROLE" : self.assign_var_role_routine,
            "#SA_ASSIGN_PARAM_ROLE" : self.assign_param_role_routine,
            "#SA_ASSIGN_LENGTH" : self.assign_length_routine,
            "#SA_SAVE_PARAM" : self.save_param_routine,
            "#SA_ASSIGN_FUN_ATTRS" : self.assign_fun_attrs_routine,

            "#SA_CHECK_DECL" : self.check_declaration_routine,

            "#SA_SAVE_FUN" : self.save_fun_routine,
            "#SA_CHECK_ARGS" : self.check_args_routine,

            "#SA_PUSH_ARG_STACK" : self.push_arg_stack_routine,
            "#SA_SAVE_ARG" : self.save_arg_routine,
            "#SA_POP_ARG_STACK" : self.pop_arg_stack_routine, 
            

            "#SA_PUSH_WHILE" : self.push_while_routine,
            "#SA_CHECK_WHILE" : self.check_while_routine,
            "#SA_POP_WHILE" : self.pop_while_routine,

            "#SA_PUSH_SWITCH" : self.push_switch_routine,
            "#SA_CHECK_BREAK" : self.check_break_routine,
            "#SA_POP_SWITCH" : self.pop_switch_routine,

            "#SA_SAVE_TYPE_CHECK" : self.save_type_check_routine,
            "#SA_INDEX_ARRAY" : self.index_array_routine,
            "#SA_INDEX_ARRAY_POP" : self.index_array_pop_routine,
            "#SA_TYPE_CHECK" : self.type_check_routine,
        }
        # accosiated stacks
        self.semantic_stacks = {
            "main_check" : [],
            "type_assign" : [],
            "type_check" : [],
            "fun_check" : [],
        }
        # flags
        self.main_found = False
        self.main_not_last = False

        # counters
        self.arity_counter = 0
        # self.arg_lists = {}
        self.while_counter = 0
        self.switch_counter = 0

        # lists
        self.fun_param_list = []
        self.fun_arg_list = []

        self._semantic_errors = []
        self.semantic_error_file = os.path.join(script_dir, "errors", "semantic_errors.txt")


    @property
    def scope(self):
        return len(SymbolTableManager.scope_stack) - 1


    @property
    def semantic_errors(self):
        semantic_errors = []
        if self._semantic_errors:
            for lineno, error in self._semantic_errors:
                semantic_errors.append(f"#{lineno} : Semantic Error! {error}\n")
        else:
            semantic_errors.append("The input program is semantically correct.\n")
        return "".join(semantic_errors)


    def _get_lexim(self, token):
        if token[0] == "ID":
            return SymbolTableManager.symbol_table[token[1]]['lexim']
        else:
            return token[1]


    def save_semantic_errors(self):
        with open(self.semantic_error_file, "w") as f:
            f.write(self.semantic_errors)


    ''' semantic routines start here '''


    def inc_scope_routine(self, input_token, line_number):
        SymbolTableManager.scope_stack.append(len(SymbolTableManager.symbol_table))


    def dec_scope_routine(self, input_token, line_number):
        scope_start_idx = SymbolTableManager.scope_stack.pop()
        SymbolTableManager.symbol_table = SymbolTableManager.symbol_table[:scope_start_idx]


    def save_main_routine(self, input_token, line_number):
        self.semantic_stacks["main_check"].append(self._get_lexim(input_token))


    def pop_main_routine(self, input_token, line_number):
        self.semantic_stacks["main_check"] = self.semantic_stacks["main_check"][:-2]

    
    def save_type_routine(self, input_token, line_number):
        SymbolTableManager.declaration_flag = True
        self.semantic_stacks["type_assign"].append(input_token[1])


    def assign_type_routine(self, input_token, line_number):
        if input_token[0] == "ID" and self.semantic_stacks["type_assign"]:
            symbol_idx = input_token[1]
            SymbolTableManager.symbol_table[symbol_idx]["type"] = self.semantic_stacks["type_assign"].pop()
            self.semantic_stacks["type_assign"].append(symbol_idx)
            SymbolTableManager.declaration_flag = False
        

    def assign_fun_role_routine(self, input_token, line_number):
        if self.semantic_stacks["type_assign"]:
            symbol_idx = self.semantic_stacks["type_assign"][-1]
            SymbolTableManager.symbol_table[symbol_idx]["role"] = "function"
            SymbolTableManager.symbol_table[symbol_idx]["address"] = MemoryManager.pb_index

    
    def assign_param_role_routine(self, input_token, line_number):
        self.assign_var_role_routine(input_token, line_number, "param")


    def assign_var_role_routine(self, input_token, line_number, role="local_var"):
        if self.semantic_stacks["type_assign"]:
            symbol_idx = self.semantic_stacks["type_assign"][-1]
            symbol_row = SymbolTableManager.symbol_table[symbol_idx]
            symbol_row["role"] = role
            if self.scope == 0:
                # symbol_row["address"] = MemoryManager.static_offset
                # MemoryManager.static_offset += 4
                symbol_row["role"] = "global_var"
            # else:
            #     symbol_row["offset"] = MemoryManager.stack_frame_offset
            #     MemoryManager.stack_frame_offset += 4
            if symbol_row["type"] == "void":
                SymbolTableManager.error_flag = True
                self._semantic_errors.append((line_number, "Illegal type of void for '{}'.".format(symbol_row["lexim"])))
                symbol_row.pop("type") # void types are not considered to be defined
            if input_token[1] == "[":
                symbol_row["type"] = "array"


    def assign_length_routine(self, input_token, line_number):
        if self.semantic_stacks["type_assign"]:
            symbol_idx = self.semantic_stacks["type_assign"].pop()
            symbol_row = SymbolTableManager.symbol_table[symbol_idx]
            if input_token[0] == "NUM":
                symbol_row["arity"] = int(input_token[1])
                if symbol_row["role"] == "param":
                    symbol_row["offset"] = MemoryManager.get_param_offset()
                else: 
                    symbol_row["address"] = MemoryManager.get_static(int(input_token[1]))
                # if self.scope == 0:
                #     MemoryManager.static_offset += 4 * (int(input_token[1]) - 1)
            else:
                SymbolTableManager.symbol_table[symbol_idx]["arity"] = 1
                if symbol_row["role"] == "param":
                    symbol_row["offset"] = MemoryManager.get_param_offset()
                else:
                    symbol_row["address"] = MemoryManager.get_static()
                
            if input_token[1] == "[" and self.fun_param_list:
                self.fun_param_list[-1] = "array"
            

    def save_param_routine(self, input_token, line_number):
        self.fun_param_list.append(input_token[1])

    
    def push_arg_stack_routine(self, input_token, line_number):
        SymbolTableManager.arg_list_stack.append([])


    def pop_arg_stack_routine(self, input_token, line_number):
        if len(SymbolTableManager.arg_list_stack) > 1:
            SymbolTableManager.arg_list_stack.pop()

    
    def save_arg_routine(self, input_token, line_number):
        if input_token[0] == "ID":
            SymbolTableManager.arg_list_stack[-1].append(SymbolTableManager.symbol_table[input_token[1]].get("type"))
        else:
            SymbolTableManager.arg_list_stack[-1].append("int")


    def assign_fun_attrs_routine(self, input_token, line_number):
        if self.semantic_stacks["type_assign"]:
            symbol_idx = self.semantic_stacks["type_assign"].pop()
            params = self.fun_param_list
            SymbolTableManager.symbol_table[symbol_idx]["arity"] = len(params)
            SymbolTableManager.symbol_table[symbol_idx]["params"] = params
            self.fun_param_list = []
            SymbolTableManager.temp_stack.append(0) # init temp counter for this function


    def check_main_routine(self, input_token, line_number):
        main_signature = ("void", "main", "void")
        try:
            top_three = tuple(self.semantic_stacks["main_check"][-3:])
            self.semantic_stacks["main_check"] = self.semantic_stacks["main_check"][:-3]

            if not self.main_found:
                self.main_found = (top_three == main_signature and self.scope == 1)
            # check whether main is the last global function definition 
            elif not self.main_not_last and self.main_found and self.scope == 1:
                self.main_not_last = True

        except IndexError:
            pass
    

    def check_declaration_routine(self, input_token, line_number):
        if "type" not in SymbolTableManager.symbol_table[input_token[1]]:
            lexim = self._get_lexim(input_token)
            SymbolTableManager.error_flag = True
            self._semantic_errors.append((line_number, f"'{lexim}' is not defined."))

    
    def save_fun_routine(self, input_token, line_number):
        if SymbolTableManager.symbol_table[input_token[1]].get("role") == "function":
            self.semantic_stacks["fun_check"].append(input_token[1])


    def check_args_routine(self, input_token, line_number):
        if self.semantic_stacks["fun_check"]:
            fun_id = self.semantic_stacks["fun_check"].pop()
            lexim = SymbolTableManager.symbol_table[fun_id]["lexim"]
            args = SymbolTableManager.arg_list_stack[-1]
            # args = self.arg_lists.get(fun_id)
            if args is not None:
                self.semantic_stacks["type_check"] = self.semantic_stacks["type_check"][:len(args)]
                if SymbolTableManager.symbol_table[fun_id]["arity"] != len(args):
                    SymbolTableManager.error_flag = True
                    self._semantic_errors.append((line_number, f"Mismatch in numbers of arguments of '{lexim}'."))
                else:
                    params = SymbolTableManager.symbol_table[fun_id]["params"]
                    i = 1
                    for param, arg in zip(params, args):
                        if param != arg and arg is not None:
                            SymbolTableManager.error_flag = True
                            self._semantic_errors.append((line_number, f"Mismatch in type of argument {i} of '{lexim}'. Expected '{param}' but got '{arg}' instead."))
                        i += 1
                # self.arg_lists[fun_id] = []
                # SymbolTableManager.arg_list_stack[-1] = []


    def push_while_routine(self, input_token, line_number):
        self.while_counter += 1


    def check_while_routine(self, input_token, line_number):
        if self.while_counter <= 0:
            SymbolTableManager.error_flag = True
            self._semantic_errors.append((line_number, f"No 'while' found for 'continue'"))


    def pop_while_routine(self, input_token, line_number):
        self.while_counter -= 1

    
    def push_switch_routine(self, input_token, line_number):
        self.switch_counter += 1


    def check_break_routine(self, input_token, line_number):
        if self.while_counter <= 0 and self.switch_counter <= 0:
            SymbolTableManager.error_flag = True
            self._semantic_errors.append((line_number, "No 'while' or 'switch' found for 'break'."))


    def pop_switch_routine(self, input_token, line_number):
        self.switch_counter -= 1


    def save_type_check_routine(self, input_token, line_number):
        if input_token[0] == "ID":
            operand_type = SymbolTableManager.symbol_table[input_token[1]].get("type")
        else:
            operand_type = "int"
        self.semantic_stacks["type_check"].append(operand_type)
    

    def index_array_routine(self, input_token, line_number):
        if self.semantic_stacks["type_check"]:
            self.semantic_stacks["type_check"][-1] = "int"


    def index_array_pop_routine(self, input_token, line_number):
        if self.semantic_stacks["type_check"]:
            self.semantic_stacks["type_check"].pop()


    def type_check_routine(self, input_token, line_number):
        try:
            operand_b_type = self.semantic_stacks["type_check"].pop()
            operand_a_type = self.semantic_stacks["type_check"].pop()
            if operand_b_type is not None and operand_a_type is not None:
                if operand_a_type == "array":
                    SymbolTableManager.error_flag = True
                    self._semantic_errors.append((line_number, 
                        f"Type mismatch in operands, Got '{operand_a_type}' instead of 'int'."))
                elif operand_a_type != operand_b_type:
                    SymbolTableManager.error_flag = True
                    self._semantic_errors.append((line_number, 
                        f"Type mismatch in operands, Got '{operand_b_type}' instead of '{operand_a_type}'."))
                else:
                    self.semantic_stacks["type_check"].append(operand_a_type)
        except IndexError:
            pass

    ''' semantic routines end here '''


    def semantic_check(self, action_symbol, input_token, line_number):
        try:
            self.semantic_checks[action_symbol](input_token, line_number)
        # except KeyError as e:
        #     raise e
        #     raise NotImplementedError(f"No semantic check for action symbol '{action_symbol}' found!")
        except Exception as e:
            print(f"{line_number} : Error in semantic routine {action_symbol}:", str(e))


    def eof_check(self, line_number):
        if not self.main_found or self.main_not_last:
            SymbolTableManager.error_flag = True
            self._semantic_errors.append((line_number, "main function not found!"))
