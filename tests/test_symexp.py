# '''
# Created on Dec 25, 2014
# 
# @author: bvukobratovic
# '''
# from sydpy._util._symexp import SymNode
# from random import random, randint
# 
# def proxy_oper(method):
#     def wrapper(self, other):
#         return SymNode(self, method.__name__, other)
#     return wrapper
# 
# class SymLeaf(object):
#     def __init__(self, val):
#         self.val = val
#         
#     def eval(self):
#         return self.val
#     
#     @proxy_oper
#     def __add__(self, other):
#         pass
#     @proxy_oper
#     def __radd__(self, other):
#         pass
# 
#     @proxy_oper    
#     def __sub__(self, other):
#         pass
#     @proxy_oper
#     def __rsub__(self, other):
#         pass
# 
#     @proxy_oper
#     def __mul__(self, other):
#         pass
#     @proxy_oper
#     def __rmul__(self, other):
#         pass
# 
#     @proxy_oper
#     def __div__(self, other):
#         pass
#     @proxy_oper
#     def __rdiv__(self, other):
#         pass
# 
#     @proxy_oper    
#     def __truediv__(self, other):
#         pass
#     @proxy_oper
#     def __rtruediv__(self, other):
#         pass
#     
#     @proxy_oper
#     def __floordiv__(self, other):
#         pass
#     def __rfloordiv__(self, other):
#         pass
# 
#     @proxy_oper    
#     def __mod__(self, other):
#         pass
#     @proxy_oper
#     def __rmod__(self, other):
#         pass
# 
#     # XXX divmod
# 
#     @proxy_oper    
#     def __pow__(self, other):
#         pass
#     @proxy_oper
#     def __rpow__(self, other):
#         pass
# 
#     @proxy_oper
#     def __lshift__(self, other):
#         pass
#     def __rlshift__(self, other):
#         pass
# 
#     @proxy_oper            
#     def __rshift__(self, other):
#         pass
#     @proxy_oper 
#     def __rrshift__(self, other):
#         pass
# 
#     @proxy_oper           
#     def __and__(self, other):
#         pass
#     def __rand__(self, other):
#         pass
# 
#     @proxy_oper
#     def __or__(self, other):
#         pass
#     @proxy_oper
#     def __ror__(self, other):
#         pass
#     
#     @proxy_oper
#     def __xor__(self, other):
#         pass
#     @proxy_oper
#     def __rxor__(self, other):
#         pass
#     @proxy_oper
#     def __neg__(self):
#         pass
#     @proxy_oper
#     def __pos__(self):
#         pass
#     @proxy_oper
#     def __abs__(self):
#         pass
#     @proxy_oper
#     def __invert__(self):
#         pass
#         
#     # conversions
#     @proxy_oper
#     def __int__(self):
#         pass
#     @proxy_oper
#     def __float__(self):
#         pass
#     @proxy_oper
#     def __oct__(self):
#         pass
#     @proxy_oper
#     def __hex__(self):
#         pass
#     @proxy_oper
#     def __index__(self):
#         pass
# 
#     # comparisons
#     @proxy_oper
#     def __eq__(self, other):
#         pass
#     
#     @proxy_oper
#     def __ne__(self, other):
#         pass 
#     @proxy_oper
#     def __lt__(self, other):
#         pass
#     @proxy_oper
#     def __le__(self, other):
#         pass
#     @proxy_oper
#     def __gt__(self, other):
#         pass
#     @proxy_oper
#     def __ge__(self, other):
#         pass
# 
# def test_symexp():
#     a_val = random()
#     b_val = random()
#     c_val = random()
#     d_val = random()
#     e_val = random()
#     
#     a = SymLeaf(a_val)
#     b = SymLeaf(b_val)
#     c = SymLeaf(c_val)
#     d = SymLeaf(d_val)
#     e = SymLeaf(e_val)
#     
#     exp = a * 22 ** b + c / 84 - d ** 2 * 5 * e
#     exp_val = a_val * 22 ** b_val + c_val / 84 - d_val ** 2 * 5 * e_val
#     assert exp.eval() == exp_val
#     
#     a_val = randint(0, (1 << 32) - 1)
#     b_val = randint(0, (1 << 32) - 1)
#     c_val = randint(0, (1 << 32) - 1)
#     d_val = randint(0, (1 << 32) - 1)
#     e_val = randint(0, (1 << 32) - 1)
#     
#     a = SymLeaf(a_val)
#     b = SymLeaf(b_val)
#     c = SymLeaf(c_val)
#     d = SymLeaf(d_val)
#     e = SymLeaf(e_val)
#     
#     exp = (7 >> a ^ b & 0x89 + c * 84 - d << e) & (b << c) | (d & 0x890)
#     exp_val = (7 >> a_val ^ b_val & 0x89 + c_val * 84 - d_val << e_val) & (b_val << c_val) | (d_val & 0x890)
#     assert exp.eval() == exp_val
#     
#     
# test_symexp()
#      
