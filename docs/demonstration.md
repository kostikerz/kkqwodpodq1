# Примеры запуска и ошибок

## demo, этап 1

```text
package=A
repository=C:\Users\HONOR\Documents\Codex\2026-11-17\new-chat\outputs\kkqwodpodq1\examples\graph.csv
test_mode=True
output=C:\Users\HONOR\Documents\Codex\2026-11-17\new-chat\outputs\kkqwodpodq1\artifacts\demo.png
max_depth=10
filter_substring=
exit=0
```

## demo, этап 2

```text
B
C
exit=0
```

## demo, этап 3

```text
A: B C
B: D
D:
C: D
exit=0
```

## demo, этап 4

```text
1. D
2. B
3. C
4. A
exit=0
```

## cycle, этап 3

```text
A: B
B: C
C: A
exit=0
```

## cycle, этап 4

```text
1. cycle group: A, B, C
exit=0
```

## shorter, этап 3

```text
A: B D
B: C
C: D
D: E
E: F
F:
exit=0
```

## shorter, этап 4

```text
1. F
2. E
3. D
4. C
5. B
6. A
exit=0
```

## Ошибка package

```text
Error: Invalid package name
exit=1
```

## Ошибка repository

```text
Error: repository must name an existing test file
exit=1
```

## Ошибка test_mode

```text
Error: test_mode must be true or false
exit=1
```

## Ошибка output

```text
Error: output must name a PNG file
exit=1
```

## Ошибка max_depth

```text
Error: max_depth must be a non-negative integer
exit=1
```

## Ошибка filter_substring

```text
Error: filter_substring cannot contain control characters
exit=1
```
