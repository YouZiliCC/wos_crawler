import sqlite3

# 检查实际数据数量与result_count是否一致
schools = ['THU', 'UCB', 'Harvard']
conn = sqlite3.connect('data.db')
cursor = conn.cursor()
try:
    for school in schools:
        cursor.execute(f'''
            SELECT address, result_count
            FROM infos WHERE school='{school}'
        ''')
        expected_counts = dict(cursor.fetchall())
        cursor.execute(f'''
            SELECT address, COUNT(*) AS actual_count
            FROM {school}
            GROUP BY address
        ''')
        actual_counts = dict(cursor.fetchall())
        for address, expected_count in expected_counts.items():
            actual_count = actual_counts.get(address, 0)
            if actual_count != expected_count and expected_count:
                print(f"Address: {address}, Expected: {expected_count}, Actual: {actual_count}")
except Exception as e:
    conn.rollback()
finally:
    conn.close()