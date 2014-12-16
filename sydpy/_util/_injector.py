######################################################################
## 
## Feature Broker
## 
######################################################################

class FeatureBroker:
    def __init__(self, allowReplace=False):
        self.providers = {}
        self.allowReplace = allowReplace
    def Provide(self, feature, provider, *args, **kwargs):
        if not self.allowReplace:
            assert not (feature in self.providers), "Duplicate feature: %r" % feature
        if callable(provider):
            def call(): return provider(*args, **kwargs)
        else:
            def call(): return provider
        self.providers[feature] = call
    def __getitem__(self, feature):
        try:
            provider = self.providers[feature]
        except KeyError:
            raise KeyError("Unknown feature named {0}".format(feature))
        return provider()

features = FeatureBroker(allowReplace=True)

######################################################################
## 
## Representation of Required Features and Feature Assertions
## 
######################################################################

#
# Some basic assertions to test the suitability of injected features
#

def NoAssertion(obj): return True

def IsInstanceOf(*classes):
    def test(obj): return isinstance(obj, classes)
    return test

def HasAttributes(*attributes):
    def test(obj):
        for each in attributes:
            if not hasattr(obj, each): return False
        return True
    return test

def HasMethods(*methods):
    def test(obj):
        for each in methods:
            try:
                attr = getattr(obj, each)
            except AttributeError:
                return False
            if not callable(attr): return False
        return True
    return test

#
# An attribute descriptor to "declare" required features
#

def RequiredVariable(feature, assertion=NoAssertion):
    obj = features[feature]
    assert assertion(obj), \
             "The value %r of %r does not match the specified criteria" \
             % (obj, feature)
    return obj

class RequiredFeature(object):
    def __init__(self, feature, assertion=NoAssertion):
        self.feature = feature
        self.assertion = assertion
    def __get__(self, obj, T):
        return self.result # <-- will request the feature upon first call
    def __getattr__(self, name):
        assert name == 'result', "Unexpected attribute request other then 'result'"
        self.result = self.Request()
        return self.result
    def Request(self):
        obj = features[self.feature]
        assert self.assertion(obj), \
                 "The value %r of %r does not match the specified criteria" \
                 % (obj, self.feature)
        return obj

# class Component(object):
#     "Symbolic base class for components"