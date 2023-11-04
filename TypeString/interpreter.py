import re
from collections import defaultdict
import sys

def instantly_call(func):
    func()
    return func

code:str = None
@instantly_call
def get_code():
    global code
    code_file_path:str = None
    if len(sys.argv) > 1:
        code_file_path = sys.argv[1]
    else:
        code_file_path = input("code file path (type here or use it as a argument)\n:")
    
    with open(code_file_path,"r",encoding="utf-8") as f:
        code = f.read()
    
del get_code

tokens:list[str] = None
@instantly_call
def tokenlize():
    global tokens
    extracted_code:str = code + " " #使得末尾总有至少一个空格 => 分割以后总有一个空串 => 约等于EOF token
    for keyword in [
        (r'\n',' \n '),
        (r'\$',' $ '),
        (r'=',' = '),
        (r':',' : ')
    ]:
        extracted_code = re.sub(
            keyword[0],
            keyword[1],
            extracted_code
        )

    code_pieces = re.split(
        r"[ \f\r\t\v]+",
        extracted_code
    )

    code_pieces = ['\n'] + list(filter(lambda x:x!='',code_pieces)) + ['\n','']

    tokens = code_pieces
del tokenlize

user_input:str = None
@instantly_call
def get_user_input():
    global user_input
    user_input = input("input = ")
del get_user_input

@instantly_call
def run():
    def raiseIfIsKeyword(token_stream):
        if token_stream.top() in ['$',':','=','\n']:
            raise ValueError("Need string, not keyword.")
    class Stream():
        def __init__(self,list_):
            self.list_:list = list_
            self.pointer:int = 0
        def top(self):
            return self.list_[self.pointer]
        def skip(self):
            self.pointer += 1
        def goto(self,pointer):
            self.pointer = pointer
        
        def __repr__(self) -> str:
            return "Stream"+str(self.list_[self.pointer::])

    variable_pointing_dict:defaultdict = defaultdict(lambda : "undefined") #字符串有默认值
    literal_bind_dict:dict[str,str] = {"input":user_input} #绑定没有默认值 (有就糟了) 不过输入有(不知道为什么的给我看语法介绍去)
    label_tokenPtr_dict:dict[str,int] = {}

    token_stream = Stream(tokens)

    def calc_get_expr(token_stream = token_stream) -> str:
        dollar_times:int = 0
        while token_stream.top() == "$":
            dollar_times += 1
            token_stream.skip()
        #美元$统计完毕，字面量暴露
        
        else:
            raiseIfIsKeyword(token_stream)
            pre_string = ''
            current_string = token_stream.top()
            while current_string in literal_bind_dict.keys():
                current_string = literal_bind_dict[current_string]
            token_stream.skip()
            while dollar_times > 0:
                #进行多次求值
                pre_string = current_string
                current_string = variable_pointing_dict[current_string]
                while current_string in literal_bind_dict.keys():
                    current_string = literal_bind_dict[current_string]
                dollar_times -= 1
            return pre_string + '\n' + current_string #pre_string用于=运算获取导向

    def relabels():
        #每个\n token后面都是一个语句，有可能是label
        token_stream_for_relabels = Stream(token_stream.list_)
        while True:
            current_token = token_stream_for_relabels.top()
            if current_token == '':
                break
            elif current_token == '\n':
                '''正式逻辑'''
                token_stream_for_relabels.skip()
                current_token = token_stream_for_relabels.top()
                if current_token in [':','','=','\n']:
                    continue

                label_value = (calc_get_expr(token_stream_for_relabels).split('\n'))[1]
                if token_stream_for_relabels.top() == '\n':
                    label_tokenPtr_dict[label_value] = token_stream_for_relabels.pointer
                
            else:
                token_stream_for_relabels.skip()
        pass
    while True: #开始读取 (T~的结构过于简单，没有代码块，所以不需要递归)
        current_token:str = token_stream.top()
        if current_token == ':':
            # 跳转
            token_stream.skip()
            first_value = (calc_get_expr().split('\n'))[1]
            second_value = (calc_get_expr().split('\n'))[1]
            label_value = (calc_get_expr().split('\n'))[1]

            if first_value == second_value:
                relabels()
                token_stream.goto(label_tokenPtr_dict[label_value])
            else:
                token_stream.skip()
            pass
        elif current_token == '':
            #EOF
            break
        elif current_token == '\n':
            token_stream.skip()
        else:
            # 表达式 -> \n //标签
            #        -> = -> 表达式若干 -> 表达式若干 -> \n //赋值
            left_value:str = calc_get_expr()
            # print(left_value)
            operation_token:str = token_stream.top()
            if operation_token == '\n':
                left_value = (left_value.split('\n'))[1]
                #标签
                token_stream.skip()
                label_tokenPtr_dict[left_value] = token_stream.pointer
            elif operation_token == '=':
                #赋值
                token_stream.skip()
                current_token = token_stream.top()
                right_value = ""
                if current_token in ['\n',':','=']:
                    raise ValueError("Keyword after '=' is not allowed")
                while True:
                    current_token = token_stream.top()
                    if current_token == '\n':
                        break
                    elif current_token in [':','=']:
                        raise ValueError("")
                    else:
                        right_value += (calc_get_expr().split('\n'))[1]
                
                #结束拼接和右获取，开始绑定
                if left_value[0] == '\n': #是字面量绑定 (原因去看get)
                    left_value = left_value[1::]
                    if left_value == right_value:
                        raise ValueError("Self binding is not allowed!")
                    literal_bind_dict[left_value] = right_value
                else:
                    pre_string,real_left = left_value.split('\n')
                    variable_pointing_dict[pre_string] = right_value
            pass
    
    if "output" in literal_bind_dict.keys():
        print("output = "+literal_bind_dict["output"])
    else:
        print("program halted with no output")
    
    input("Press [enter] to quit...")

del run
