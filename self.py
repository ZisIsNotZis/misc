x = '''x = \'''{}\'''
print(x.format(x.replace('\\\\','\\\\\\\\').replace("''","\\''")))'''
print(x.format(x.replace('\\', '\\\\').replace("''", "\\''")))

x = '''code = \'''{}\'''
print(code.format(code.replace('\\\\','\\\\\\\\').replace("\''","\\\''")))'''
print(code.format(code.replace('\\', '\\\\').replace("''", "\''")))


# start
x = '''#start
x = \'''{}\'''
#middle
print(x.format(x.replace('\\\\','\\\\\\\\').replace("'""'","\\\\'""'")))
#end'''
# middle
print(x.format(x.replace('\\', '\\\\').replace("'""'", "\\'""'")))
# end

interesting. You sort of avoided this problen by only converting to

x = '''x = \'''{}\'''
print(x.format(x.replace('\\\\',r'\\\\').replace("'""'",r"\\'""'")))'''
print(x.format(x.replace('\\', r'\\').replace("'""'", r"\'""'")))

still wrong. this is a working one i write
```python
x = '''x = \'''{}\'''
print(x.format(x.replace('\\\\',r'\\\\').replace("'""'",r"\\'""'")))'''
print(x.format(x.replace('\\', r'\\').replace("'""'", r"\'""'")))
```
# begin

print(123, 'abc', "def", "\n")
# end

s = 's = {quote}{s}{quote}{newline}print(s.format(quote=chr(39), s=s, newline=chr(10)))'
print(s.format(quote=chr(39), s=s, newline=chr(10)))
