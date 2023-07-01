import pymysql
import pandas as pd
from config import host, user, pasword, db_name

path_chek = r"C:\Users\yaroslav.havrel\Desktop\Work Local\Програмування\Проект. Підбір ШГРП\chek.xlsx"

# роблю підключення до бази даних
try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    # print("Successfully connection...")

    # вибираю вихідні дані, що необхідні для даного модуля
    with connection.cursor() as c:
        c.execute("SELECT id, p_in_design,p_in_w_nom,p_in_w_min,p_in_s_nom,p_in_s_min,p_out_w_max,p_out_w_nom,p_out_w_min,\
        p_out_s_max,p_out_s_nom,p_out_s_min,q_max,period,opso,upso,eq_type,reduction_lines FROM input_data ORDER BY id DESC LIMIT 1")
        input_data = c.fetchall()

    # завантажую дані про всі регулятори fiorentini
    with connection.cursor() as c:
        c.execute("SELECT * FROM fiorentini")
        f_data = c.fetchall()


except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю змінні по вихідних даних
p_in_design = input_data[0]["p_in_design"]
p_in_w_nom = input_data[0]['p_in_w_nom']
p_in_w_min = input_data[0]['p_in_w_min']
p_in_s_nom = input_data[0]['p_in_s_nom']
p_in_s_min = input_data[0]['p_in_s_min']
p_out_w_max = input_data[0]['p_out_w_max']
p_out_w_nom = input_data[0]['p_out_w_nom']
p_out_w_min = input_data[0]['p_out_w_min']
p_out_s_max = input_data[0]['p_out_s_max']
p_out_s_nom = input_data[0]['p_out_s_nom']
p_out_s_min = input_data[0]['p_out_s_min']
q_max = input_data[0]['q_max']
period = input_data[0]['period']
opso = input_data[0]['opso']
upso = input_data[0]['upso']
eq_type = input_data[0]['eq_type']
reduction_lines = input_data[0]['reduction_lines']

# створюю таблицю даних для розрахунків
fiorentini = pd.DataFrame(f_data,
                          columns=['id', 'price_priority', 'tables_name', 'grup_reg', 'regulator', 'p_in_reg_max',
                                   'p_out_reg_min', 'p_out_reg_max', 'priorety', 'slum_shut_valve', 'relif_valve',
                                   'dn_reg_in','dn_reg_out'])
fiorentini.set_index("id", inplace=True)

# вибираю дані відповідно до періоду
if period == "winter":
    p_in_nom = p_in_w_nom
    p_in_min = p_in_w_min
    p_out_nom = p_out_w_nom
    p_out_nom_ncalc = p_out_s_nom
    p_out_max_calc = p_out_w_max
    p_out_min_calc = p_out_w_min
    p_out_max_ncalc = p_out_s_max
    p_out_min_ncalc = p_out_s_min

else:
    period = "summer"
    p_in_nom = p_in_s_nom
    p_in_min = p_in_s_min
    p_out_nom = p_out_s_nom
    p_out_nom_ncalc = p_out_w_nom
    p_out_max_calc = p_out_s_max
    p_out_min_calc = p_out_s_min
    p_out_max_ncalc = p_out_w_max
    p_out_min_ncalc = p_out_w_min

p_out_max = max(p_out_w_max, p_out_s_max)
p_out_min = min(p_out_w_min, p_out_s_min)

# рахую і додаю до таблиці даних коефіцієнт відхилення виіздного тиску віл вихю даних
fiorentini["k_p_out"] = 0
for index_number in range(len(fiorentini.index)):
    p_out_reg_min = fiorentini.loc[index_number + 1, "p_out_reg_min"]
    p_out_reg_max = fiorentini.loc[index_number + 1, "p_out_reg_max"]

    if p_out_min >= p_out_reg_min:
        k1 = 0
    else:
        k1 = abs(p_out_min - p_out_reg_min)

    if p_out_max <= p_out_reg_max:
        k2 = 0
    else:
        k2 = abs(p_out_max - p_out_reg_max)

    if p_out_nom <= p_out_reg_max and p_out_nom >= p_out_reg_min:
        k3 = 0.1
    else:
        k3 = 1

    fiorentini.loc[index_number + 1, "k_p_out"] = (k1 + k2) * k3

