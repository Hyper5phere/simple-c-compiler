'''
CS-E4002 - Special Course in Computer Science: Compilers
========================================================

Programming Exercise 3 - Parser

Author:             Pasi Pyrrö
Student Number:     426985
Date:               20 March 2020
Python version:     3.6
'''

import os
from anytree import Node, RenderTree, PreOrderIter
from scanner import Scanner, SymbolTableManager
from semantic_analyser import SemanticAnalyser
from code_gen import CodeGen, MemoryManager

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

non_terminal_to_missing_construct = {
    "Program"                       : "int ID;",
    "Declaration-list"              : "int ID;",
    "Declaration"                   : "int ID;",
    "Declaration-initial"           : "int ID",
    "Declaration-prime"             : ";",
    "Var-declaration-prime"         : ";",
    "Fun-declaration-prime"         : "(void) {int ID;}",
    "Type-specifier"                : "int",
    "Params"                        : "void",
    "Param-list-void-abtar"         : "ID",
    "Param-list"                    : ", int ID",
    "Param"                         : "int ID",
    "Param-prime"                   : "[]",
    "Compound-stmt"                 : "{int ID;}",
    "Statement-list"                : ";",
    "Statement"                     : ";",
    "Expression-stmt"               : ";",
    "Selection-stmt"                : "if (NUM); else;",
    "Iteration-stmt"                : "while (NUM);",
    "Return-stmt"                   : "return;",
    "Return-stmt-prime"             : ";",
    "Switch-stmt"                   : "switch (NUM) {}",
    "Case-stmts"                    : "case NUM",
    "Case-stmt"                     : "case NUM",
    "Default-stmt"                  : "default: ;",
    "Expression"                    : "NUM",
    "B"                             : "NUM",
    "H"                             : "NUM",
    "Simple-expression-zegond"      : "NUM",
    "Simple-expression-prime"       : "()",
    "C"                             : "< NUM",
    "Relop"                         : "<",
    "Additive-expression"           : "NUM",
    "Additive-expression-prime"     : "()",
    "Additive-expression-zegond"    : "NUM",
    "D"                             : "+ NUM",
    "Addop"                         : "+",
    "Term"                          : "NUM",
    "Term-prime"                    : "()",
    "Term-zegond"                   : "NUM",
    "G"                             : "* NUM",
    "Factor"                        : "NUM",
    "Var-call-prime"                : "()",
    "Var-prime"                     : "[NUM]",
    "Factor-prime"                  : "()",
    "Factor-zegond"                 : "NUM",
    "Args"                          : "NUM",
    "Arg-list"                      : "NUM",
    "Arg-list-prime"                : ", NUM",
}

