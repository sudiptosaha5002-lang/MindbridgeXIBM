from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'area', 'base', 'col', 'embed', 'track', 'wbr'}

    def handle_starttag(self, t, a):
        if t not in self.void:
            self.stack.append(t)

    def handle_endtag(self, t):
        if t in self.void:
            return
        if self.stack and self.stack[-1] == t:
            self.stack.pop()
        elif t in self.stack:
            while self.stack and self.stack[-1] != t:
                self.errors.append('unclosed ' + self.stack.pop())
            self.stack.pop()
        else:
            self.errors.append('stray /' + t)

html = open('index.html', encoding='utf-8').read()
p = P()
p.feed(html)
print('unclosed:', p.stack[:10])
print('errors:', p.errors[:10])
ids = ['emergencyHospitalFilter', 'filterHospital', 'emergencyExpFilter', 'emergencyRatingFilter',
       'emergencyLocInput', 'clinicLocInput', 'emergencyDocsGroups', 'clinicalCentersList']
print('ids:', {i: ('id="%s"' % i) in html for i in ids})
