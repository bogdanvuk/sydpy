from sydpy.component import Component


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
                    raise Exception('Multi-child0 tree.')
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

test_qualified_name()
test_indexing()
test_pattern_search()