productions = (
    "",                                                                 
    "Declaration-list",                                                 
    "Declaration Declaration-list",                                     
    "EPSILON",                                                          
    "Declaration-initial Declaration-prime",                            
    "#SA_SAVE_MAIN #SA_SAVE_TYPE Type-specifier #SA_SAVE_MAIN #SA_ASSIGN_TYPE ID",                    
    "#SA_ASSIGN_FUN_ROLE Fun-declaration-prime",                                            
    "#SA_ASSIGN_VAR_ROLE #SA_MAIN_POP Var-declaration-prime",                                                                           
    "#SA_ASSIGN_LENGTH ;",                                                                                                            
    "[ #SA_ASSIGN_LENGTH NUM ] ;",                                                                                                    
    "( #SA_INC_SCOPE #SA_SAVE_MAIN Params #SA_ASSIGN_FUN_ATTRS ) #SA_MAIN_CHECK Compound-stmt #CG_CALC_STACKFRAME_SIZE #CG_RETURN_SEQ_CALLEE #SA_DEC_SCOPE",                            
    "int",                                                                                                          
    "void",                                                 
    "#SA_SAVE_TYPE #SA_SAVE_PARAM int #SA_ASSIGN_TYPE ID #SA_ASSIGN_PARAM_ROLE Param-prime Param-list",                        
    "void Param-list-void-abtar",                           
    "ID Param-prime Param-list",                              
    "EPSILON",                                              
    ", #SA_SAVE_PARAM Param Param-list",                                   
    "EPSILON",                                              
    "Declaration-initial #SA_ASSIGN_PARAM_ROLE Param-prime",                      
    "#SA_ASSIGN_LENGTH [ ]",                                                  
    "#SA_ASSIGN_LENGTH EPSILON",                                              
    "{ Declaration-list Statement-list }",                  
    "Statement Statement-list",                             
    "EPSILON",                                              
    "Expression-stmt",                                      
    "Compound-stmt",                                        
    "Selection-stmt",                                       
    "Iteration-stmt",                                       
    "Return-stmt",                                          
    "Switch-stmt",                                          
    "Expression #CG_CLOSE_STMT ;",                                         
    "#SA_CHECK_WHILE #CG_CONT_JP continue ;",                                           
    "#SA_CHECK_BREAK #CG_BREAK_JP_SAVE break ;",                                              
    ";",                                                    
    "if ( Expression ) #CG_SAVE Statement else #CG_ELSE Statement #CG_IF_ELSE",           
    "#SA_PUSH_WHILE while #CG_LABEL #CG_INIT_WHILE_STACKS ( Expression ) #CG_SAVE Statement #CG_WHILE #SA_POP_WHILE",                       
    "return Return-stmt-prime #CG_SET_RETVAL #CG_RETURN_SEQ_CALLEE",                             
    ";",                                                    
    "Expression ;",                                         
    "#SA_PUSH_SWITCH switch ( Expression ) { Case-stmts Default-stmt } #SA_POP_SWITCH",        
    "Case-stmt Case-stmts",                                 
    "EPSILON",                                              
    "case NUM : Statement-list",                         
    "default : Statement-list",                             
    "EPSILON",                                              
    "Simple-expression-zegond",                             
    "#SA_CHECK_DECL #SA_SAVE_FUN #SA_SAVE_TYPE_CHECK #CG_PUSH_ID ID B",                                                 
    "= Expression #SA_TYPE_CHECK #CG_ASSIGN",                                         
    "#SA_INDEX_ARRAY [ Expression ] #SA_INDEX_ARRAY_POP H",                                     
    "Simple-expression-prime",                              
    "= Expression #SA_TYPE_CHECK #CG_ASSIGN",                                         
    "G D C",                                                
    "Additive-expression-zegond C",                         
    "Additive-expression-prime C",                          
    "#CG_SAVE_OP Relop Additive-expression #SA_TYPE_CHECK #CG_RELOP",                            
    "EPSILON",                                              
    "<",                                                    
    "==",                                                   
    "Term D",                                               
    "Term-prime D",                                         
    "Term-zegond D",                                        
    "#CG_SAVE_OP Addop Term #SA_TYPE_CHECK #CG_ADDOP D",                                         
    "EPSILON",                                              
    "+",                                                    
    "-",                                                    
    "Factor G",                                             
    "Factor-prime G",                                       
    "Factor-zegond G",                                      
    "* Factor #SA_TYPE_CHECK #CG_MULT G",                                           
    "EPSILON",                                              
    "( Expression )",                                       
    "#SA_CHECK_DECL #SA_SAVE_FUN #SA_SAVE_TYPE_CHECK #CG_PUSH_ID ID Var-call-prime",                                    
    "#SA_SAVE_TYPE_CHECK #CG_PUSH_CONST NUM",                                                  
    "#SA_PUSH_ARG_STACK ( Args #SA_CHECK_ARGS ) #CG_CALL_SEQ_CALLER #SA_POP_ARG_STACK",                                             
    "Var-prime",                                            
    "#SA_INDEX_ARRAY [ Expression ] #SA_INDEX_ARRAY_POP",                                       
    "EPSILON",                                              
    "#SA_PUSH_ARG_STACK ( Args #SA_CHECK_ARGS ) #CG_CALL_SEQ_CALLER #SA_POP_ARG_STACK",                                                                        
    "EPSILON",                                              
    "( Expression )",                                       
    "#SA_SAVE_TYPE_CHECK #CG_PUSH_CONST NUM",                                                  
    "Arg-list",                                             
    "EPSILON",                                              
    "#SA_SAVE_ARG Expression Arg-list-prime",                            
    ", #SA_SAVE_ARG Expression Arg-list-prime",                          
    "EPSILON",                                              
    "SYNCH",                                                
    "EMPTY"                                                 
)

