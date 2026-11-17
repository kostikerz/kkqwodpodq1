# Практическая работа № 2, вариант № 3

Инструмент анализа зависимостей Ubuntu (apt) на Python 3.10+.
Зависимости извлекаются самостоятельно, без apt и сторонних библиотек.

## Этап 1: CSV-конфигурация

Запуск: `python -m src.cli configs/demo.csv --stage 1`.
Также доступны `run.bat configs/demo.csv --stage 1` и
`sh run.sh configs/demo.csv --stage 1`.
Проверка: `python -m unittest discover -v`.
Сборка не требуется. Зависимостей Python вне стандартной библиотеки нет.

CSV UTF-8 содержит заголовок `key,value` и ровно шесть настроек:

| Ключ | Назначение |
| --- | --- |
| package | Имя Ubuntu-пакета или заглавные латинские буквы в тестах |
| repository | URL индекса Packages или путь к тестовому CSV |
| test_mode | true/false |
| output | Путь к PNG |
| max_depth | Целое >= 0, корень имеет глубину 0 |
| filter_substring | Исключаемая подстрока, пустая отключает фильтр |

Пути вычисляются относительно конфигурации. Неизвестные/повторные ключи,
ошибочные значения и отсутствующие файлы дают сообщение Error и код 1.
На этапе 1 все параметры выводятся в формате ключ=значение.
Каждый этап сохраняется отдельным Conventional Scoped Commit.

## Этап 2: прямые зависимости Ubuntu

`python -m src.cli configs/apt.csv --stage 2` выводит прямые зависимости apt.
repository указывает на полный URL Packages, Packages.gz, Packages.xz
или Packages.bz2 конкретного выпуска, компонента и архитектуры Ubuntu.
HTTP загружается urllib.request, сжатие и Debian control разбираются
стандартной библиотекой. Учитываются Depends и Pre-Depends.
Альтернативы сохраняются все; virtual-пакет связан со всеми Provides.
Ограничения версий сохраняются в исходных полях, но не решаются.
Это консервативный граф метаданных, не решатель установки apt.
Несколько версий одного пакета в одном индексе отклоняются явно.

## Этап 3: нерекурсивный DFS

`--stage 1` показывает конфигурацию, `--stage 2` прямые зависимости,
`--stage 3` граф. Тестовый файл CSV: `package,dependencies`, зависимости
разделяются пробелами; все вершины должны быть объявлены, листья - пустые.
Примеры: `configs/demo.csv` (ромб), `configs/cycle.csv` (цикл),
`configs/shorter.csv` (повторное достижение вершины более коротким путём).

DFS использует стек, без рекурсии. Глубина - минимальное число рёбер от
корня; при более коротком пути вершина раскрывается повторно.
На границе глубины вершины включаются без дальнейшего раскрытия.
Фильтр регистрозависимый, отсекает вершину вместе с её ветвью.
Если фильтр исключает корень, выдаётся ошибка. Циклы сохраняют обратные
рёбра и не зацикливают обход. Пакеты вне выбранного индекса обозначаются
предупреждением и остаются листьями; отсутствующий корень - ошибка.

## Этап 4: порядок загрузки

`python -m src.cli configs/demo.csv --stage 4` выводит зависимости раньше
потребителей. Нерекурсивный алгоритм Косарайю выделяет циклические группы;
между группами порядок корректен, внутри цикла порядок не задаётся.
Корень включается последним, если не входит в цикл с зависимостями.
Для демонстрации повторить команду с cycle.csv и shorter.csv.
Методика сравнения с apt, объяснение расхождений и ограничения проверки:
[docs/comparison.md](docs/comparison.md).

## Этап 5: PlantUML и PNG

Установить Java 8+ и скачать официальный
[PlantUML 1.2025.2](https://repo.maven.apache.org/maven2/net/sourceforge/plantuml/plantuml/1.2025.2/plantuml-1.2025.2.jar).
Путь к JAR задаётся переменной PLANTUML_JAR. JAVA при необходимости
задаёт полный путь к java.exe. Раскладка Smetana не требует Graphviz.

```powershell
$env:PLANTUML_JAR = 'C:\tools\plantuml.jar'
python -m src.cli configs/demo.csv
python -m src.cli configs/apt.csv
python -m src.cli configs/bash.csv
python -m src.cli configs/coreutils.csv
```

```sh
export PLANTUML_JAR=/path/to/plantuml.jar
python3 -m src.cli configs/apt.csv --stage 5
```

По умолчанию запускается этап 5. Текст сохраняется рядом с PNG в .puml
и выводится в терминал. Стрелки: пакет → зависимость, корень голубой.
Если Java/JAR отсутствуют, остаётся .puml и выдаётся понятная ошибка.
Код возврата: 0 - успех, 1 - ошибка данных/ввода-вывода/рендеринга,
2 - неверные аргументы CLI. При ошибке PNG от PlantUML не сохраняется.

PNG, JAR, индексы, архивы и кэши не включаются в Git согласно правилам
преподавателя. В репозитории хранятся исходники .puml и текстовые протоколы.
GitHub Actions настроен на тесты, три визуализации и независимый эталон apt.
Успешный [запуск 44161177354](https://github.com/kostikerz/kkqwodpodq1/actions/runs/44161177354)
создал PNG и настоящий эталон apt. Текстовые результаты сохранены в
docs/reference. Оба фактических сравнения находятся в docs/comparison.md.
Проверить совпадение сохранённых графов: `python scripts/verify_reference.py`.

## Устройство и функции

| Модуль | Функции и назначение |
| --- | --- |
| config | read_rows, load_config: чтение CSV |
| config | validate_repository, validate_output: проверка путей и URL |
| config | validate_url: структура HTTP(S) URL и порт |
| repository | parse_control, dependency_groups: разбор метаданных |
| repository | decode_index, fetch_index: распаковка и HTTP |
| repository | AptRepository.dependencies: прямые зависимости/Provides |
| graph | TestRepository.dependencies: чтение тестового CSV |
| graph | build_graph: DFS, глубина, фильтр, отсутствующие пакеты |
| graph | filter_children: удаление исключённых имён и дубликатов |
| order | finishing_order, load_order, format_order: SCC и порядок |
| visualization | plantuml, render_png, save_diagram: текст и PNG |
| cli | execute, main: запуск этапа и обработка ошибок |

Все публичные функции содержат docstring. Тесты автономны и не требуют
сети, apt или Java. Интеграционные запуски с настоящим JAR и Ubuntu-индексом
протоколируются отдельно в docs/validation.md.