# вибараю регулятор, що найкраще підходить по вихідному тиску і проставляю йому 0,5 бали в таблицю даних
fiorentini["k_p_out_final"] = 0
for group_number in fiorentini["grup_reg"].unique().tolist():
    a1 = fiorentini[fiorentini["grup_reg"] == group_number]
    a1.loc[a1["k_p_out"] == a1["k_p_out"].min(), "k_p_out_final"] = 0.5

    for index_number in a1.index.tolist():
        fiorentini.loc[index_number, "k_p_out_final"] = a1.loc[index_number, "k_p_out_final"]

# рахую основний коефіцієн відповідності регулятора вихідним даним
fiorentini["k_reg"] = 0
for index_number in range(len(fiorentini.index)):
    p_out_reg_min = fiorentini.loc[index_number + 1, "p_out_reg_min"]
    p_out_reg_max = fiorentini.loc[index_number + 1, "p_out_reg_max"]

    if p_out_nom <= p_out_reg_max and p_out_nom >= p_out_reg_min:
        k1 = 1
    else:
        k1 = 0

    if p_out_nom_ncalc <= p_out_reg_max and p_out_nom_ncalc >= p_out_reg_min:
        k2 = 1
    else:
        k2 = 0

    if p_out_min >= p_out_reg_min:
        k3 = 1
    else:
        k3 = 0

    if p_out_max <= p_out_reg_max:
        k4 = 1
    else:
        k4 = 0

    fiorentini.loc[index_number + 1, "k_reg"] = k1 + k2 + k3 + k4 + fiorentini.loc[index_number + 1, "k_p_out_final"] + \
                                                fiorentini.loc[index_number + 1, "priorety"]

# виставляю виставляю True/Fols для автоматичного режиму
fiorentini["automatic_mode"] = False

for group_number in fiorentini["grup_reg"].unique().tolist():
    a1 = fiorentini[fiorentini["grup_reg"] == group_number]
    a1.loc[a1["k_reg"] == a1["k_reg"].max(), "automatic_mode"] = True

    for index_number in a1.index.tolist():
        p_out_reg_min = fiorentini.loc[index_number, "p_out_reg_min"]
        p_out_reg_max = fiorentini.loc[index_number, "p_out_reg_max"]
        p_in_reg_max = fiorentini.loc[index_number, "p_in_reg_max"]

        if p_out_reg_max >= p_out_nom and p_out_reg_min <= p_out_nom and p_in_reg_max >= p_in_design:
            fiorentini.loc[index_number, "automatic_mode"] = a1.loc[index_number, "automatic_mode"]

        else:
            fiorentini.loc[index_number, "automatic_mode"] = False

# виставляю виставляю True/Fols для ручного режиму
fiorentini["manual_mode"] = False
for index_number in fiorentini.index.tolist():
    p_out_reg_min = fiorentini.loc[index_number, "p_out_reg_min"]
    p_out_reg_max = fiorentini.loc[index_number, "p_out_reg_max"]
    p_in_reg_max = fiorentini.loc[index_number, "p_in_reg_max"]

    if p_out_reg_max >= p_out_nom and p_out_reg_min <= p_out_nom and p_in_reg_max >= p_in_design:
        fiorentini.loc[index_number, "manual_mode"] = True
    else:
        fiorentini.loc[index_number, "manual_mode"] = False
# вибираю логіку автоматичного або ручного режиму
final_mode = "automatic_mode"
if final_mode == "automatic_mode":
    fiorentini["final_mode"] = fiorentini["automatic_mode"]
else:
    fiorentini["final_mode"] = fiorentini["manual_mode"]

# вибираю розрахункову комбінацію вхідного і вихідного тисків для кожного регулятор
fiorentini["p_in_q_calc"] = 0
fiorentini["p_out_q_calc"] = 0
fiorentini["p_in_tupe"] = 0
fiorentini["p_out_tupe"] = 0

