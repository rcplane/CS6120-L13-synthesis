@rcplane and @zachary-kent worked together

# Summary

[Link to repo](https://github.com/rcplane/CS6120-L13-synthesis).

We extended the grammar of the language presented in class to include mutable
assignments, (roughly) based off @bcarlet's task implementation with some
modifications, and then `for` loops with a fixed lower and upper bound.

# Implementation

- We first extended the grammar with mutable assignments of the form `x := e`
  where `x` is an identifier and `e` is an expression. The start non-terminal of
  the grammar was then 0 or more statements in sequence followed by an
  expression. Semantically, each of these assignments are evaluated one by one
  and then the final expression is evaluated in the environment extended by the
  bindings introduced by mutable assignments. For example, the following code
  snippet would evaluate to 2:

  ```
  x := 0
  x := x + 1;
  x + 1
  ```

  This syntax was adapted from @bcarlet's implementation, alongside the
  structure of the modified interpreter, which is parameterized over functions
  `assign` and `lookup` are used to introduce and access mutable bindings.

- However, we implemented the `assign` and `lookup` operations themselves
  differently, drawing from _symbolic execution_. In symbolic execution, we
  maintain an environment from identifiers to symbolic values, which are
  expressed entirely in terms of the inputs to the program; in this case,
  universally quantified variables. By the time all mutable assignments in the
  program are evaluated, every variable, including those introduced/modified by
  mutable assignment, can be expressed in terms of the universally quantified
  variables. Finally, for a program `x1 := e1; ...; xn := en; e`, after
  evaluating all mutable assignments, we can then use the map from variables to
  symbolic values to express `e` purely in terms of program inputs.
- We then extended the grammar with bounded `for` loops so that there were two
  variants of top level statements:

  ```
  start ::= stmt* exprs
  stmt ::= for i = start to end do stmt* done; | x := expr
  ```

  Because the lower and upper bounds of loops are known statically, we simply
  unroll them when interpreting them. That is, we can unroll every arbitrarily
  nested loop into a finite sequence of assignments. This did not require too
  many modifications to the interpreter beyond those introduced for assignments.
- Holes can still only be placed within expressions; that is, a hole cannot
  stand in for an entire statement.

# Tests and Results

- We initially tested sketch completion starting with regression testing for
  addition expression solving and simple assignment then moved up to small loops
  and nested loops, varying the location of the hole.
- A
  [simple bash script](https://github.com/rcplane/CS6120-L13-Synthesis/solve_examples.sh)
  was written to repeat tests and confirm pretty output behavior. Sample ouptut
  is included below:

```
examples/assign.txt
x := 1;
x := x + 1;
x
----
??
Synthesized:
2
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/assign_sketch.txt
x := 0;
x := x + 10;
x
----
x + ??
Synthesized:
0 + 10
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/basic.txt
x * 9
----
x << ?? + ??
Synthesized:
(x << 3) + x
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/body_hole.txt
for i = 1 to 2 do
  for j = 1 to 2 do
    x := x * 2;
  done; 
done;
x
----
for i = 1 to 2 do
  for j = 1 to 2 do
    x := x + ??;
  done; 
done;
x
Synthesized:
for i = 1 to 2 do
for j = 1 to 2 do
x := x + x;
done;
done;
x
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/loop_sketch.txt
a := 0;
for i = 1 to 2 do a := a + 1; done;
a
----
a := 0;
a := a + ??;
a
Synthesized:
a := 0;
a := a + 2;
a
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/loop_sum.txt
for i = 1 to 2 do
  a := a + 1; 
done;
a
----
a + ??
Synthesized:
a + 2
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
examples/loops.txt
for i = 1 to 2 do
  for j = 1 to 3 do
    a := a * 2; 
  done; 
done;
a
----
a * ??
Synthesized:
a * 64
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

# Difficulties

- Ideally, we would be able to represent entire statements using holes that
  could be filled in. However, it was not clear how to do this. We considered
  using an axiomatized program logic, like one based of KAT, but this seemed
  much too difficult for this task.
- We struggled with how best to represent the synthesized program, striking a
  balance between readibility and degree of simplification. For example, you can
  display the entire unrolled program, but this would be very difficult to read.
  In the end, we decided to maintain the structure of loops when displaying the
  synthesized program to the user.
- Large loop counts and broad holes in loop bodies led to invalid model errors
  in z3 expression construction. Specifically, we very quickly overflowed the
  bit vector when doing computations with nested loops.

# Generative AI

- Both of us used GitHub Copilot throughout the task, which was mildly helpful,
  especially for generating documentation. However, completions for printing
  functions and interpreter logic was lacking, often taking on javascript syntax
  instead of python perhaps getting confused by the context conditioning of semi
  colons in the lark grammar early in the solve.py file. It was mainly useful
  for generating debugging statements, such as the following for printing the
  sketch program:
  ```
  print(f"Sketch: {pretty(tree1)}")
  ```

- Chat GPT4 April 2023 was used in early brainstorming to transcribe Stein's
  algorithm for binary GCD calcuation as an expression loop body to compare
  operation count Z3 optimization against a Euclid loop body, but using opt was
  a different track of project than augmenting Z3 solve lark interpretation.

```
```
