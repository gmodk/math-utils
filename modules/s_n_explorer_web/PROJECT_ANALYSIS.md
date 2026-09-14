# Analysis of the original `s_n explorer`

## Existing design

The command-line application has the right architectural idea: user interaction is separated from the mathematical engine.

`main.py` exposes a menu over `S_n` with the following operations:

1. compose two permutations;
2. inspect a permutation;
3. list all elements;
4. list inverses;
5. list self-inverse elements;
6. print a Cayley table;
7. construct a dihedral group;
8. enumerate subgroups and identify normal ones;
9. compute quotient groups.

`symmetric_group.py` stores permutations as zero-based lists, renders them in one-based mathematical notation, and uses the composition convention

`(sigma o tau)(i) = sigma(tau(i))`.

The module already implements the central finite-group algorithms: permutation generation, inverse, cycle decomposition, order, sign, Cayley tables, `D_n`, generated subgroups, exhaustive subgroup enumeration, normality, left cosets and quotient groups.

## Main strengths

- The algebra is already isolated from input/output code.
- The composition convention is explicit and consistent.
- The subgroup generator builds closure rather than testing arbitrary subsets.
- Quotients correctly enforce normality.
- The CLI warns users that factorial and subgroup growth make large cases impractical.

## Main limitations of the CLI

- Every action is modal and text-only; comparing multiple structures requires scrolling terminal output.
- Selecting permutations by printed index becomes cumbersome when `n!` grows.
- The ASCII polygon is informative but not geometric.
- Cayley tables become unreadable in a terminal before they become computationally impossible.
- Exhaustive subgroup output has no progressive visual hierarchy.
- Conjugacy classes, a natural structural view of `S_n`, are absent.

## Web-extension strategy

The GUI does **not** reimplement the mathematics in JavaScript. Python remains the computational source of truth and returns JSON. JavaScript is restricted to interaction and rendering.

This keeps the project conceptually aligned with the original code while adding:

- paginated and filtered element browsing;
- persistent permutation inspection;
- structured composition cards;
- scrollable Cayley tables;
- SVG geometry for `D_m`;
- generated-subgroup mode for larger groups;
- visual normality/quotient workflow;
- conjugacy-class classification by cycle type.

## Why not Streamlit for this version

The repository already contains a Streamlit GUI. Streamlit is useful for rapidly exposing Python data applications, but an explicit HTML interface gives finer control over interaction, layout, responsiveness, table behavior, SVG geometry, and future deployment. The dependency-free HTTP server also avoids a Python web-framework requirement while preserving the original engine.