for index_number in fiorentini.index.tolist():
    if fiorentini.loc[index_number, "final_mode"] == True:
        p_out_reg_max = fiorentini.loc[index_number, "p_out_reg_max"]
        if p_in_min * 1000 >= min(p_out_max, p_out_reg_max) + 200:
            p_in_q_calc = p_in_min
            p_out_q_calc = min(p_out_max, p_out_reg_max)
            p_in_tupe = "min"
            p_out_tupe = "max"

        elif p_in_min * 1000 >= p_out_nom + 200:
            p_in_q_calc = p_in_min
            p_out_q_calc = p_out_nom
            p_in_tupe = "min"
            p_out_tupe = "nom"

        else:
            p_in_q_calc = p_in_nom
            p_out_q_calc = p_out_nom
            p_in_tupe = "nom"
            p_out_tupe = "nom"
    else:
        p_in_q_calc = 0
        p_out_q_calc = 0
        p_in_tupe = 0
        p_out_tupe = 0
    fiorentini.loc[index_number, "p_in_q_calc"] = p_in_q_calc
    fiorentini.loc[index_number, "p_out_q_calc"] = p_out_q_calc
    fiorentini.loc[index_number, "p_in_tupe"] = p_in_tupe
    fiorentini.loc[index_number, "p_out_tupe"] = p_out_tupe

# розраховую пропускну здатність для кожного з регуляторів, що підійшли по тисках
fiorentini["q_reg"] = 0
for index_number in fiorentini.index.tolist():
    if fiorentini.loc[index_number, "final_mode"] == True:
        try:
            connection = pymysql.connect(
                host=host,
                port=3306,
                user=user,
                password=pasword,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor)

            # print("Successfully connection...")

            # вибираю вихідні дані, що необхідні для даного модуля
            with connection.cursor() as c:
                qwery = 'SELECT * FROM ' + fiorentini.loc[index_number, "tables_name"] + ' WHERE p_in = 0'
                c.execute(qwery)
                p_out_reg = c.fetchall()

            p_out_reg = list(p_out_reg[0].values())[2:]

            p_out_q_calc = fiorentini.loc[index_number, "p_out_q_calc"]

            near_big = min(filter(lambda x: x >= p_out_q_calc, p_out_reg))
            near_les = max(filter(lambda x: x <= p_out_q_calc, p_out_reg))
            if near_big == near_les:
                with connection.cursor() as c:
                    qwery = 'SELECT ' + str(near_big) + 'out' + ' FROM ' + fiorentini.loc[
                        index_number, "tables_name"] + ' WHERE p_in = ' + str(
                        fiorentini.loc[index_number, "p_in_q_calc"])
                    c.execute(qwery)
                    q_reg = c.fetchall()

                q_reg = q_reg[0][str(near_big) + 'out']
            else:
                with connection.cursor() as c:
                    qwery = 'SELECT ' + str(near_les) + 'out, ' + str(near_big) + 'out' + ' FROM ' + fiorentini.loc[
                        index_number, "tables_name"] + ' WHERE p_in = ' + str(
                        fiorentini.loc[index_number, "p_in_q_calc"])
                    c.execute(qwery)
                    q_reg = c.fetchall()

                q_big = q_reg[0][str(near_big) + 'out']
                q_les = q_reg[0][str(near_les) + 'out']

                q_reg = q_les + ((q_big - q_les) / (near_big - near_les)) * (p_out_q_calc - near_les)

        except Exception as ex:
            print("Connection refused...")
            print(ex)
    else:
        q_reg = 0

    fiorentini.loc[index_number, "q_reg"] = q_reg

# виконую сортування регуляторів по ціні в записую результат
fiorentini = fiorentini.sort_values("price_priority")
fiorentini["reg_result"] = False

for index_number in fiorentini["price_priority"].tolist():
    if fiorentini.loc[index_number, "q_reg"] >= q_max:
        fiorentini.loc[index_number, "reg_result"] = True
        if final_mode == "automatic_mode":
            break
        else:
            pass
    else:
        fiorentini.loc[index_number, "reg_result"] = False

fiorentini = fiorentini.sort_values("id")

# необхідно додати логіку між ручним і автоматичним режимом
regulator_result = fiorentini.loc[fiorentini["reg_result"] == True, "tables_name"].values[0]

qwery = "SELECT * FROM f_spring WHERE reg_name = '" + regulator_result + "'"

