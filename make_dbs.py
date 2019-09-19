
# https://medium.com/@jainakansha/installing-and-running-mysql-on-macos-with-errors-resolved-70ef53e3b5b9

import pymysql


CONN_DICT = {'host': 'localhost', 'user': 'root', 'password': 'DearSugar2017'}

# Use patterns script to get column names for db tables

patt_data = get_pattern_data_by_id(2458) 
patt_info = parse_pattern(patt_data)
patt_keys = list(patt_info.keys())

pattern_tbl_query = '''CREATE TABLE patterns(comments_count int, currency varchar(16), difficulty_average float(16),
                                    difficulty_count int, downloadable boolean, favorites_count int, free boolean,
                                    generally_available date, name varchar(255), permalink varchar(255),
                                    price float(16), projects_count int, published date, queued_projects_count int,
                                    rating_average float(16), rating_count int, url varchar(255), yardage_max float(16),
                                    ravelry_download boolean, pattern_id int, pattern_type varchar(32),
                                    author_name varchar(255), author_pattern_count int, author_favorites_count int,
                                    author_id int, yardage_min float(16), yarn_weight varchar(16), row_gauge float(16),
                                    stitch_gauge float(16)'''

for i, key in enumerate(patt_keys):
	if key.startswith('needles') or key.startswith('attribute'):
		pattern_tbl_query += f", {key} boolean"
	if i+1 == len(patt_keys):
		pattern_tbl_query += ');'


'''
with pymysql.connect(**CONN_DICT) as conn, conn.connection.cursor() as cur:
	#cur.execute("CREATE DATABASE ravelry")
	cur.execute("SHOW DATABASES")
	#cur.execute(pattern_tbl_query)
	cur.execute('USE ravelry;')
	cur.execute('SHOW TABLES;')
	cur.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 'patterns' AND column_name = 'needles_us_0'")
	res = cur.fetchall()
'''


with pymysql.connect(**CONN_DICT) as conn, conn.connection.cursor() as cur:
	cur.execute("USE ravelry;")
	query = '''INSERT INTO patterns({}) VALUES ({});'''.format(", ".join(list(patt_info.keys())), ", ".join(["%s"] * len(patt_info)))
	cur.execute(query, list(patt_info.values()))
	res = cur.fetchall()

with pymysql.connect(**CONN_DICT) as conn, conn.connection.cursor() as cur:
	cur.execute("USE ravelry;")
	cur.execute("SELECT stitch_gauge, row_gauge, difficulty_average, rating_average from patterns")
	#cur.execute('SELECT rating_average, row_gauge from patterns')
	res = cur.fetchall()

