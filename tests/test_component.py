from sydpy.component import Component, all2kwargs, system, compinit


def test_all2kwargs():
    def func(a, b, c, d, e=5, f=6, g=7, h=8):
        pass
    
    kwargs = all2kwargs(func, 1, 2, c=3, d=4, e=5, h=8)
    
    assert kwargs==dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8)

def test_update_params():
    conf = [('obj1.obj2.obj3.a', 4),
            ('obj1.*3.b', 4),
            ('obj1.*.obj?.c', 4),
            ('obj1.?3.c', 8),            
            ('*.*.*.d', 4),
            ('o*o*o*e', 4),
            ('*.*.*7.e', 8),
            ('obj?.obj?.obj?.f', 4),
            ('*.g', 4),
            ('*h', 4),
            ]
    
    system.set_config(conf)
    params = dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8)
    system.update_params('obj1.obj2.obj3', params)
    
    for _,v in params.items():
        assert v==4
        
def test_component_decorator():
    conf = [('obj1.obj2.obj3.a', 4),
            ('obj1.*.obj?.c', 4),
            ('*.*.*.d', 4),
            ('obj?.obj?.obj?.f', 4),
            ('*h', 4),
            ]
    
    system.set_config(conf)
    
    class Test(Component):
        @compinit
        def __init__(self, name, a, b, c, d, e=5, f=6, g=7, h=8):
            assert a==4
            assert b==10
            assert c==4
            assert d==4
    
    test = Test('obj1.obj2.obj3', 10, 10, c=10, d=10, e=10, h=10)
    
    assert test.e == 10
    assert test.f == 4
    assert test.g == 7
    assert test.h == 4
    
def create_component_tree(index_tree):
    tree = None 
    for t in index_tree:
        
        segments = t.split('/')
        current = None
        for s in segments:
            if not tree:
                tree = Component(s)
                current = tree
            elif not current:
                if s != tree.name:
                    raise Exception('Multi-root tree.')
                else:
                    current = tree
            else:
                if s not in current:
                    current += Component(s)

                current = current[s]
    
    return tree

def test_qualified_name():
    index_tree = [
                  '/child0/child1/child2/child3/child4',
                  ]
    
    tree = create_component_tree(index_tree)
    
    assert tree['child0']['child1']['child2']['child3']['child4'].qualified_name == index_tree[0]

def test_indexing():
    index_tree = [
                  '/',
                  '/child0',
                  '/child0/child1',
                  '/child0/child1/child1',
                  '/child0/child2',
                  '/child0/child2/child1',
                  '/child0/child2/child2',
                  ]
    
    tree = create_component_tree(index_tree)
    
    assert set(tree.index().keys()) == set(index_tree)

def test_pattern_search():
    index_tree = [
              '/child0/ch1/ch1/ch1',
              '/child0/ch1/ch1/ch2',                  
              '/child0/ch1/ch1/ch3',                  
              '/child0/ch2/ch1/ch1',
              '/child0/ch2/ch1/ch2',                  
              '/child0/ch2/ch1/ch3',
              '/child0/ch2/ch1/ch4',
              '/child0/ch2/ch2/ch1',
              '/child0/ch2/ch2/ch2',                  
              ]
    
    tree = create_component_tree(index_tree)
    
    assert set(tree.findall('/*/ch3').keys()) == set(['/child0/ch2/ch1/ch3', '/child0/ch1/ch1/ch3',])

test_component_decorator()
#test_all2kwargs()
#test_update_params()
# test_qualified_name()
# test_indexing()
# test_pattern_search()