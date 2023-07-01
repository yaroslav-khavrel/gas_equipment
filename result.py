import pymysql
from config import host, user, pasword, db_name
from relif_valve import relif_result, sp_range_relif_result, sp_name_relif_result, relif_set_value_result
from dn import dn_result, filter, vel_in_result, vel_out_result
from main import spring_names, spring_result, regulator_sh_result, sh_sp_min_range_result, sh_sp_max_range_result, sh_sp_min_name_result, sh_sp_max_name_result, p_out_nom, sh_set_value_min_result, sh_set_value_max_result, eq_type, reduction_lines, p_in_design, p_out_design, period, p_in_tupe, p_out_tupe, p_in_q_calc, p_out_q_calc

nomenclature_grp = eq_type
if dn_result[0] != "":
    nomenclature_grp += " - " + dn_result[0]
else:
    pass

nomenclature_grp += " - " + reduction_lines + " - " + str(dn_result[1]) + "x" + str(dn_result[2]) + " - " + str(round(p_in_design)) + "/" + str(p_out_design) + " " + regulator_sh_result


try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=pasword,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor)

    # print("Successfully connection...")

    qwery = "INSERT INTO result (id, relif, sp_range_relif, sp_name_relif, sp_set_relif, tupe, dn_in, dn_out, q_grp, filter, vel_in, vel_out, " + spring_names + " regulator, sp_range_ss_min, sp_range_ss_max, sp_name_ss_min,  sp_name_ss_max, sp_set_main, sp_set_ss_min, sp_set_ss_max, nomenclature_grp, reduction_lines, p_in_design, p_out_design, period_calc, p_in_tupe, p_out_tupe, p_in_calc, p_out_calc) VALUES( 1,'" + relif_result + "', \
            '" + sp_range_relif_result + "', '" + sp_name_relif_result + "', '" + str(relif_set_value_result) + "', '" + dn_result[0] + "', '" + str(dn_result[1]) + "',\
            '" + str(dn_result[2]) + "', '" + str(dn_result[3]) + "', '" + filter + "', '" + str(vel_in_result) + "', '" + str(vel_out_result) + "', " + spring_result + " '" + regulator_sh_result + "', '" + sh_sp_min_range_result + "', '" + sh_sp_max_range_result + "', '" + \
            sh_sp_min_name_result + "', '" + sh_sp_max_name_result + "', '" + str(p_out_nom) + "', '" + str(sh_set_value_min_result) + "', '" + str(sh_set_value_max_result) + "', '" + nomenclature_grp + "', '" + reduction_lines + "', '" + str(p_in_design) + "', '" + str(p_out_design) + "', '" + period + "', '" + p_in_tupe + "', '" + p_out_tupe + "', '" + str(p_in_q_calc) + "', '" + str(p_out_q_calc) + "')"
    print(qwery)

    with connection.cursor() as c:
        c.execute(qwery)
        # connection.commit()

except Exception as ex:
    print("Connection refused...")
    print(ex)