# роблю підключення до бази даних для вивантаження пружин
try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    # print("Successfully connection...")

    # вибираю вихідні дані, що необхідні для даного модуля
    with connection.cursor() as c:
        c.execute(qwery)
        spring = c.fetchall()

except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю таблицю даних пружин для розрахунків
spring = pd.DataFrame(spring,columns=['id', 'reg_name', 'sp_name', 'sp_min', 'sp_max', 'sp_range'])

spring["k_sp_calc"] = 0
spring["k_sp_ncalc"] = 0

# рахую коефіцієнти відповідності для кожної пружини
for index_number in range(len(spring.index)):
    sp_min = spring.loc[index_number,"sp_min"]
    sp_max = spring.loc[index_number,"sp_max"]
    if p_out_nom <= sp_max and p_out_nom >= sp_min:
        k1 = 0.1 * abs(2 * p_out_nom - sp_min - sp_max)
    else:
        k1 = 1 * abs(2 * p_out_nom - sp_min - sp_max)

    if p_out_min_calc < sp_min:
        k2 = abs(p_out_min_calc - sp_min)
    else:
        k2 = 0

    if p_out_max_calc > sp_max:
        k3 = abs(p_out_max_calc - sp_max)
    else:
        k3 = 0
    spring.loc[index_number, "k_sp_calc"] = k1 + k2 + k3

    if p_out_nom_ncalc <= sp_max and p_out_nom_ncalc >= sp_min:
        k1 = 0.1 * abs(2 * p_out_nom_ncalc - sp_min - sp_max)
    else:
        k1 = 1 * abs(2 * p_out_nom_ncalc - sp_min - sp_max)

    if p_out_min_ncalc < sp_min:
        k2 = abs(p_out_min_ncalc - sp_min)
    else:
        k2 = 0

    if p_out_max_calc > sp_max:
        k3 = abs(p_out_max_ncalc - sp_max)
    else:
        k3 = 0
    spring.loc[index_number, "k_sp_ncalc"] = k1 + k2 + k3

# вибираю оснону пружину в розрахунковий період і першу додаткову в нерозрахункового
spring["calc"] = 0
spring["ncalc"] = 0
sp_min_main = spring.loc[spring["k_sp_calc"] == spring["k_sp_calc"].min(), "sp_min"].tolist()[0]
sp_max_main = max(spring.loc[spring["sp_min"] == sp_min_main, "sp_max"])
spring.loc[spring["sp_max"] == sp_max_main, "calc"] = "main"
calc_range= list(spring.loc[spring["calc"] == "main", "sp_min"]) + list(spring.loc[spring["calc"] == "main", "sp_max"])

sp_min_main = spring.loc[spring["k_sp_ncalc"] == spring["k_sp_ncalc"].min(), "sp_min"].tolist()[0]
sp_max_main = max(spring.loc[spring["sp_min"] == sp_min_main, "sp_max"])
spring.loc[spring["sp_max"] == sp_max_main, "ncalc"] = "dop"
ncalc_range = list(spring.loc[spring["ncalc"] == "dop", "sp_min"]) + list(spring.loc[spring["ncalc"] == "dop", "sp_max"])

# обмежую віхідний тиск діапазоном пружин регуляторів
p_out_min_calc = max(p_out_min_calc,min(spring["sp_min"]))
p_out_max_calc = min(p_out_max_calc,max(spring["sp_max"]))
p_out_min_ncalc = max(p_out_min_ncalc,min(spring["sp_min"]))
p_out_max_ncalc = min(p_out_max_ncalc,max(spring["sp_max"]))

# вихначаю додаткові пружини
while calc_range[0] > p_out_min_calc:
    if calc_range[0] > p_out_min_calc:
        near_min = max(filter(lambda x: x < calc_range[0], list(spring["sp_min"])))
        spring.loc[spring["sp_min"] == near_min, "calc" ] = "dop"
        calc_range[0] = near_min
    else:
        break
while calc_range[1] < p_out_max_calc:
    if calc_range[1] < p_out_max_calc:
        near_max = min(filter(lambda x: x > calc_range[1], list(spring["sp_max"])))
        spring.loc[spring["sp_max"] == near_max, "calc" ] = "dop"
        calc_range[1] = near_max
    else:
        break

