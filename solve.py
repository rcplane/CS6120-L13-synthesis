
# derived from
# https://github.com/sampsyo/minisynth

import lark
import sys
import z3

# A language based on a Lark example from:
# https://github.com/lark-parser/lark/wiki/Examples
# augmented from https://github.com/lark-parser/lark/blob/master/lark/grammars/python.lark
GRAMMAR = """
start: stmts expr         -> start

stmts: stmt*              -> stmts

stmt: CNAME ":=" expr ";" -> assign
  | "for" CNAME "=" NUMBER "to" NUMBER "do" stmts "done" ";" -> for

?expr: sum
  | sum "?" sum ":" sum -> if

?sum: term
  | sum "+" term        -> add
  | sum "-" term        -> sub

?term: item
  | term "*"  item      -> mul
  | term "/"  item      -> div
  | term ">>" item      -> shr
  | term "<<" item      -> shl

?item: NUMBER           -> num
  | "-" item            -> neg
  | CNAME               -> var
  | "(" start ")"

%import common.NUMBER
%import common.WS
%import common.CNAME
%ignore WS
""".strip()


# This function adapated from https://github.com/bcarlet/CS-6120/blob/main/task13/synth.py
def interp(tree, lookup, assign):
    """Evaluate the arithmetic expression.

    Pass a tree as a Lark `Tree` object for the parsed expression. For
    `lookup`, provide a function for mapping variable names to values.
    """
    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr'):  # Binary operators.
        lhs = interp(tree.children[0], lookup, assign)
        rhs = interp(tree.children[1], lookup, assign)
        if op == 'add':
            return lhs + rhs
        elif op == 'sub':
            return lhs - rhs
        elif op == 'mul':
            return lhs * rhs
        elif op == 'div':
            return lhs / rhs
        elif op == 'shl':
            return lhs << rhs
        elif op == 'shr':
            return lhs >> rhs
    elif op == 'neg':  # Negation.
        sub = interp(tree.children[0], lookup, assign)
        return -sub
    elif op == 'num':  # Literal number.
        return int(tree.children[0])
    elif op == 'var':  # Variable lookup.
        return lookup(tree.children[0])
    elif op == 'if':  # Conditional.
        cond = interp(tree.children[0], lookup, assign)
        true = interp(tree.children[1], lookup, assign)
        false = interp(tree.children[2], lookup, assign)
        return (cond != 0) * true + (cond == 0) * false
    elif op == 'assign':
        # x := e
        expr = interp(tree.children[1], lookup, assign)
        assign(tree.children[0], expr)
    elif op == 'stmts':
        for child in tree.children:
            interp(child, lookup, assign)
    elif op == 'for':
        var = tree.children[0]
        start = int(tree.children[1])
        end = int(tree.children[2])
        for i in range(start, end + 1):
            assign(var, i)
            interp(tree.children[3], lookup, assign)
    elif op == 'start':
        interp(tree.children[0], lookup, assign)
        return interp(tree.children[1], lookup, assign)


def pretty(tree, subst={}, paren=False, depth=0):
    """Pretty-print a tree, with optional substitutions applied.

    If `paren` is true, then loose-binding expressions are
    parenthesized. We simplify boolean expressions "on the fly."
    """

    if not hasattr(tree, "data"):
        return tree

    if paren:
        par = lambda s: '({})'.format(s)
    else:
        par = lambda s: s

    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr', 'xor'):
        lhs = pretty(tree.children[0], subst, True)
        rhs = pretty(tree.children[1], subst, True)
        c = {
            'add': '+',
            'sub': '-',
            'mul': '*',
            'div': '/',
            'shl': '<<',
            'shr': '>>',
            'xor': '^',
        }[op]
        return par('{} {} {}'.format(lhs, c, rhs))
    elif op == 'neg':
        sub = pretty(tree.children[0], subst)
        return '-{}'.format(sub, True)
    elif op == 'num':
        return tree.children[0]
    elif op == 'var':
        name = tree.children[0]
        return str(subst.get(name, name))
    elif op == 'if':
        cond = pretty(tree.children[0], subst)
        true = pretty(tree.children[1], subst)
        false = pretty(tree.children[2], subst)
        return par('{} ? {} : {}'.format(cond, true, false))
    elif op == 'assign':
        name = tree.children[0]
        expr = pretty(tree.children[1], subst)
        return '{} := {};\n'.format(subst.get(name, name), expr)
    elif op == 'stmts':
        return ''.join(pretty(child, subst) for child in tree.children)
    elif op == 'for':
        var = tree.children[0]
        start = pretty(tree.children[1], subst)
        end = pretty(tree.children[2], subst)
        stmts = pretty(tree.children[3], subst)
        return 'for {} = {} to {} do\n{}done;\n'.format(var, start, end, stmts)
    elif op == 'start':
        stmts = pretty(tree.children[0], subst)
        expr = pretty(tree.children[1], subst)
        return '{}{}'.format(stmts, expr)


