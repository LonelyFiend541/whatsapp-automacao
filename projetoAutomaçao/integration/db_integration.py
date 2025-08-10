import pyodbc

server = ''       # Data Source
database = ''        # Initial Catalog
username = ''      # User ID
password = ''      # Password

try:
    conexao = pyodbc.connect(
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        'TrustServerCertificate=yes;'
        'Encrypt=no;'
        'Connection Timeout=5;'
    )

    print("✅ Conexão bem-sucedida!")

    cursor = conexao.cursor()
    cursor.execute("SELECT GETDATE();")
    data = cursor.fetchone()
    print("🕒 Data/Hora no servidor:", data[0])

    conexao.close()

except Exception as e:
    print("❌ Erro ao conectar:", e)