while ncalc_range[0] > p_out_min_ncalc:
    if ncalc_range[0] > p_out_min_ncalc:
        near_min = max(filter(lambda x: x < ncalc_range[0], list(spring["sp_min"])))
        spring.loc[spring["sp_min"] == near_min, "ncalc" ] = "dop"
        ncalc_range[0] = near_min
    else:
        break
while ncalc_range[1] < p_out_max_ncalc:
    if ncalc_range[1] < p_out_max_ncalc:
        near_max = min(filter(lambda x: x > ncalc_range[1], list(spring["sp_max"])))
        spring.loc[spring["sp_max"] == near_max, "ncalc" ] = "dop"
        ncalc_range[1] = near_max
    else:
        break

# визначаю сумарний перелік пружин
spring["sp_result"] = 0
for index_number in range(len(spring.index)):
    if spring.loc[index_number,"calc"] == "main":
        spring.loc[index_number,"sp_result"] = "main"

    elif spring.loc[index_number,"calc"] == "dop" or spring.loc[index_number,"ncalc"] == "dop":
        spring.loc[index_number,"sp_result"] = "dop"
    else:
        spring.loc[index_number,"sp_result"] = "0"

# завантажую базу дананих slum_shut
sh_name = fiorentini.loc[fiorentini["reg_result"] == True, "slum_shut_valve"].values[0]
qwery = "SELECT * FROM f_slum_shut WHERE sh_model = '" + sh_name + "'"

try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    # print("Successfully connection...")

    # вибираю вихідні дані, що необхідні для даного модуля
    with connection.cursor() as c:
        c.execute(qwery)
        slum_shut = c.fetchall()

except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю таблицю даних для подальшої роботи
slum_shut = pd.DataFrame(slum_shut, columns= ['id','sh_model','sh_name', 'name', 'max_min','max_max','min_min','min_max','priorety'])

# рахую додаткові значення OPSO
opso_min = 1.25 * min(p_out_min_calc,p_out_min_ncalc)
opso_max = 1.25 * max(p_out_max_calc,p_out_max_ncalc)

# рахую коефіцієнти для визначення моделі slum_shut
slum_shut["k_max"] = 0
for index_number in slum_shut.index:
    max_min = slum_shut.loc[index_number, "max_min"]
    max_max = slum_shut.loc[index_number, "max_max"]
    if opso_min < max_min:
        k1 = abs(opso_min - max_min)
    else:
        k1 = 0

    if opso_max > max_max:
        k2 = abs(opso_max - max_max)
    else:
        k2 = 0
    slum_shut.loc[index_number, "k_max"] = k1 + k2

slum_shut["k_final"] = 0
for index_number in slum_shut.index:
    max_min = slum_shut.loc[index_number, "max_min"]
    max_max = slum_shut.loc[index_number, "max_max"]
    min_min = slum_shut.loc[index_number, "min_min"]
    min_max = slum_shut.loc[index_number, "min_max"]
    if min(slum_shut["k_max"]) == slum_shut.loc[index_number, "k_max"]:
        k1 = 0.5
    else:
        k1 = 0

    if opso >= max_min and opso <= max_max:
        k2 = 1
    else:
        k2 = 0

    if upso >= min_min and upso <= min_max:
        k3 = 1
    else:
        k3 = 0
    slum_shut.loc[index_number,"k_final"] = k1 + k2 + k3 + slum_shut.loc[index_number,"priorety"]

# визначаю модель slum_shut
slum_shut["sh_result"] = 0
for index_number in slum_shut.index:
    if max(slum_shut["k_final"]) == slum_shut.loc[index_number, "k_final"]:
        slum_shut.loc[index_number,"sh_result"] = True
    else:
        slum_shut.loc[index_number,"sh_result"] = False

# роблю вивантаження бази даних пружин
sh_name = slum_shut.loc[slum_shut["sh_result"] == True, "sh_name"].values[0]

try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    # print("Successfully connection...")

    qwery = "SELECT * FROM f_slum_shut_spring WHERE sh_name = '" + sh_name + " MAX'"
    with connection.cursor() as c:
        c.execute(qwery)
        sh_sp_max = c.fetchall()

    qwery = "SELECT * FROM f_slum_shut_spring WHERE sh_name = '" + sh_name + " MIN'"
    with connection.cursor() as c:
        c.execute(qwery)
        sh_sp_min = c.fetchall()