def z3_expr(tree, vars=None):
    """Create a Z3 expression from a tree.

    Return the Z3 expression and a dict mapping variable names to all
    free variables occurring in the expression. All variables are
    represented as BitVecs of width 8. Optionally, `vars` can be an
    initial set of variables.
    """

    # Maps variables to symbolic values, generated by the following grammar
    symbolic_vars = dict(vars) if vars else {}
    symbolic_env = symbolic_vars.copy()

    # Lazily construct a mapping from names to variables.
    def get_var(name):
        if name in symbolic_env:
            return symbolic_env[name]
        else:
            v = z3.BitVec(name, 8)
            symbolic_vars[name] = v
            symbolic_env[name] = v
            return v

    def set_var(name, value):
        symbolic_env[name] = value

    return interp(tree, get_var, set_var), symbolic_vars

    # {}
    # tmp := a;
    # { tmp: [[a]] }
    # a := b;
    # { tmp: [[a]], a: [[b]] }
    # b := tmp;
    # { tmp: [[a]], a: [[b]], b: [[a]] }
    # a - b
    # [[b]] - [[a]]

    # {}
    # a := 1
    # { a: 1 }
    # a := 2
    # { a: 2 }
    # a

def solve(phi):
    """Solve a Z3 expression, returning the model.
    """

    s = z3.Solver()
    s.add(phi)
    s.check()
    return s.model()


def model_values(model):
    """Get the values out of a Z3 model.
    """
    return {
        d.name(): model[d]
        for d in model.decls()
    }


def synthesize(tree1, tree2):
    """Given two programs, synthesize the values for holes that make
    them equal.

    `tree1` has no holes. In `tree2`, every variable beginning with the
    letter "h" is considered a hole.
    """

    expr1, vars1 = z3_expr(tree1)
    expr2, _ = z3_expr(tree2, vars1.copy())

    # Filter out the variables starting with "h" to get the non-hole
    # variables.
    plain_vars = {k: v for k, v in vars1.items()
                  if not k.startswith('h')}
    
    #print(f"Quantified vars: {plain_vars}")

    #print(f"constraint: {expr1 == expr2}")

    goal = expr1 == expr2
    quantified_vars = list(plain_vars.values())
    if quantified_vars:
        goal = z3.ForAll(
            quantified_vars,  # For every valuation of variables...
            goal,  # ...the two expressions produce equal results.
        )

    # Solve the constraint.
    #print(f"solving goal {goal}")
    return solve(goal)


def desugar_hole(source):
    parts = source.split('??')
    out = []
    for (i, part) in enumerate(parts[:-1]):
        out.append(part)
        out.append('(hb{0} ? x : hn{0})'.format(i))
    out.append(parts[-1])
    return ''.join(out)


def simplify(tree, subst={}):
    op = tree.data

    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr', 'neg', 'if', 'start', 'stmts'):
        for i in range(len(tree.children)):
            tree.children[i] = simplify(tree.children[i], subst)

    if op == 'if':
        cond = tree.children[0]
        if cond.data == 'var':
            name = cond.children[0]
            if name in subst:
                val = subst[name]
                if val.as_signed_long():
                    return tree.children[1]
                else:
                    return tree.children[2]
    elif op == 'assign':
        tree.children[1] = simplify(tree.children[1], subst)
    elif op == 'for':
        tree.children[3] = simplify(tree.children[3], subst)

    return tree


def ex3(source):
    src1, src2 = source.strip().split('----')
    # print(f"Original src2: {src2}")
    src2 = desugar_hole(src2)  # Allow ?? in the sketch part.
    # print(f"Desugared src2: {src2}")

    parser = lark.Lark(GRAMMAR)
    tree1 = parser.parse(src1)
    # print(f"Sketch: {pretty(tree1)}")
    tree2 = parser.parse(src2)
    # print(f"With holes: {pretty(tree2)}")

    model = synthesize(tree1, tree2)

    #print(f"Solution: {model}")

    values = model_values(model)
    simplified = simplify(tree2, values)  # Remove foregone conclusions.
    print(f"\nSynthesized:\n{pretty(simplified, values)}")


if __name__ == '__main__':
    ex3(sys.stdin.read())

