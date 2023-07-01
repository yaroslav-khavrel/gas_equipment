import pymysql
import pandas as pd
from config import host, user, pasword, db_name
from main import relif_valve, p_relif_min, p_relif_max, p_out_nom, path_chek

qwery = "SELECT * from f_relif WHERE relif_model = '" + relif_valve + "'"

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
        c.execute(qwery)
        relif = c.fetchall()
    with connection.cursor() as c:
        c.execute("SELECT relif FROM input_data ORDER BY id DESC LIMIT 1")
        p_relif = c.fetchall()

except Exception as ex:
    print("Connection refused...")
    print(ex)

# створюю таблицю даних для розрахунків
relif = pd.DataFrame(relif, columns=['id','relif_model','relif_name','type','sp_min','sp_max','sp_range','sp_name'])

# вибираю вихідні дані
p_relif = p_relif[0]["relif"]

relif["k_relif_calc"] = 0
for index_number in relif.index:
    if relif.loc[index_number,"type"] == "additional":
        relif.loc[index_number, "sp_min"] = relif.loc[index_number, "sp_min"] + p_out_nom
        relif.loc[index_number, "sp_max"] = relif.loc[index_number, "sp_max"] + p_out_nom

    sp_min = relif.loc[index_number,"sp_min"]
    sp_max = relif.loc[index_number,"sp_max"]

    if p_relif <= sp_max and p_relif >= sp_min:
        k1 = 0.1 * abs(2 * p_relif - sp_min - sp_max)
    else:
        k1 = 1 * abs(2 * p_relif - sp_min - sp_max)

    if p_relif_min < sp_min:
        k2 = abs(p_relif_min - sp_min)
    else:
        k2 = 0

    if p_relif_max > sp_max:
        k3 = abs(p_relif_max - sp_max)
    else:
        k3 = 0
    relif.loc[index_number, "k_relif_calc"] = k1 + k2 + k3

# визначаю основну пружину relif
relif["sp_result"] = 0
for index_number in relif.index:
    if min(relif["k_relif_calc"]) == relif.loc[index_number, "k_relif_calc"]:
        relif.loc[index_number,"sp_result"] = True
    else:
        relif.loc[index_number,"sp_result"] = False

# визначення значення налаштування

if p_relif <= relif.loc[relif["sp_result"] == True, "sp_min"].values[0]:
    relif_set_value_result = relif.loc[relif["sp_result"] == True, "sp_min"].values[0]

elif p_relif >= relif.loc[relif["sp_result"] == True, "sp_max"].values[0]:
    relif_set_value_result = relif.loc[relif["sp_result"] == True, "sp_max"].values[0]
else:
    relif_set_value_result = p_relif

# виводжу результат
relif_result = relif.loc[relif["sp_result"] == True, "relif_name"].values[0]
sp_range_relif_result = relif.loc[relif["sp_result"] == True, "sp_range"].values[0]
sp_name_relif_result = relif.loc[relif["sp_result"] == True, "sp_name"].values[0]

print("ЗСК: " + relif_result)
print("Пружина ЗСК: " + sp_range_relif_result)
# relif.to_excel(path_chek, sheet_name="Sheet1")