except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю таблиці даних
sh_sp_max = pd.DataFrame(sh_sp_max, columns=['id','sh_name','sp_min','sp_max','sp_range','sp_name'])
sh_sp_min = pd.DataFrame(sh_sp_min, columns=['id','sh_name','sp_min','sp_max','sp_range','sp_name'])

# рахую додаткові значення OPSO
opso_min = max(opso_min,min(sh_sp_max['sp_min']))
opso_max = min(max(opso,opso_max),max(sh_sp_max['sp_max']))

# розрахоувю коефіцієнт для визначення основної пружини slum_shut max
sh_sp_max["k_sp_calc"] = 0
for index_number in sh_sp_max.index :
    sp_min = sh_sp_max.loc[index_number,"sp_min"]
    sp_max = sh_sp_max.loc[index_number,"sp_max"]
    if opso <= sp_max and opso >= sp_min:
        k1 = 0.1 * abs(2 * opso - sp_min - sp_max)
    else:
        k1 = 1 * abs(2 * opso - sp_min - sp_max)

    if opso_min < sp_min:
        k2 = abs(opso_min - sp_min)
    else:
        k2 = 0

    if opso_max > sp_max:
        k3 = abs(opso_max - sp_max)
    else:
        k3 = 0
    sh_sp_max.loc[index_number, "k_sp_calc"] = k1 + k2 + k3

# визначаю основну пружину slum_shut max
sh_sp_max["sp_result"] = 0
for index_number in sh_sp_max.index:
    if min(sh_sp_max["k_sp_calc"]) == sh_sp_max.loc[index_number, "k_sp_calc"]:
        sh_sp_max.loc[index_number,"sp_result"] = True
    else:
        sh_sp_max.loc[index_number,"sp_result"] = False

# розрахоувю коефіцієнт для визначення основної пружини slum_shut min
sh_sp_min["k_sp_calc"] = 0
for index_number in sh_sp_min.index :
    sp_min = sh_sp_min.loc[index_number,"sp_min"]
    sp_max = sh_sp_min.loc[index_number,"sp_max"]
    if upso <= sp_max and upso >= sp_min:
        sh_sp_min.loc[index_number,"k_sp_calc"] = 0.1 * 100 * abs(upso - (sp_max + sp_min) / 2)/(sp_max - sp_min)
    else:
        sh_sp_min.loc[index_number,"k_sp_calc"] = 1 * 100 * abs(upso - (sp_max + sp_min) / 2)/(sp_max - sp_min)

# визначаю основну пружину slum_shut min
sh_sp_min["sp_result"] = 0
for index_number in sh_sp_min.index:
    if min(sh_sp_min["k_sp_calc"]) == sh_sp_min.loc[index_number, "k_sp_calc"]:
        sh_sp_min.loc[index_number,"sp_result"] = True
    else:
        sh_sp_min.loc[index_number,"sp_result"] = False
if len(sh_sp_min.index) == 0:
    sh_sp_min.loc[0, "sp_name"] = "speed valve"
    sh_sp_min.loc[0, "sp_range"] = "-"
    sh_sp_min.loc[0, "sp_result"] = True

# дані для розрахунку скидного клапану
relif_valve = fiorentini.loc[fiorentini["reg_result"] == True,"relif_valve"].values[0]
p_relif_min = 1.15 * min(p_out_min_calc,p_out_min_ncalc)
p_relif_max = 1.15 * max(p_out_max_calc,p_out_max_ncalc)

# Для розрахунку діметрів газопроводів
dn_reg_in = fiorentini.loc[fiorentini["reg_result"] == True, "dn_reg_in"].values[0]
dn_reg_out = fiorentini.loc[fiorentini["reg_result"] == True, "dn_reg_out"].values[0]
p_in_q_calc = fiorentini.loc[fiorentini["reg_result"] == True, "p_in_q_calc"].values[0]
p_out_q_calc = fiorentini.loc[fiorentini["reg_result"] == True, "p_out_q_calc"].values[0]
regulator_result = fiorentini.loc[fiorentini["reg_result"] == True, "regulator"].values[0]
q_reg = fiorentini.loc[fiorentini["reg_result"] == True, "q_reg"].values[0]

