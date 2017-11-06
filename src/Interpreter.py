import re

from src.Lexer import *
from src.RafMath import RafMath

# Dictionary of variables
variables = {}

# Dictionary of functions and number of params
functions = {
    "sin": 1,
    "cos": 1,
    "tg": 1,
    "ctg": 1,
    "log": 1,
    "sqrt": 1,
    "pow": 2
}


def func_caller(func, *args, **kwargs):
    return func(*args, **kwargs)


class Interpreter(object):
    def __init__(self, lexer):
        self.lexer = lexer
        # set current token to the first token taken from the input
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def name(self):
        """
        name:
            [a-zA-z][a-zA-z0-9]*
        """
        token = self.current_token

        if token.type == STRING:
            regex = re.compile("[a-zA-z][a-zA-z0-9]*")
            match = regex.match(token.value)
            if match is not None:
                self.eat(STRING)
                return match.group()
            else:
                raise Exception("Invalid name")

    def func(self, name):
        """
        func:
            name \((expr?\,?)*\)
        """
        self.eat(OPEN_PARENTHESES)

        if name in functions:

            # Get function parameters
            i = 0
            params = []
            while self.current_token.type != CLOSE_PARENTHESES:
                result = self.expr()
                if result is not None:
                    params.append(result)
                if self.current_token.type == COMMA:
                    self.eat(COMMA)
                i += 1

            if len(params) != functions[name]:
                raise TypeError("Function: " + name + " requires " + str(functions[name]) + "argument/s , but has "
                                                                                            "been given " + str(len(
                    params)) + " argument/s")

            args = []
            tmp = getattr(RafMath, name, *args)

            if self.current_token.type == CLOSE_PARENTHESES:
                self.eat(CLOSE_PARENTHESES)
            else:
                raise Exception("Invalid call of function: " + name + " missing ) sign")

            return func_caller(tmp, args, *params)

        else:
            # Function hasn't been declared, raising exception
            raise Exception("Call of the undefined function: " + name)

    def variable(self, name):
        """
         variable:
            name (= expr)?
        """
        if self.current_token.type == ASSIGN:
            self.eat(ASSIGN)
            variables[name] = self.expr()

        else:
            if name in variables:
                return variables[name]
            else:
                raise Exception("Variable " + name + " not declared")

        return None

    def alpha(self):
        """
        alpha:
            func | variable
        """
        name = self.name()

        token = self.current_token
        if token.type == OPEN_PARENTHESES:
            return self.func(name)
        else:
            return self.variable(name)

    def factor(self):
        """
        INTEGER | \(
        """
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)

        if token.type == OPEN_PARENTHESES:
            return self.inside_parentheses()

        return token.value

    def unary(self):
        """
        unary:
            (- | +)factor) | factor | ((- | +)alpha) | alpha
        """
        if self.current_token.type == PLUS:
            self.eat(PLUS)

            if self.current_token.type == INTEGER:
                return self.factor()
            elif self.current_token.type == STRING:
                return self.alpha()

        if self.current_token.type == MINUS:
            self.eat(MINUS)

            if self.current_token.type == INTEGER:
                return -self.factor()
            elif self.current_token.type == STRING:
                return -self.alpha()

        if self.current_token.type == INTEGER:
            return self.factor()

        if self.current_token.type == STRING:
            return self.alpha()

        if self.current_token.type == OPEN_PARENTHESES:
            return self.factor()

    def term(self):
        """
        term:
            unary ((MUL | DIV) (factor | alpha))*
        """
        result = self.unary()

        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)

                if self.current_token.type == INTEGER:
                    result = result * self.factor()
                elif self.current_token.type == STRING:
                    result = result * self.alpha()

            elif token.type == DIV:
                self.eat(DIV)

                if self.current_token.type == INTEGER:
                    result = result / self.factor()
                elif self.current_token.type == STRING:
                    result = result / self.alpha()

        return result

    def expr(self):
        """Arithmetic expression parser / interpreter.

        expr:
            acum ((GREATER | LESS | EQUAL | GREATER_EQUAL | LESS_EQUAL) acum)*
        acum:
            term ((PLUS | MINUS) term)*
        term:
            unary ((MUL | DIV) (factor | alpha))*
        unary:
            ((- | +)factor) | factor | ((- | +)alpha) | alpha
        alpha:
            func | variable
        func:
            name \((expr?\,?)*\)
        variable:
            name (= expr)?
        name:
            [a-zA-z][a-zA-z0-9]*
        factor:
            INTEGER | BOOL | \{
        """
        result = self.acum()

        while self.current_token.type in (EQUALS, LESS, GREATER, GEQUALS, LEQUALS):
            token = self.current_token
            if token.type == EQUALS:
                self.eat(EQUALS)
                result = result == self.acum()
            elif token.type == LESS:
                self.eat(LESS)
                result = result < self.acum()
            elif token.type == GREATER:
                self.eat(GREATER)
                result = result > self.acum()
            elif token.type == LEQUALS:
                self.eat(LEQUALS)
                result = result <= self.acum()
            elif token.type == GEQUALS:
                self.eat(GEQUALS)
                result = result >= self.acum()

        return result

    def acum(self):
        """
        acum:
            term ((PLUS | MINUS) term)*
        """
        result = self.term()

        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()

        return result

    def inside_parentheses(self):
        self.eat(OPEN_PARENTHESES)
        result = self.expr()
        self.eat(CLOSE_PARENTHESES)

        return result


def main():
    while True:
        try:
            text = input('rafmath > ')
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        lexer = Lexer(text)
        interpreter = Interpreter(lexer)
        result = interpreter.expr()

        if result is not None:
            print(result)


if __name__ == '__main__':
    main()
