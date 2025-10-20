import sqlite3

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# 创建表 infos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS infos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school TEXT NOT NULL,
        address TEXT NOT NULL,
        url TEXT,
        result_count INTEGER,
        page_count INTEGER,
        crawled_or_not INTEGER DEFAULT 0
    );
''')

# 创建表PKU,THU,UCB,Harvard
cursor.execute('''
    CREATE TABLE IF NOT EXISTS PKU (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        title TEXT,
        authors TEXT,
        pub_date TEXT,
        conference TEXT,
        source TEXT,
        citations INTEGER,
        refs INTEGER,
        wos_id TEXT,
        abstract TEXT,
        UNIQUE(address, wos_id)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS THU (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        title TEXT,
        authors TEXT,
        pub_date TEXT,
        conference TEXT,
        source TEXT,
        citations INTEGER,
        refs INTEGER,
        wos_id TEXT,
        abstract TEXT,
        UNIQUE(address, wos_id)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS UCB (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        title TEXT,
        authors TEXT,
        pub_date TEXT,
        conference TEXT,
        source TEXT,
        citations INTEGER,
        refs INTEGER,
        wos_id TEXT,
        abstract TEXT,
        UNIQUE(address, wos_id)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Harvard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        title TEXT,
        authors TEXT,
        pub_date TEXT,
        conference TEXT,
        source TEXT,
        citations INTEGER,
        refs INTEGER,
        wos_id TEXT,
        abstract TEXT,
        UNIQUE(address, wos_id)
    );
''')
conn.commit()

with open('THU.txt', 'r') as file:
    for line in file:
        address = line.strip()
        cursor.execute('''
            INSERT INTO infos (school, address) VALUES
            ('THU', ?)
        ''', (address,))
conn.commit()

with open('Harvard.txt', 'r') as file:
    for line in file:
        address = line.strip()
        cursor.execute('''
            INSERT INTO infos (school, address) VALUES
            ('Harvard', ?)
        ''', (address,))
conn.commit()

with open('UCB.txt', 'r') as file:
    for line in file:
        address = line.strip()
        cursor.execute('''
            INSERT INTO infos (school, address) VALUES
            ('UCB', ?)
        ''', (address,))
conn.commit()

conn.close()