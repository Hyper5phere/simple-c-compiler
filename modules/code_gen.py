'''
CS-E4002 - Special Course in Computer Science: Compilers
========================================================

Programming Exercise 5 - Intermediate Code Generator

Author:             Pasi Pyrrö
Student Number:     426985
Date:               1 April 2020
Python version:     3.6
'''

import os
from scanner import SymbolTableManager

script_dir = os.path.dirname(os.path.abspath(__file__))

class MemoryManager(object):
    ''' Manages shared information about memory locations '''

    @classmethod
    def init(cls):
        cls.static_base_ptr = 1000  # 1024
        cls.temp_base_ptr   = 5000  # 8196
        cls.stack_base_ptr  = 10008 # 16392

        cls.static_offset   = 0
        cls.temp_offset     = 0

        cls.args_field_offset   = 4
        cls.locals_field_offset = 0
        cls.arrays_field_offset = 0
        cls.temps_field_offset  = 0

        cls.pb_index = 0            # program block index

    @classmethod
    def reset(cls):
        ''' call this when finished creating stack frame '''
        cls.args_field_offset  = 4
        cls.locals_field_offset = 0
        cls.array_field_offset = 0
        cls.temp_field_offset  = 0

    @classmethod
    def get_temp(cls):
        temp = cls.temp_base_ptr + cls.temp_offset
        cls.temp_offset += 4
        SymbolTableManager.temp_stack[-1] += 4
        return temp 

    @classmethod
    def get_static(cls, arity=1):
        temp = cls.static_base_ptr + cls.static_offset
        cls.static_offset += 4 * arity
        return temp

    @classmethod
    def get_param_offset(cls, arity=1):
        offset = cls.args_field_offset
        cls.args_field_offset += 4
        return offset


