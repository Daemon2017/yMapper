[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Daemon2017_yMapper&metric=alert_status)](https://sonarcloud.io/dashboard?id=Daemon2017_yMapper)
# yMapper
yMapper - это программа, позволяющая в автоматическом режиме строить карты таксономического разнообразия выбранного Y-SNP. Результатом её работы является топографическая карта [Stamen](http://maps.stamen.com/terrain/), на которую нанесен слой с сеткой из шестиугольных ячеек, при наведении на любую из которых появляется всплывающая подсказка, содержащая информацию о том, какие именно подветви выбранного Y-SNP присутствуют в ней присутствуют. Также, используется зрительное отражение уровня таксономического разнообразия: чем оно выше, тем ниже прозрачность ячейки. Карта может состоять из множества слоев с различными размерами ячеек, что позволяет отражать сведения о разнообразии подветвей в различных приближениях.
<br>Ниже приведен пример карты таксономического разнообразия SNP R-CTS1211, построенной с помощью yMapper, а на живые карты Вы можете взглянуть [здесь](https://daemon2017.github.io/yFarseer/).
![Карта таксономического разнообразия R-CTS1211](https://sun9-66.userapi.com/c813024/v813024186/51cb6/0KsPWHXJSA4.jpg "Карта таксономического разнообразия R-CTS1211")

## Для чего всё это?
Существует 2 критерия, по которым можно предсказать область происхождения Y-SNP, а значит и всей генетической популяции, являющейся его носителем:
* критерий частоты - SNP образовался в том регионе, в котором он встречается чаще всего;
* критерий разнообразия - SNP образовался в том регионе, где наблюдается наибольшее разнообразие его подветвей.

<br>Таким образом, данная программа позволяет строить наглядные карты по критерию разнообразия, которые могут быть использованы в определении области происхождения того или иного SNP.

## Состав программы
Программа состоит из 4  модулей:
* **ftdna_tree_collector_rest.py** - получает [Y-древо FTDNA](https://www.familytreedna.com/public/y-dna-haplotree/);
* **mapper.py** -  отрисовывает на карте те SNP, которые, по данным Y-древа FTDNA, восходят к дочерним SNP целевого SNP (например, для целевого SNP [R-Z283](https://www.yfull.com/tree/R-Z283/) дочерними SNP будут являться R-Y128147, R-YP4758 и R-Z282);
* **predictor.py** - обучает модель градиентного бустинга выявлять дочерние SNP целевого SNP по 12/37/67/111 STR тех наборов, у которых или сделан NGS (*30X Whole Genome Sequencing Test* от Dante Labs, *BigY700* от FTDNA и пр.), или концевой (терминальный) SNP является нисходящим по отношению к дочерним SNP целевого SNP. Функционал этого модуля используется только в расширенном варианте применения;
* **utils.py** - выполняет вспомогательные действия.

## Требования к установленному ПО
* Python 3.* (например, 3.5);
* модули Python: folium, numpy, scikit-learn, xgboost, pandas, shapely.

## Требования ко входным данным
CSV-файл со входными данными должен иметь Pandas-формат и содержать следующие столбцы-заголовки (порядок не имеет значения):
```
Kit Number,Short Hand,CDY,DYF395S1,DYF406S1,DYS19,DYS385,DYS388,DYS389i,DYS389ii,DYS390,DYS391,DYS392,DYS393,DYS413,DYS425,DYS426,DYS434,DYS435,DYS436,DYS437,DYS438,DYS439,DYS441,DYS442,DYS444,DYS445,DYS446,DYS447,DYS448,DYS449,DYS450,DYS452,DYS454,DYS455,DYS456,DYS458,DYS459,DYS460,DYS461,DYS462,DYS463,DYS464,DYS472,DYS481,DYS485,DYS487,DYS490,DYS492,DYS494,DYS495,DYS497,DYS504,DYS505,DYS510,DYS511,DYS513,DYS520,DYS522,DYS525,DYS531,DYS532,DYS533,DYS534,DYS537,DYS540,DYS549,DYS552,DYS556,DYS557,DYS561,DYS565,DYS568,DYS570,DYS572,DYS575,DYS576,DYS578,DYS587,DYS589,DYS590,DYS593,DYS594,DYS607,DYS617,DYS632,DYS635,DYS636,DYS638,DYS640,DYS641,DYS643,DYS650,DYS710,DYS712,DYS714,DYS715,DYS716,DYS717,DYS726,Y-GATA-A10,Y-GATA-H4,Y-GGAAT-1B07,YCAII,lat,lng,NGS
```
Где 
* Kit Number - уникальное имя образца, например, 329713;
* Short Hand - имя концевого SNP в формате FTDNA, например, R-Y35189;
* lat - широта, например, 54.31041;
* lng - долгота, например, 26.8488827;
* NGS - флаг наличия полногеномного теста (NGS), например, True;
* остальные - значения STR-маркеров в формате FTDNA.

<br>На примере моего образца:
```
329713,R-BY82934,33-36,17-17,9.0,16,12-13,13.0,12.0,28.0,25.0,10.0,11.0,13.0,20-22,12.0,12.0,9.0,11.0,12.0,14.0,11.0,10.0,13.0,13.0,13.0,12.0,12.0,24.0,20.0,33.0,8.0,31.0,11.0,11.0,15.0,15.0,9-10,10.0,11.0,11.0,24.0,13-15-16-16,8.0,23.0,15.0,13.0,12.0,12.0,9.0,15.0,15.0,14.0,12.0,17.0,10.0,15.0,21.0,10.0,10.0,11.0,11.0,12.0,14.0,12.0,12.0,12.0,24.0,12.0,15.0,15.0,13.0,11.0,20.0,11.0,10.0,18.0,8.0,19.0,12.0,8.0,15.0,10.0,16.0,12.0,9.0,23.0,11.0,11.0,11.0,10.0,10.0,19.0,32.0,18.0,25.0,22.0,27.0,19.0,12.0,13.0,10.0,9.0,19-23,54.31041,26.8488827,True
```
Советы по улучшению данных:
* Если у какого-то образца нет сведений о концевом SNP, либо указанный концевой SNP является очень поверхностным, но Вы считаете образец особенно важным для всего исследования в целом, то имеет смысл самостоятельно предсказать его SNP с помощью пророка [Nevgen](http://www.nevgen.org/) - он использует подход с Байесовской вероятностью и дает меньше ложноположительных/ложноотрицательных срабатываний, чем подход на основе градиентного бустинга.

## Установка Python, зависимостей (Windows) и запуск .py-файлов
1. Откройте [страницу](https://www.python.org/downloads/windows/) загрузки версий Python под Windows и скачайте *Windows x86-64 executable installer* для версии не ниже 3.5.* - например, версию *Python 3.5.3 - Jan. 17, 2017*. Запустите загруженный файл и выполните установку.
2. Откройте командную строку, нажав комбинацию *Win+R*, введя *cmd* и нажав *ОК*. Перейдите в папку, где расположены .py-файлы yMapper'а, с помощью команды *cd*, например, так: 
   >cd C:\Users\Daemon2017\PycharmProjects\yMapper
   
   <br>Введите команду:
   >pip install -r requirements.txt
   
   <br>после чего дождитесь окончания загрузки и установки всех необходимых пакетов.
3. Чтобы запустить .py-файл, необходимо ввести команду: 
   >python mapper.py

## Варианты использования
### Минимальный
Минимальный вариант использования подразумевает, что Ваша цель - построить карту таксономического разнообразия, используя лишь те сведения, которые на 100% являются достоверными, пусть и не настолько полными, насколько это возможно. Необходимо выполнить следующие действия:
* В Notepad'е откройте файл mapper.py и задайте 10 настроек:
    - is_extended: False;
    - target_snp: имя Y-SNP, таксономическое разнообразие которого Вы хотите исследовать. Обратите внимание, что его нужно указывать в том виде, в котором оно отражено в Y-древе FTDNA;
    - Настройки сетки из ячеек-шестиугольников:
       - x_0: долгота левого нижнего угла сетки;
       - y_0: широта левого нижнего угла сетки;
       - x_1: долгота правого верхнего угла сетки;
       - y_1: широта правого верхнего угла сетки;
    - Начальные настройки карты:
      - x_center: долгота начальной середины карты;
      - y_center: широта начальной середины карты;
      - zoom: первоначальное приближение карты;
    - h_list: список из размеров ячеек - чем больше значений в списке, тем больше слоев будет иметь выходная карта;
* Запустите получившийся блокнот через Cell -> Run All и дождитесь завершения работы - Вы увидите отрисованную карту в предпоследнем шаге блокнота и файл вида map_{target_snp}.html в папке проекта. На время работы больше всего влияют 3 настройки: размер сетки, зернистость сетки и количество размеров ячеек в списке. При настройках по умолчанию, на построение карты уйдет около 1/3 часа.
### Максимальный
Максимальный вариант использования подразумевает, что Ваша цель - построить карту таксономического разнообразия, используя все доступные сведения - даже если результат будет иметь некоторые ошибки. Необходимо выполнить следующие действия:
* В Notepad'е откройте файл mapper.py и задайте 10 настроек:
    - is_extended: True;
    - target_snp: имя Y-SNP, таксономическое разнообразие которого Вы хотите исследовать. Обратите внимание, что его нужно указывать в том виде, в котором оно отражено в Y-древе FTDNA;
    - Настройки сетки из ячеек-шестиугольников:
       - x_0: долгота левого нижнего угла сетки;
       - y_0: широта левого нижнего угла сетки;
       - x_1: долгота правого верхнего угла сетки;
       - y_1: широта правого верхнего угла сетки;
    - Начальные настройки карты:
      - x_center: долгота начальной середины карты;
      - y_center: широта начальной середины карты;
      - zoom: первоначальное приближение карты;
    - h_list: список из размеров ячеек - чем больше значений в списке, тем больше слоев будет иметь выходная карта;
* Запустите получившийся блокнот через Cell -> Run All и дождитесь завершения работы - Вы увидите отрисованную карту в предпоследнем шаге блокнота и файл вида map_{target_snp}_extended.html в папке проекта. На время работы больше всего влияют 3 настройки: размер сетки, зернистость сетки и количество размеров ячеек в списке. При настройках по умолчанию, на построение карты уйдет чуть более часа.

## Благодарности
Хочу поблагодарить форумчанина [**TK**](http://forum.molgen.org/index.php?action=profile;u=6135) за то, что он объяснил мне основные тонкости построения карт таксономического разнообразия: спасибище и низкий поклон - дело, начатое Вами, дало мне заряд на многие вечера и ночи! :)
