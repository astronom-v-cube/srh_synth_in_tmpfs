# Скрипт для многопточного синтеза изображений с Сибирского радиогелиографа в оперативной памяти

### Что нужно знать о скрипте:
1. Работает с библиотекой ```srhdata```
2. ```srh48_api``` не поддерживается
3. Расчитан на использование с калибровочной таблицей, но поменяв параметры, можно включить синтез и без нее
4. Синтез - многопоточный. Можно менять количество потоков, то есть количество синтезируемых одновременно файлов. От количества потоков зависит потребление ресурсов процессора и оперативной памяти
5. При количестве потоков 8+ рекомендуется наличие 16+ Гб оперативной памяти
6. Для запуска скрипта у вас должна быть настроенное виртуальное окружение ```Python 3.8``` или ```Python 3.10```, установленная библиотека ```srhdata``` со всеми зависимостями

### Как использовать скрипт:
1. а никак