class CodeGen(object):
    def __init__(self):
        self.semantic_stack = []
        self.call_seq_stack = []
        self.cont_label_stack = []
        self.break_loc_stack = []

        self.semantic_routines = {
            "INIT_PROGRAM" : self.init_program_routine,
            "FINISH_PROGRAM" : self.finish_program_routine,

            "#CG_CALC_STACKFRAME_SIZE" : self.calc_stackframe_size_routine,

            "#CG_CALL_SEQ_CALLER" : self.call_seq_caller_routine,
            "#CG_CALL_SEQ_CALLEE" : self.call_seq_callee_routine,
            
            "#CG_SET_RETVAL" : self.set_retval_routine,
            "#CG_RETURN_SEQ_CALLEE" : self.return_seq_callee_routine,

            "#CG_PUSH_ID" : self.push_id_routine,
            "#CG_PUSH_CONST" : self.push_const_routine,

            "#CG_CLOSE_STMT": self.close_stmt_routine,

            "#CG_ASSIGN" : self.assign_routine,
            "#CG_MULT" : self.mult_routine,
            "#CG_SAVE_OP" : self.save_op_routine,
            "#CG_RELOP" : self.relop_routine,
            "#CG_ADDOP" : self.addop_routine,

            "#CG_LABEL" : self.label_routine,
            "#CG_SAVE" : self.save_routine,
            "#CG_WHILE" : self.while_routine,

            "#CG_IF_ELSE" : self.if_else_routine,
            "#CG_ELSE" : self.else_routine,

            "#CG_INIT_WHILE_STACKS" : self.init_while_stacks_routine,
            "#CG_CONT_JP" : self.cont_jp_routine,
            "#CG_BREAK_JP_SAVE" : self.break_jp_save_routine,

        }

        self.token_to_op = {
            "+"  : "ADD",
            "-"  : "SUB",
            "==" : "EQ",
            "<"  : "LT"
        }

        self.program_block = []

        self.output_file = os.path.join(os.path.dirname(script_dir), "output", "output.txt")

    
    @property
    def stack_frame_ptr_addr(self):
        ''' memory location for runtime stack frame pointer variable '''
        return MemoryManager.static_base_ptr


    @property
    def print_addr(self):
        return MemoryManager.static_base_ptr + 4


    @property
    def arg_counter(self):
        return [len(l) for l in SymbolTableManager.arg_list_stack]


    def _add_three_addr_code(self, three_addr_code, idx=None, insert=False, increment=True):
        if idx is None:
            idx = MemoryManager.pb_index
        if isinstance(three_addr_code, tuple):
            three_addr_code = self._get_three_addr_code(three_addr_code[0], *three_addr_code[1:])
        if insert:
            self.program_block[idx] = (idx, three_addr_code)
        else:
            self.program_block.append((idx, three_addr_code))
        if increment:
            MemoryManager.pb_index += 1


    def _add_placeholder(self):
        self._add_three_addr_code("PLACEHOLDER")

    
    def _add_print_code(self, t):
        self._add_three_addr_code(self._get_three_addr_code("print", t))

    
    def _get_three_addr_code(self, opcode, *args):
        three_addr_code = "(" + opcode.upper()
        for i in range(3):
            try:
                arg = args[i]
                three_addr_code = three_addr_code + ", " + str(arg)
            except IndexError:
                three_addr_code = three_addr_code + ", "
        return three_addr_code + ")"


    def _get_context_info(self):
        scope_stack = SymbolTableManager.scope_stack
        symbol_table = SymbolTableManager.symbol_table
        return scope_stack, symbol_table


    def _get_enclosing_fun(self, level=1):
        try:
            scope_stack = SymbolTableManager.scope_stack
            symbol_table = SymbolTableManager.symbol_table
            return symbol_table[scope_stack[-level] - 1]
        except IndexError:
            return None


    def _get_add_code(self, *args):
        return self._get_three_addr_code("ADD", *args)

    
    def _get_sub_code(self, *args):
        return self._get_three_addr_code("SUB", *args)

    
    def _get_static_addr(self, offset):
        return MemoryManager.static_base_ptr + offset

    
    def _resolve_addr(self, operand):
        if isinstance(operand, int):
            addr = operand
        elif "address" in operand:
            addr = operand["address"] # static address
        else:
            # need to calculate dynamic address
            t_arg_addr = MemoryManager.get_temp()
            self._add_three_addr_code(self._get_add_code(self.stack_frame_ptr_addr, f"#{operand['offset']}", t_arg_addr))
            addr = f"@{t_arg_addr}"
        return addr


    def save_output(self):
        with open(self.output_file, "w") as f:
            if self.program_block:
                for lineno, three_addr_code in self.program_block:
                    f.write(f"{lineno}\t{three_addr_code}\n")
            else:
                f.write("Failed to generate output program.\n")


    ''' semantic routines begin here '''


    def push_const_routine(self, input_token):
        addr = MemoryManager.get_static()
        const = "#" + input_token[1]
        self._add_three_addr_code(self._get_three_addr_code("assign", const, addr))
        self.semantic_stack.append(addr)


    def push_id_routine(self, input_token):
        id_row = SymbolTableManager.symbol_table[input_token[1]]
        self.semantic_stack.append(id_row)

    
    def init_program_routine(self, input_token):
        three_addr_code = self._get_three_addr_code("assign", f"#{MemoryManager.stack_base_ptr}", 
                                  self.stack_frame_ptr_addr)
        self._add_three_addr_code(three_addr_code)
        # allocate space for stack ptr and print address (+0 and +4)
        MemoryManager.static_offset += 8
        for _ in range(3):
            self._add_placeholder()
        

    def assign_routine(self, input_token):
        try:
            # self.expression_assigned = True
            A = self._resolve_addr(self.semantic_stack.pop())
            R = self._resolve_addr(self.semantic_stack[-1])
            self._add_three_addr_code(("assign", A, R))
        except IndexError:
            pass

    
    def save_op_routine(self, input_token):
        op = self.token_to_op[input_token[1]]
        self.semantic_stack.append(op)


    def mult_routine(self, input_token):
        self.binary_op_routine("MULT")


    def relop_routine(self, input_token):
        try:
            op = self.semantic_stack.pop(-2)
            self.binary_op_routine(op)
        except IndexError:
            pass
    
    def addop_routine(self, input_token):
        try:
            op = self.semantic_stack.pop(-2)
            self.binary_op_routine(op)
        except IndexError:
            pass

    def binary_op_routine(self, op):
        try:
            R = MemoryManager.get_temp()
            A2 = self._resolve_addr(self.semantic_stack.pop())
            A1 = self._resolve_addr(self.semantic_stack.pop())
            self._add_three_addr_code((op, A1, A2, R))
            self.semantic_stack.append(R)
        except IndexError:
            pass


    def finish_program_routine(self, input_token):
        # back patch main jump here
        t_ret_addr = MemoryManager.get_temp()
        self.program_block[1] = (1, self._get_sub_code(self.stack_frame_ptr_addr, "#4", t_ret_addr))
        self.program_block[2] = (2, self._get_three_addr_code("assign", f"#{MemoryManager.pb_index}", f"@{t_ret_addr}"))
        self.program_block[3] = (3, self._get_three_addr_code("jp", SymbolTableManager.findrow("main")["address"]))


    def call_seq_caller_routine(self, input_token, backpatch=False):
        ''' expects semantic stack to contain:
            ----------------------------------
            ss(top)         = arg_n addr
            ...
            ss(top - n + 2) = arg_2 addr
            ss(top - n + 1) = arg_1 addr
            ss(top - n)     = fun   addr
        '''
        stack = self.semantic_stack if not backpatch else self.call_seq_stack

        if backpatch:
            callee = stack.pop()
            store_idx = MemoryManager.pb_index
            t_ret_val = stack.pop()
            self.arg_counter[-1] = stack.pop()
            MemoryManager.pb_index = stack.pop()
        else:
            callee = stack[-(self.arg_counter[-1] + 1)]
        
        caller = SymbolTableManager.get_enclosing_fun()

        if callee["lexim"] == "output":
            arg = stack.pop()
            stack.pop() # pop output row off the stack
            arg_addr = self._resolve_addr(arg)
            self._add_three_addr_code(self._get_three_addr_code("assign", arg_addr, self.print_addr))
            self._add_three_addr_code(self._get_three_addr_code("PRINT", self.print_addr))
            self.arg_counter[-1] = 0
            self.semantic_stack.append("void")
            return

        if not backpatch:
            t_ret_val = MemoryManager.get_temp()
        
        if "frame_size" in caller:
            # current top_sp and access link pointer
            top_sp = self.stack_frame_ptr_addr
            frame_size = caller["frame_size"]
            t_new_top_sp = MemoryManager.get_temp()
            self._add_three_addr_code(self._get_add_code(top_sp, f"#{frame_size}", t_new_top_sp), insert=backpatch)
            # assign access link address to new stack frame
            self._add_three_addr_code(self._get_three_addr_code("assign", top_sp, f"@{t_new_top_sp}"), insert=backpatch)
            t_args = MemoryManager.get_temp()
            self._add_three_addr_code(self._get_add_code(t_new_top_sp, "#4", t_args), insert=backpatch)
            n_args = callee["arity"]
            args = stack[-n_args:]
            for i in range(n_args):
                stack.pop()
                arg = args[i]
                # arg_addr = self._resolve_addr(arg)
                if isinstance(arg, int):
                    arg_addr = arg
                elif "address" in arg:
                    arg_addr = arg["address"]  # static address
                else:
                    # need to calculate dynamic address
                    t_arg_addr = MemoryManager.get_temp()
                    self._add_three_addr_code(self._get_add_code(self.stack_frame_ptr_addr, f"#{arg['offset']}", t_arg_addr), 
                                              insert=backpatch)
                    arg_addr = f"@{t_arg_addr}"
                if callee["params"][-i-1] == "array":
                    arg_addr = f"#{arg}" # pass by reference
                self._add_three_addr_code(self._get_three_addr_code("assign", arg_addr, f"@{t_args}"), insert=backpatch)
                # self._add_three_addr_code(self._get_three_addr_code("print", f"@{t_args}"), insert=backpatch)
                self._add_three_addr_code(self._get_add_code(t_args, "#4", t_args), insert=backpatch)
            fun_addr = stack.pop()["address"] 
            # put pointers for return address and return value in temp variables 
            t_ret_addr = MemoryManager.get_temp()
            t_ret_val_callee = MemoryManager.get_temp()
            self._add_three_addr_code(self._get_sub_code(t_new_top_sp, "#4", t_ret_addr), insert=backpatch)
            self._add_three_addr_code(self._get_sub_code(t_new_top_sp, "#8", t_ret_val_callee), insert=backpatch)
            # increment stack frame pointer by frame size TODO: update stack pointer via access link and static offset
            # self._add_three_addr_code(self._get_add_code(top_sp, f"#{frame_size}", top_sp), insert=backpatch)
            self._add_three_addr_code(self._get_three_addr_code("assign", t_new_top_sp, top_sp), insert=backpatch)
            # self._add_three_addr_code(self._get_three_addr_code("print", top_sp), insert=backpatch)
            # assign value for return address in callee stack frame
            self._add_three_addr_code(self._get_three_addr_code("assign", f"#{MemoryManager.pb_index + 2}", f"@{t_ret_addr}"), 
                                      insert=backpatch)
            # jump to function address
            self._add_three_addr_code(self._get_three_addr_code("jp", fun_addr), insert=backpatch)
            # fetch the return value to a temporary and push it to the stack
            self._add_three_addr_code(self._get_three_addr_code("assign", f"@{t_ret_val_callee}", t_ret_val), insert=backpatch)
            # decrement stack frame pointer by frame size
            self._add_three_addr_code(self._get_sub_code(top_sp, f"#{frame_size}", top_sp), insert=backpatch)
            # self._add_three_addr_code(self._get_three_addr_code("print", top_sp), insert=backpatch)
        else: # in recursive calls we need to backpatch
            callee = stack[-(self.arg_counter[-1] + 1)]
            self.call_seq_stack += self.semantic_stack[-(self.arg_counter[-1] + 1):]
            num_offset_vars = 0
            for i in range(1, callee["arity"]+1):
                arg = self.semantic_stack[-i]
                if not isinstance(arg, int) and "offset" in arg:
                    num_offset_vars += 1
            self.semantic_stack = self.semantic_stack[:-(self.arg_counter[-1] + 1)]
            self.call_seq_stack.append(MemoryManager.pb_index)
            self.call_seq_stack.append(self.arg_counter[-1])
            self.call_seq_stack.append(t_ret_val)
            self.call_seq_stack.append(callee)
            
            for _ in range(10 + callee["arity"]*2 + num_offset_vars): # reserve space for call seq
                self._add_placeholder()

        if backpatch:
            MemoryManager.pb_index = store_idx
        else:
            if callee["type"] == "void":
                self.semantic_stack.append("void")
            else:
                self.semantic_stack.append(t_ret_val)

        
    def call_seq_callee_routine(self, input_token):
        pass # TODO: assign array pointers here


    def calc_stackframe_size_routine(self, input_token):
        ''' Calculates size of callee's stack frame and local variable field 
            and stores it into symbol table '''
        scope_stack, symbol_table = self._get_context_info()
        fun_row = SymbolTableManager.get_enclosing_fun()
        fun_row["args_size"] = 0
        fun_row["locals_size"] = 0
        fun_row["arrays_size"] = 0
        fun_row["temps_size"] = SymbolTableManager.temp_stack.pop()
        if not SymbolTableManager.temp_stack:
            SymbolTableManager.temp_stack = [0]
        for i in range(scope_stack[-1], len(symbol_table)):
            if symbol_table[i]["role"] == "local_var":
                if symbol_table[i]["type"] == "array":
                    fun_row["arrays_size"] += 4 * symbol_table[i]["arity"]
                fun_row["locals_size"] += 4
            else:
                fun_row["args_size"] += 4
        fun_row["frame_size"] = fun_row["args_size"] + 12
        # fun_row["frame_size"] = fun_row["args_size"] + fun_row["locals_size"] \
        #                       + fun_row["arrays_size"] + fun_row["temps_size"] + 12
        fun_row["args_offset"] = 4
        fun_row["locals_offset"] = fun_row["args_offset"] + fun_row["args_size"]
        fun_row["arrays_offset"] = fun_row["locals_offset"] + fun_row["locals_size"]
        fun_row["temps_offset"] = fun_row["arrays_offset"] + fun_row["arrays_size"]
        
        while self.call_seq_stack:
            self.call_seq_caller_routine(input_token, backpatch=True)

        MemoryManager.reset()

    
    def set_retval_routine(self, input_token):
        # if self.semantic_stack:
        
        # save return value address into temp variable
        t = MemoryManager.get_temp()
        self._add_three_addr_code(self._get_sub_code(self.stack_frame_ptr_addr, "#8", t))
        try:
            retval_addr = self._resolve_addr(self.semantic_stack.pop())
        except IndexError:
            ta_code = self._get_three_addr_code("assign", "#0", f"@{t}")
            self._add_three_addr_code(ta_code)
        else:
            ta_code = self._get_three_addr_code("assign", retval_addr, f"@{t}")
            self._add_three_addr_code(ta_code)


    def return_seq_callee_routine(self, input_token):
        t = MemoryManager.get_temp()
        # save return address into temp variable
        self._add_three_addr_code(self._get_sub_code(self.stack_frame_ptr_addr, "#4", t))
        t2 = MemoryManager.get_temp()
        self._add_three_addr_code(self._get_three_addr_code("assign", f"@{t}", t2))
        self._add_three_addr_code(self._get_three_addr_code("jp", f"@{t2}"))
    

    def close_stmt_routine(self, input_token):
        # if not self.expression_assigned and self.semantic_stack:
        if self.semantic_stack:
            self.semantic_stack.pop() # pop result of last assignment
        # self.expression_assigned = False

    
    def label_routine(self, input_token):
        self.semantic_stack.append(MemoryManager.pb_index)


    def save_routine(self, input_token):
        self.semantic_stack.append(MemoryManager.pb_index)
        self._add_placeholder()


    def while_routine(self, input_token):
        try:
            saved_idx = self.semantic_stack.pop()
            cond = self._resolve_addr(self.semantic_stack.pop())
            jp_target = self.semantic_stack.pop()
            self._add_three_addr_code(("jp", jp_target))
            self._add_three_addr_code(("jpf", cond, MemoryManager.pb_index), 
                                      idx=saved_idx, insert=True, increment=False)
        except IndexError:
            pass

        try:
            self.cont_label_stack.pop()
            break_locs = self.break_loc_stack.pop()
            for bloc in break_locs:
                self._add_three_addr_code(("jp", MemoryManager.pb_index), 
                                           idx=bloc, insert=True, increment=False)
        except IndexError:
            pass
        

    def init_while_stacks_routine(self, input_token):
        self.cont_label_stack.append(MemoryManager.pb_index)
        self.break_loc_stack.append([])


    def cont_jp_routine(self, input_token):
        self._add_three_addr_code(("jp", self.cont_label_stack[-1]))


    def break_jp_save_routine(self, input_token):
        self.break_loc_stack[-1].append(MemoryManager.pb_index)
        self._add_placeholder()


    def if_else_routine(self, input_token):
        try:
            saved_idx = self.semantic_stack.pop()
            self._add_three_addr_code(("jp", MemoryManager.pb_index), 
                                        idx=saved_idx, insert=True, increment=False)
        except IndexError:
            pass


    def else_routine(self, input_token):
        try:
            saved_idx = self.semantic_stack.pop()
            cond = self._resolve_addr(self.semantic_stack.pop())
            self.semantic_stack.append(MemoryManager.pb_index)
            self._add_placeholder()
            self._add_three_addr_code(("jpf", cond, MemoryManager.pb_index), 
                                        idx=saved_idx, insert=True, increment=False)
        except IndexError:
            pass


    ''' Semantic routines end here '''


    def code_gen(self, action_symbol, input_token):
        if not SymbolTableManager.error_flag:
            try:
                self.semantic_routines[action_symbol](input_token)
            except Exception as e:
                print(f"Error in semantic routine {action_symbol}:", str(e))