productions = tuple([p.split() for p in productions]) # split productions into arrays

terminal_to_col = {
    "ID"        : 0,
    ";"         : 1,
    "["         : 2,
    "NUM"       : 3,
    "]"         : 4,
    "("         : 5,
    ")"         : 6,
    "int"       : 7,
    "void"      : 8,
    ","         : 9,
    "{"         : 10,
    "}"         : 11,
    "continue"  : 12,
    "break"     : 13,
    "if"        : 14,
    "else"      : 15,
    "while"     : 16,
    "return"    : 17,
    "switch"    : 18,
    "case"      : 19,
    ":"         : 20,
    "default"   : 21,
    "="         : 22,
    "<"         : 23,
    "=="        : 24,
    "+"         : 25,
    "-"         : 26,
    "*"         : 27,
    "$"         : 28
}

non_terminal_to_row = {
    "Program"                       : 0,
    "Declaration-list"              : 1,
    "Declaration"                   : 2,
    "Declaration-initial"           : 3,
    "Declaration-prime"             : 4,
    "Var-declaration-prime"         : 5,
    "Fun-declaration-prime"         : 6,
    "Type-specifier"                : 7,
    "Params"                        : 8,
    "Param-list-void-abtar"         : 9,
    "Param-list"                    : 10,
    "Param"                         : 11,
    "Param-prime"                   : 12,
    "Compound-stmt"                 : 13,
    "Statement-list"                : 14,
    "Statement"                     : 15,
    "Expression-stmt"               : 16,
    "Selection-stmt"                : 17,
    "Iteration-stmt"                : 18,
    "Return-stmt"                   : 19,
    "Return-stmt-prime"             : 20,
    "Switch-stmt"                   : 21,
    "Case-stmts"                    : 22,
    "Case-stmt"                     : 23,
    "Default-stmt"                  : 24,
    "Expression"                    : 25,
    "B"                             : 26,
    "H"                             : 27,
    "Simple-expression-zegond"      : 28,
    "Simple-expression-prime"       : 29,
    "C"                             : 30,
    "Relop"                         : 31,
    "Additive-expression"           : 32,
    "Additive-expression-prime"     : 33,
    "Additive-expression-zegond"    : 34,
    "D"                             : 35,
    "Addop"                         : 36,
    "Term"                          : 37,
    "Term-prime"                    : 38,
    "Term-zegond"                   : 39,
    "G"                             : 40,
    "Factor"                        : 41,
    "Var-call-prime"                : 42,
    "Var-prime"                     : 43,
    "Factor-prime"                  : 44,
    "Factor-zegond"                 : 45,
    "Args"                          : 46,
    "Arg-list"                      : 47,
    "Arg-list-prime"                : 48,
}

