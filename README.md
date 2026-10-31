# Hyprland Config Manager

[![Platform](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20Wayland-blue.svg)](https://archlinux.org)
[![Toolkit](https://img.shields.io/badge/GUI-GTK4%20%2B%20Libadwaita-indigo.svg)](https://gnome.pages.gitlab.gnome.org/libadwaita/)
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

**Hyprland Config Manager** — современное, нативное графическое приложение (GTK4 + Libadwaita) для полного управления конфигурацией композитора **Hyprland** в Arch Linux.

Приложение избавляет пользователя от необходимости вручную редактировать текстовый файл `hyprland.conf`, предоставляя интуитивный и эстетичный интерфейс в стиле настроек современного Linux Desktop.

---

## Архитектура & Принцип работы

```
+-------------------------------------------------------------------------+
|                  Hyprland Config Manager (GTK4 / Libadwaita)            |
+-------------------------------------------------------------------------+
     |                                                               ^
     v                                                               |
+-------------------+      +-------------------+      +-------------------+
|   Config Engine   | ---> | Hyprland AST Model| ---> |    Generator      |
|  (Parser & Model) | <--- |(Preserves Comments| <--- |   (Unified Diff)  |
+-------------------+      +-------------------+      +-------------------+
     |                                                          |
     v                                                          v
+-------------------+      +-------------------+      +-------------------+
|  Backup Manager   |      | HyprlandValidator |      | SafeApplyPipeline |
| (Timestamped auto)|      | (Syntax & Checks) |      | (Atomic & Rollback|
+-------------------+      +-------------------+      +-------------------+
                                                                |
                                                                v
                                                      +-------------------+
                                                      | hyprctl IPC Client|
                                                      | (Real-time reload)|
                                                      +-------------------+
```

1. **Config Engine & AST Parser**: парсит `hyprland.conf` в абстрактное синтаксическое дерево (AST), на 100% сохраняя структуру файла, пользовательские комментарии, неизвестные композитору блоки и директивы `source = ...`.
2. **Безопасная транзакция применения (Safe Apply)**:
   $$\text{Текущий конфиг} \longrightarrow \text{Бэкап} \longrightarrow \text{Генерация} \longrightarrow \text{Валидация} \longrightarrow \text{Атомарная запись} \longrightarrow \text{hyprctl reload} \longrightarrow \text{Проверка}$$
3. **Автоматический откат (Automatic Rollback)**: если Hyprland отвергает конфигурацию или процесс применения прерывается, приложение автоматически восстанавливает рабочий бэкап и возвращает композитор в стабильное состояние. Кнопка **[Rollback]** доступна всегда в нижней панели.
4. **Режим Offline / Headless**: если Hyprland временно не запущен (например, вход из консоли TTY), приложение не падает, а открывается в режиме безопасного редактирования с понятным статусом: `Hyprland is not running (Offline / File Edit Mode)`.

---

## Возможности экранов

- **Dashboard**: телеметрия Hyprland (версия, активные мониторы, рабочие места, сфокусированное окно, дата изменения конфига, текущий профиль) и кнопки быстрых действий: `[Apply]`, `[Reload]`, `[Validate]`, `[Backup]`, `[Restore]`.
- **Monitors**: управление разрешениями, частотой обновления (Гц), положением экранов ($X \times Y$), масштабированием Wayland (дробный скейлинг 1.0, 1.25, 1.5, 2.0...), VRR (Adaptive Sync) и поворотом дисплеев. Автоматически опрашивает реальные мониторы через `hyprctl -j monitors`.
- **Windows**: настройка радиуса скругления углов (`rounding`), внутренних и внешних отступов (`gaps_in`, `gaps_out`), ширины рамок (`border_size`), алгоритмов тайлинга (`dwindle`, `master`), теней и эффекта размытия Dual-Kawase (`blur`).
- **Appearance**: выбор готовых цветовых схем (**Catppuccin**, **Tokyo Night**, **Gruvbox**, **Nord**, **Dracula**, **AMOLED**, **Dark**, **Light**), настройка градиентных рамок (`col.active_border`) и создание пользовательских тем.
- **Animations**: интерактивная настройка скоростей анимации, кривых Безье (Cubic Bezier) и переключение пресетов: **Smooth**, **Minimal**, **Fast**, **Gaming** (анимации отключены для максимального FPS).
- **Input**:
  - *Мышь*: чувствительность, профиль ускорения (`adaptive`, `flat`), естественная прокрутка.
  - *Клавиатура*: переключение раскладок (`us,ru`), параметры XKB (`grp:alt_shift_toggle`, `caps:escape`), скорость и задержка автоповтора, NumLock по умолчанию.
  - *Тачпад*: жесты, естественная прокрутка, Tap-to-Click, отключение при наборе текста.
- **Keybinds**: таблица горячих клавиш с поиском, возможностью добавления/редактирования/удаления и **автоматическим обнаружением конфликтов комбинаций** (например, `SUPER + Q уже используется`).
- **Startup**: управление программами автозапуска (`exec-once` и `exec`) с переключателями включения/отключения без удаления строк.
- **Workspaces**: привязка воркспейсов к конкретным мониторам, постоянные (persistent) воркспейсы и спец-пространства (scratchpads).
- **Window Rules**: визуальный конструктор правил `windowrulev2` (плавающие окна, прозрачность, привязка к воркспейсу, размер, центрирование) без необходимости вручную писать регулярные выражения.
- **Wallpapers**: выбор обоев, поддержка демонов `hyprpaper`, `swww`, `swaybg`, `feh`, живой предпросмотр.
- **Environment**: управление переменными окружения (`env = ...`) для Wayland, курсоров, GTK/Qt бэкендов и Electron.
- **Advanced**: тонкая настройка алгоритма `dwindle` (псевдотайлинг, сохранение сплитов), переменная частота кадров (`vfr`) и опции композитора.
- **Profiles**: система профилей (**Gaming**, **Work**, **Laptop**, **Minimal**, **Streaming**) с возможностью создания, дублирования, экспорта, импорта и безопасной активации с автобэкапом.
- **Config Editor**: встроенный редактор с подсветкой, номерами строк, поиском, проверкой синтаксиса и двусторонней синхронизацией с GUI.
- **Backups**: история резервных копий с отображением diff-изменений, даты, причины создания и кнопкой мгновенного отката.

---

## Установка на Arch Linux

### Способ 1: Сборка через PKGBUILD (Рекомендуемый)

Склонируйте репозиторий и соберите нативный пакет Arch Linux с помощью стандартной утилиты `makepkg`:

```bash
# 1. Перейдите в каталог проекта
cd hyprland-config-manager

# 2. Соберите и установите пакет вместе с зависимостями
makepkg -si
```

### Способ 2: Установка из AUR (после публикации)

```bash
# Через yay
yay -S hyprland-config-manager

# Или через paru
paru -S hyprland-config-manager
```

### Способ 3: Запуск напрямую из исходников (для разработки)

```bash
# Установите системные зависимости через pacman:
sudo pacman -S python python-gobject gtk4 libadwaita hyprland

# Запустите приложение напрямую:
python -m hyprconf_manager.main
```

---

## Зависимости

### Основные (Arch Linux packages):
- `python` ($\ge 3.9$)
- `python-gobject` (PyGObject для GTK4 и Libadwaita)
- `gtk4` (Нативный Wayland UI тулкит)
- `libadwaita` (Компоненты современного интерфейса GNOME/Linux)
- `hyprland` (Wayland композитор)

### Опциональные (рекомендуемые):
- `hyprpaper` или `swww` / `swaybg` (демоны обоев)
- `wl-clipboard` (интеграция с буфером обмена Wayland)
- `xdg-utils` (открытие системных директорий и файлов)

---

## Использование через консоль (CLI)

Помимо полнофункционального GUI, приложение поддерживает быстрые CLI-команды для автоматизации и скриптов:

```bash
# Проверить синтаксис и целостность hyprland.conf
hyprland-config-manager --validate

# Вывести статус работы Hyprland и конфигурации
hyprland-config-manager --status

# Создать немедленный резервный снимок конфигурации
hyprland-config-manager --backup "Снимок перед обновлением драйверов"

# Посмотреть список всех доступных бэкапов
hyprland-config-manager --list-backups

# Откатить конфигурацию до последнего бэкапа
hyprland-config-manager --rollback

# Показать список профилей
hyprland-config-manager --profiles

# Активировать профиль Gaming
hyprland-config-manager --activate-profile Gaming

# Показать diff между конфигом на диске и GUI-моделью
hyprland-config-manager --diff

# Указать нестандартный путь к файлу конфигурации
hyprland-config-manager -c /path/to/custom/hyprland.conf
```

---

## Удаление (Uninstall)

Если пакет был установлен через `makepkg` или AUR:

```bash
sudo pacman -R hyprland-config-manager
```

---

## Запуск юнит-тестов

В проекте реализован полный набор юнит-тестов, проверяющий парсер, генератор, валидатор, бэкапы, обнаружение конфликтов и транзакционный откат:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
