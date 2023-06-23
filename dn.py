import pymysql
import pandas as pd
from config import host, user, pasword, db_name
from main import regulator_result, dn_reg_in, dn_reg_out, p_in_q_calc, p_out_q_calc, q_max, p_out_max, q_reg

# роблю підключення до бази даних
try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    print("Successfully connection...")

    # вибираю вихідні дані, що необхідні для даного модуля
    with connection.cursor() as c:
        c.execute("SELECT * FROM dn")
        dn = c.fetchall()

    with connection.cursor() as c:
        c.execute("SELECT * FROM types")
        types = c.fetchall()

except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю таблиці даних
dn = pd.DataFrame(dn, columns=['id','dn','d','s','din'])
types = pd.DataFrame(types, columns=['id','reg_type','types','d_in','d_out','capacity','filter'])

# ввожу змінні швидкості газу (для ручного режиму будуть задаватися користувачем)
vel_to_05 = 20
vel_over_05 = 25

if p_out_q_calc/1000 <= 0.5:
    vel_out = 20
else:
    vel_out = 25

# рахую витрату для кожного діаметру в таблиці діаметрів
dn["q_max_in"] = 0.97 * 3.14 * ((dn["din"]/2000)**2) * vel_over_05 * 3600 * (p_in_q_calc + 1.013)
dn["q_max_out"] = 0.97 * 3.14 * ((dn["din"]/2000)**2) * vel_out * 3600 * (p_out_q_calc/1000 + 1.013)

# вибираю найменші діаметри, що відповідають витраті
dn_in_q = dn.loc[dn["q_max_in"] == min(filter(lambda x: x > q_max,dn["q_max_in"])), 'dn'].values[0]
dn_out_q = dn.loc[dn["q_max_out"] == min(filter(lambda x: x > q_max,dn["q_max_out"])), 'dn'].values[0]

dn_in_calc = max(dn_in_q, dn_reg_in)
dn_out_calc = max(dn_out_q, dn_reg_out)

# виконую остаточний розрахунок діаметрів
if "SQD" in regulator_result:
    types = types[types['reg_type'] == regulator_result]
else:
    types = types[types['reg_type'] == "standart"]

if dn_in_calc <= 250 or dn_out_calc <= 300:
    dn_select = types[types["d_out"] <=300]
    if p_out_max <= 50 and q_max <= 2500:
        types_st = types[types["capacity"] != 0]
        index = types_st.loc[types_st["capacity"] == min(filter(lambda x: x >= q_max, types["capacity"])),"d_in"].index[0]
        din_types_st = types_st.loc[index,"d_in"]
        if din_types_st >= dn_in_calc:
            dn_result =  types_st.loc[index, ["types", "d_in", "d_out", "capacity", "filter"]].tolist()
        else:
            index = dn_select.loc[dn_select["d_in"] == min(filter(lambda x: x > din_types_st, dn_select["d_in"])),"d_in"].index[0]
            dn_result = dn_select.loc[index, ["types", "d_in", "d_out", "capacity", "filter"]].tolist()
    else:
        index_dn_in_calc = dn_select[dn_select["d_in"] == dn_in_calc].index[0]
        index_dn_out_calc = dn_select[dn_select["d_out"] == dn_out_calc].index[0]
        index = max(index_dn_in_calc,index_dn_out_calc)
        dn_result = dn_select.loc[index, ["types", "d_in", "d_out", "capacity","filter"]].tolist()
        dn_result[3] = 0

elif dn_in_calc <= 300 or dn_out_calc <= 400:
    index_dn_in_calc = types[types["d_in"] == dn_in_calc].index[0]
    index_dn_out_calc = types[types["d_out"] == dn_out_calc].index[0]
    if index_dn_in_calc == index_dn_out_calc:
        dn_result = types.loc[index_dn_in_calc, ["types", "d_in", "d_out", "capacity", "filter"]].tolist()
    else:
        dn_result = ['-', dn_in_calc, dn_out_calc, 0, "standart"]

else:
    dn_result = ['-', dn_in_calc, dn_out_calc, 0, "standart"]

# визначаю витрату для всіх ШГРП крім на НТ
if dn_result[3] == 0:
    dn_result[3] = round(min(1.0309278*(dn.loc[dn["dn"] == dn_result[1],"q_max_in"].values[0] + dn.loc[dn["dn"] == dn_result[2],"q_max_out"].values[0]),q_reg),0)
else:
    pass

# визначаю найменування фільтів для
if dn_result[4] == "standart":
    filter = "ФГСП - х - " + str(dn_result[1]) +" - 12"

elif dn_result[4] == "built_in_regulator":
    filter = "Вбудований в регулятор тиску"

else:
    filter = "В комплекті з регулятором " + str(dn_result[4])

вивід результатів
print("Тип ШГРП: " + dn_result[0])
print("DN входу: " + str(dn_result[1]))
print("DN виходу: " + str(dn_result[2]))
print("Пропускна здатність: " + str(dn_result[3]))
print("Фільтр: " + filter)