parsing_table = (
    # 0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20   21   22   23   24   25   26   27   28
    #ID    ;    [  NUM    ]    (    )  int void    ,    {    } cont break  if else whil retu swit case    : defa    =    <   ==    +    -    *    $
    (88,  88,  88,  88,  88,  88,  88,   1,   1,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 1  Program
    ( 3,   3,  88,   3,  88,   3,  88,   2,   2,  88,   3,   3,   3,   3,   3,  88,   3,   3,   3,  88,  88,  88,  88,  88,  88,  88,  88,  88,   3), # 2  Declaration-list
    (87,  87,  88,  87,  88,  87,  88,   4,   4,  88,  87,  88,  87,  87,  87,  88,  87,  87,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 3  Declaration
    (88,  87,  87,  88,  88,  87,  87,   5,   5,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 4  Declaration-initial
    (87,   7,   7,  87,  88,   6,  88,  87,  87,  88,  87,  88,  87,  87,  87,  88,  87,  87,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 5  Declaration-prime
    (87,   8,   9,  87,  88,  87,  88,  87,  87,  88,  87,  88,  87,  87,  87,  88,  87,  87,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 6  Var-declaration-prime
    (87,  87,  88,  87,  88,  10,  88,  87,  87,  88,  87,  88,  87,  87,  87,  88,  87,  87,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 7  Fun-declaration-prime
    (87,  88,  88,  88,  88,  88,  88,  11,  12,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 8  Type-specifier
    (88,  88,  88,  88,  88,  88,  87,  13,  14,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 9  Params
    (15,  88,  88,  88,  88,  88,  16,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 10 Param-list-void-abtar
    (88,  88,  88,  88,  88,  88,  18,  88,  88,  17,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 11 Param-list
    (88,  88,  88,  88,  88,  88,  87,  19,  19,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 12 Param
    (88,  88,  20,  88,  88,  88,  21,  88,  88,  21,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 13 Param-prime
    (87,  87,  88,  87,  88,  87,  88,  87,  87,  88,  22,  87,  87,  87,  87,  87,  87,  87,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 14 Compound-stmt
    (23,  23,  88,  23,  88,  23,  88,  88,  88,  88,  23,  24,  23,  23,  23,  88,  23,  23,  23,  24,  88,  24,  88,  88,  88,  88,  88,  88,  87), # 15 Statement-list
    (25,  25,  88,  25,  88,  25,  88,  88,  88,  88,  26,  87,  25,  25,  27,  87,  28,  29,  30,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 16 Statement
    (31,  34,  88,  31,  88,  31,  88,  88,  88,  88,  87,  87,  32,  33,  87,  87,  87,  87,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 17 Expression-stmt
    (87,  87,  88,  87,  88,  87,  88,  88,  88,  88,  87,  87,  87,  87,  35,  87,  87,  87,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 18 Selection-stmt
    (87,  87,  88,  87,  88,  87,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87,  36,  87,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 19 Iteration-stmt
    (87,  87,  88,  87,  88,  87,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87,  87,  37,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 20 Return-stmt
    (39,  38,  88,  39,  88,  39,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87,  87,  87,  87,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 21 Return-stmt-prime
    (87,  87,  88,  87,  88,  87,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87,  87,  87,  40,  87,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 22 Switch-stmt
    (42,  88,  88,  42,  88,  42,  88,  88,  88,  88,  88,  42,  88,  88,  88,  88,  88,  88,  88,  41,  88,  42,  88,  88,  88,  88,  88,  88,  87), # 23 Case-stmts
    (87,  88,  88,  87,  88,  87,  88,  88,  88,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  43,  88,  87,  88,  88,  88,  88,  88,  88,  87), # 24 Case-stmt
    (88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  45,  88,  88,  88,  88,  88,  88,  88,  88,  88,  44,  88,  88,  88,  88,  88,  88,  87), # 25 Default-stmt
    (47,  87,  88,  46,  87,  46,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 26 Expression
    (88,  50,  49,  88,  50,  50,  50,  88,  88,  50,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  48,  50,  50,  50,  50,  50,  50), # 27 B
    (88,  52,  88,  88,  52,  88,  52,  88,  88,  52,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  51,  52,  52,  52,  52,  52,  52), # 28 H
    (88,  87,  88,  53,  87,  53,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 29 Simple-expression-zegond
    (88,  54,  88,  88,  54,  54,  54,  88,  88,  54,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  54,  54,  54,  54,  54,  54), # 30 Simple-expression-prime
    (88,  56,  88,  88,  56,  88,  56,  88,  88,  56,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  55,  55,  88,  88,  88,  87), # 31 C
    (87,  88,  88,  87,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  57,  58,  88,  88,  88,  87), # 32 Relop
    (59,  87,  88,  59,  87,  59,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 33 Additive-expression
    (88,  60,  88,  88,  60,  60,  60,  88,  88,  60,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  60,  60,  60,  60,  60,  60), # 34 Additive-expression-prime
    (88,  87,  88,  61,  87,  61,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87,  87,  88,  88,  88,  87), # 35 Additive-expression-zegond
    (88,  63,  88,  88,  63,  88,  63,  88,  88,  63,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  63,  63,  62,  62,  88,  87), # 36 D
    (87,  88,  88,  87,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  64,  65,  88,  87), # 37 Addop
    (66,  87,  88,  66,  87,  66,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87,  87,  87,  87,  88,  87), # 38 Term
    (88,  67,  88,  88,  67,  67,  67,  88,  88,  67,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  67,  67,  67,  67,  67,  67), # 39 Term-prime
    (88,  87,  88,  68,  87,  68,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87,  87,  87,  87,  88,  87), # 40 Term-zegond
    (88,  70,  88,  88,  70,  88,  70,  88,  88,  70,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  70,  70,  70,  70,  69,  87), # 41 G
    (72,  87,  88,  73,  87,  71,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87), # 42 Factor
    (88,  75,  75,  88,  75,  74,  75,  88,  88,  75,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  75,  75,  75,  75,  75,  87), # 43 Var-call-prime
    (88,  77,  76,  88,  77,  88,  77,  88,  88,  77,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  77,  77,  77,  77,  77,  87), # 44 Var-prime
    (88,  79,  88,  88,  79,  78,  79,  88,  88,  79,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  79,  79,  79,  79,  79,  87), # 45 Factor-prime
    (88,  87,  88,  81,  87,  80,  87,  88,  88,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87,  87,  87,  87,  87,  87), # 46 Factor-zegond
    (82,  88,  88,  82,  88,  82,  83,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 47 Args
    (84,  88,  88,  84,  88,  84,  87,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87), # 48 Arg-list
    (88,  88,  88,  88,  88,  88,  86,  88,  88,  85,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  88,  87)  # 49 Arg-list-prime
)


class Parser(object):
    def __init__(self, input_file):
        if not os.path.isabs(input_file):
            input_file = os.path.join(script_dir, input_file)
        self.scanner = Scanner(input_file)
        self.semantic_analyzer = SemanticAnalyser()
        self.code_generator = CodeGen()
        self._syntax_errors = []
        self.root = Node("Program") # Start symbol
        self.parse_tree = self.root
        self.stack = [Node("$"), self.root]
        
        self.parse_tree_file = os.path.join(script_dir, "output", "parse_tree.txt")
        self.syntax_error_file = os.path.join(script_dir, "errors", "syntax_errors.txt")


    @property    
    def syntax_errors(self):
        syntax_errors = []
        if self._syntax_errors:
            for lineno, error in self._syntax_errors:
                syntax_errors.append(f"#{lineno} : Syntax Error, {error}\n")
        else:
            syntax_errors.append("There is no syntax error.")
        return "".join(syntax_errors)


    def save_parse_tree(self):
        with open(self.parse_tree_file, "w", encoding="utf-8") as f:
            for pre, _, node in RenderTree(self.parse_tree):
                if hasattr(node, "token"):
                    f.write(f"{pre}{node.token}\n")
                else:
                    f.write(f"{pre}{node.name}\n")


    def save_syntax_errors(self):
        with open(self.syntax_error_file, "w") as f:
            f.write(self.syntax_errors)

    
    def _remove_node(self, node):
        try:
            # remove node from the parse tree
            parent = list(node.iter_path_reverse())[1]
            parent.children = [c for c in parent.children if c != node]
        except IndexError:
            pass


    def _clean_up_tree(self):
        ''' remove non terminals and unmet terminals from leaf nodes '''
        remove_nodes = []
        for node in PreOrderIter(self.parse_tree):
            if not node.children and not hasattr(node, "token") and node.name != "EPSILON":
                remove_nodes.append(node)
        
        for node in remove_nodes:
            self._remove_node(node)
    

    def parse(self):
        clean_up_needed = False
        token = self.scanner.get_next_token()
        new_nodes = []
        self.code_generator.code_gen("INIT_PROGRAM", None)
        while True:
            token_type, a = token
            if token_type in ("ID", "NUM"):   # parser won't understand the lexim input in this case
                a = token_type

            current_node = self.stack[-1]     # check the top of the stack
            X = current_node.name

            if X.startswith("#SA"):             # X is an action symbol for semantic analyzer
                if X == "#SA_DEC_SCOPE" and a == "ID":
                    curr_lexim = self.scanner.id_to_lexim(token[1])
                self.semantic_analyzer.semantic_check(X, token, self.scanner.line_number)
                self.stack.pop()
                if X == "#SA_DEC_SCOPE" and a == "ID":
                    token = (token[0], self.scanner.update_symbol_table(curr_lexim))
            elif X.startswith("#CG"):           # X is an action symbol for code generator
                self.code_generator.code_gen(X, token)
                self.stack.pop()
            elif X in terminal_to_col.keys():   # X is a terminal
                if X == a:
                    if X == "$":
                        break
                    self.stack[-1].token = self.scanner.token_to_str(token)
                    self.stack.pop()
                    token = self.scanner.get_next_token()
                else:
                    SymbolTableManager.error_flag = True
                    if X == "$": # parse stack unexpectedly exhausted
                        # self._clean_up_tree()
                        break
                    self._syntax_errors.append((self.scanner.line_number, f'Missing "{X}"'))
                    self.stack.pop()
                    clean_up_needed = True
            else:                               # X is non-terminal
                # look up parsing table which production to use
                col = terminal_to_col[a]
                row = non_terminal_to_row[X]
                prod_idx = parsing_table[row][col]
                rhs = productions[prod_idx]

                if "SYNCH" in rhs:
                    SymbolTableManager.error_flag = True
                    if a == "$":
                        self._syntax_errors.append((self.scanner.line_number, "Unexpected EndOfFile"))
                        # self._clean_up_tree()
                        clean_up_needed = True
                        break
                    missing_construct = non_terminal_to_missing_construct[X]
                    self._syntax_errors.append((self.scanner.line_number, f'Missing "{missing_construct}"'))
                    self._remove_node(current_node)
                    self.stack.pop()
                elif "EMPTY" in rhs:
                    SymbolTableManager.error_flag = True
                    self._syntax_errors.append((self.scanner.line_number, f'Illegal "{a}"'))
                    token = self.scanner.get_next_token()
                else:
                    self.stack.pop()
                    for symbol in rhs:
                        if not symbol.startswith("#"):
                            new_nodes.append(Node(symbol, parent=current_node))
                        else:
                            new_nodes.append(Node(symbol))

                    for node in reversed(new_nodes):
                        if node.name != "EPSILON":
                            self.stack.append(node)

                # print(f"{X} -> {' '.join(rhs)}")  # prints out the productions used
                new_nodes = []

        self.semantic_analyzer.eof_check(self.scanner.line_number)
        if clean_up_needed:
            self._clean_up_tree()
        self.code_generator.code_gen("FINISH_PROGRAM", None)


def main(input_path):
    import time
    SymbolTableManager.init()
    MemoryManager.init()
    parser = Parser(input_path)
    start = time.time()
    parser.parse()
    stop = time.time() - start
    print(f"Parsing took {stop:.6f} s")
    parser.save_parse_tree()
    parser.save_syntax_errors()
    parser.scanner.save_lexical_errors()
    parser.scanner.save_symbol_table()
    parser.scanner.save_tokens()
    parser.semantic_analyzer.save_semantic_errors()
    parser.code_generator.save_output()


if __name__ == "__main__":
    input_path = os.path.join(script_dir, "input.txt")
    main(input_path)