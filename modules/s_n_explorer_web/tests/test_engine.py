import math

from symmetric_group import (
    all_subgroups,
    build_dihedral_group,
    cayley_table,
    compose,
    conjugacy_class_summaries,
    generate_permutations,
    inverse,
    is_normal_subgroup,
    order,
    quotient_group,
    sign,
)


def test_s3_has_factorial_many_elements():
    assert len(generate_permutations(3)) == math.factorial(3) == 6


def test_composition_convention_and_inverse():
    sigma = [1, 0, 2]  # (1 2)
    tau = [1, 2, 0]    # (1 2 3)
    assert compose(sigma, tau) == [0, 2, 1]
    assert compose(sigma, inverse(sigma)) == [0, 1, 2]
    assert compose(tau, inverse(tau)) == [0, 1, 2]


def test_order_and_sign():
    transposition = [1, 0, 2]
    three_cycle = [1, 2, 0]
    assert order(transposition) == 2
    assert sign(transposition) == -1
    assert order(three_cycle) == 3
    assert sign(three_cycle) == 1


def test_s3_subgroups_and_normal_subgroups():
    s3 = generate_permutations(3)
    subgroups = all_subgroups(s3)
    assert len(subgroups) == 6
    normal_orders = sorted(len(h) for h in subgroups if is_normal_subgroup(h, s3))
    assert normal_orders == [1, 3, 6]


def test_s3_mod_a3_has_order_two():
    s3 = generate_permutations(3)
    a3 = [p for p in s3 if sign(p) == 1]
    q = quotient_group(a3, s3)
    assert q["order"] == 2
    assert q["table"] == [[0, 1], [1, 0]]


def test_cayley_table_is_latin_square_for_s3():
    s3 = generate_permutations(3)
    table = cayley_table(s3)
    target = list(range(6))
    assert all(sorted(row) == target for row in table)
    assert all(sorted(table[i][j] for i in range(6)) == target for j in range(6))


def test_dihedral_d5_has_ten_unique_elements_and_relation():
    d5 = build_dihedral_group(5)
    assert len(d5) == 10
    assert len({tuple(x["permutation"]) for x in d5}) == 10
    r = d5[1]["permutation"]
    s = d5[5]["permutation"]
    assert compose(compose(s, r), s) == inverse(r)


def test_s3_conjugacy_classes_have_sizes_1_2_3():
    classes = conjugacy_class_summaries(3)
    assert sorted(c["size"] for c in classes) == [1, 2, 3]
