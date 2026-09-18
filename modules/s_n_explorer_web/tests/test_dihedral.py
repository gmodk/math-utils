"""Independent algebra and geometric-action checks for every required n."""
import math
import pytest
from symmetric_group import build_dihedral_group, compose, inverse, identity
from modules.s_n_explorer_web.app import serialize_dihedral
from dihedral_visualization import geometry


def apply_axis(point, axis, angle):
    x,y,z=point; u,v,w=axis
    c,s=math.cos(angle),math.sin(angle); dot=x*u+y*v+z*w
    cross=[v*z-w*y,w*x-u*z,u*y-v*x]
    return [p*c+q*s+a*dot*(1-c) for p,q,a in zip(point,cross,axis)]


@pytest.mark.parametrize('n',range(3,13))
def test_group_relations_and_validity(n):
    rows=build_dihedral_group(n)
    assert len(rows)==2*n==len({tuple(e['permutation']) for e in rows})
    assert all(sorted(e['permutation'])==list(range(n)) for e in rows)
    r,s=rows[1]['permutation'],rows[n]['permutation']
    power=identity(n)
    for _ in range(n): power=compose(power,r)
    assert power==identity(n)
    assert compose(s,s)==identity(n)
    assert compose(compose(s,r),s)==inverse(r)


@pytest.mark.parametrize('n',range(3,13))
def test_rotation_angles_and_polygon_prism_action(n):
    g=geometry(n)
    for k,e in enumerate(serialize_dihedral(n)[:n]):
        a=e['animation']
        assert a['rotation_angle_rad']==pytest.approx(2*math.pi*k/n)
        assert a['axis_vector']==[0,1,0]
        for i,p in enumerate(g['prism_vertices']):
            assert apply_axis(p,a['axis_vector'],a['angle_rad'])==pytest.approx(a['prism_targets'][i],abs=1e-10)
        assert a['polygon_targets']==[g['polygon'][j] for j in e['permutation']]


@pytest.mark.parametrize('n',range(3,13))
def test_reflection_axes_layers_and_actions(n):
    g=geometry(n)
    for k,e in enumerate(serialize_dihedral(n)[n:]):
        a=e['animation']; axis=a['axis_vector']
        assert a['axis_angle_rad']==pytest.approx(-math.pi*k/n)
        assert a['angle_rad']==pytest.approx(math.pi)
        for i,p in enumerate(g['prism_vertices']):
            target=a['prism_targets'][i]
            assert apply_axis(p,axis,math.pi)==pytest.approx(target,abs=1e-10)
            assert target[1]==-p[1]
            assert a['prism_permutation'][i] % n==e['permutation'][i % n]
        for i,(x,y) in enumerate(g['polygon']):
            u,v=axis[0],-axis[2]; dot=x*u+y*v
            assert [2*dot*u-x,2*dot*v-y]==pytest.approx(a['polygon_targets'][i],abs=1e-10)


@pytest.mark.parametrize('n',range(3,13))
def test_label_styles_keep_vertex_indices(n):
    g=geometry(n)
    assert g['labels']['numbers']==[str(i+1) for i in range(n)]
    assert g['labels']['greek']==list('αβγδεζηθικλμ')[:n]
    assert g['vertex_classes']==[{'index':i,'pair':[i,i+n]} for i in range(n)]
    for e in serialize_dihedral(n):
        for i,j in enumerate(e['permutation']):
            for style in ('numbers','greek'):
                labels=g['labels'][style]
                assert labels.index(labels[j])==j
                assert e['animation']['prism_permutation'][i] % n==j


def test_cube_has_equal_edges_and_legacy_range_survives():
    g=geometry(4)
    lengths=[math.dist(g['prism_vertices'][a],g['prism_vertices'][b]) for a,b in g['edges']]
    assert all(length==pytest.approx(math.sqrt(2)) for length in lengths)
    for n in (13,24):
        assert len(serialize_dihedral(n))==2*n
        assert len(geometry(n)['labels']['greek'])==n