# результа розрахунків регулятора
if slum_shut.loc[slum_shut["sh_result"] == True, "name"].values[0] == "":
    regulator_sh_result = regulator_result
else:
    regulator_sh_result = regulator_result + " + " + slum_shut.loc[slum_shut["sh_result"] == True, "name"].values[0]

spring_result = "'" + spring.loc[spring["sp_result"] == "main", "sp_range"].values[0] + "', '" + spring.loc[spring["sp_result"] == "main", "sp_name"].values[0] + "',"
spring_names = "sp_range_main" + ", " + "sp_name_main" + ", "

for spring_index in range(len(spring.loc[spring["sp_result"] == "dop", "sp_range"])):
    spring_result += " '" + spring.loc[spring["sp_result"] == "dop", "sp_range"].values[spring_index] + "',"
    spring_result += " '" + spring.loc[spring["sp_result"] == "dop", "sp_name"].values[spring_index] + "',"
    spring_names += "sp_range_ad" + str(spring_index + 1) + ", " + "sp_name_ad" + str(spring_index + 1) + ", "


if sh_sp_min.loc[0, "sp_name"] == "speed valve":
    sh_sp_min_name_result = "speed valve"
    sh_sp_min_range_result = ""
    sh_set_value_min_result = 0

else:
    sh_sp_min_name_result = sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_name"].values[0]
    sh_sp_min_range_result = sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_range"].values[0]

    if upso <= sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_min"].values[0]:
        sh_set_value_min_result = sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_min"].values[0]

    elif upso >= sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_max"].values[0]:
        sh_set_value_min_result = sh_sp_min.loc[sh_sp_min["sp_result"] == True, "sp_max"].values[0]
    else:
        sh_set_value_min_result = upso

sh_sp_max_range_result = sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_range"].values[0]
sh_sp_max_name_result = sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_name"].values[0]

if opso <= sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_min"].values[0]:
    sh_set_value_max_result = sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_min"].values[0]

elif opso >= sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_max"].values[0]:
    sh_set_value_max_result = sh_sp_max.loc[sh_sp_max["sp_result"] == True, "sp_max"].values[0]
else:
    sh_set_value_max_result = opso

if p_out_max <= 50:
    p_out_design = 0.05
elif p_out_max <= 3000:
    p_out_design = 3
else:
    p_out_design = 6

p_in_tupe = fiorentini.loc[fiorentini["reg_result"] == True, "p_in_tupe"].values[0]
p_out_tupe = fiorentini.loc[fiorentini["reg_result"] == True, "p_out_tupe"].values[0]
p_in_q_calc = fiorentini.loc[fiorentini["reg_result"] == True, "p_in_q_calc"].values[0]
p_out_q_calc = fiorentini.loc[fiorentini["reg_result"] == True, "p_out_q_calc"].values[0]


# вивід результатів розрахунків
print("Регулятор: " + regulator_sh_result)
print("Основна пружина: " + spring.loc[spring["sp_result"] == "main", "sp_range"].values[0])
for i in range(len(spring.loc[spring["sp_result"] == "dop", "sp_range"])):
    print("Довадаткова пружина №" + str(i+1) + " : " + spring.loc[spring["sp_result"] == "dop", "sp_range"].values[i])
print("Пружина ЗЗК мін: " + sh_sp_min_range_result)
print("Пружина ЗЗК макс: " + sh_sp_max_range_result)

# slum_shut.to_excel(path_chek, sheet_name="Sheet1")

# fiorentini.to_excel(path_chek, sheet_name="Sheet1")

# spring.to_excel(path_chek, sheet_name="Sheet1")

# from relif_valve import relif_result, relif_spring_result
# print("ЗСК: " + relif_result)
# print("Пружина ЗСК: " + relif_spring_result)
#
# from dn import dn_result, filter
#
# print("Тип ШГРП: " + dn_result[0])
# print("DN входу: " + str(dn_result[1]))
# print("DN виходу: " + str(dn_result[2]))
# print("Пропускна здатність: " + str(dn_result[3]))
# print("Фільтр: " + filter)