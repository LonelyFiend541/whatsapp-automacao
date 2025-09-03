import re
import pyodbc
import os
from dotenv import load_dotenv
from pip._internal.utils.misc import tabulate

# Carrega variáveis do .env
load_dotenv()

server = os.getenv('SERVER')
database = os.getenv('DATABASE')
username = os.getenv('USERNAMEDB')
password = os.getenv('PASSWORD')
DB =(f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;")

# Conexão com o banco
conn = pyodbc.connect(DB)

cursor = conn.cursor()


def listar_tabelas_colunas():
    """
    Retorna um dicionário com todos os schemas, tabelas e suas colunas
    e imprime de forma hierárquica.
    """
    resultado = {}

    cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tabelas = cursor.fetchall()

    for schema, table in tabelas:
        if schema not in resultado:
            resultado[schema] = {}
        resultado[schema][table] = []

        # Buscar colunas da tabela
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='{schema}' AND TABLE_NAME='{table}'
            ORDER BY ORDINAL_POSITION
        """)
        colunas = cursor.fetchall()
        for name, dtype, is_nullable, char_len in colunas:
            coluna_info = f"{name} ({dtype}, {'NULL' if is_nullable == 'YES' else 'NOT NULL'})"
            if char_len:
                coluna_info += f", max_length={char_len}"
            resultado[schema][table].append(coluna_info)

    # Impressão organizada
    print("\n📋 Estrutura do Banco de Dados:\n")
    for schema, tabelas in resultado.items():
        print(f"Schema: {schema}")
        for table, colunas in tabelas.items():
            print(f"  Tabela: {table}")
            for coluna in colunas:
                print(f"    - {coluna}")
        print("-" * 50)

    return resultado

def consulta_visual(query):
    """
    Executa a consulta SQL, identifica a tabela usada e mostra
    as colunas da tabela e os resultados da query de forma organizada.
    """
    try:
        cursor.execute(query)
        linhas = cursor.fetchall()
    except Exception as e:
        print(f"❌ Erro ao executar consulta: {e}")
        return

    # Tentar extrair a tabela da query
    match = re.search(r'FROM\s+([\[\]\w\.]+)', query, re.IGNORECASE)
    if match:
        tabela = match.group(1).split('.')[-1].replace('[','').replace(']','')
    else:
        print("❌ Não foi possível identificar a tabela do SQL.")
        tabela = None

    if tabela:
        # Buscar colunas do schema
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME='{tabela}'
            ORDER BY ORDINAL_POSITION
        """)
        colunas = cursor.fetchall()
        print(f"\n📋 Estrutura da tabela '{tabela}':")
        for name, dtype, is_nullable, char_len in colunas:
            info = f"{name} ({dtype}, {'NULL' if is_nullable=='YES' else 'NOT NULL'})"
            if char_len:
                info += f", max_length={char_len}"
            print(f"  - {info}")
        print("-" * 50)

    # Exibir resultados da query
    if linhas:
        print(f"\n📝 Resultados da consulta ({len(linhas)} linhas):")
        for linha in linhas:
            print(linha)
    else:
        print("Nenhum registro encontrado.")

def update_e_confirmar(conn, tabela, coluna, valor, id_col, id_val):
    """
    Atualiza uma coluna de uma tabela e pergunta se deseja confirmar ou reverter a alteração.

    :param conn: conexão pyodbc
    :param tabela: nome da tabela
    :param coluna: nome da coluna a atualizar
    :param valor: novo valor
    :param id_col: nome da coluna de identificação (ex: ID)
    :param id_val: valor do ID a ser atualizado
    """
    cursor = conn.cursor()

    # Mostrar valor atual
    query_select = f"SELECT {coluna} FROM {tabela} WHERE {id_col} = ?"
    cursor.execute(query_select, (id_val,))
    resultado = cursor.fetchone()
    if resultado:
        print(f"📌 Valor atual: {resultado[0]}")
    else:
        print("⚠️ Nenhum registro encontrado.")
        cursor.close()
        return

    # Atualizar valor
    query_update = f"UPDATE {tabela} SET {coluna} = ? WHERE {id_col} = ?"
    cursor.execute(query_update, (valor, id_val))

    # Mostrar valor após update
    cursor.execute(query_select, (id_val,))
    novo_resultado = cursor.fetchone()
    print(f"📌 Novo valor: {novo_resultado[0]}")

    # Perguntar se deseja confirmar ou reverter
    if novo_resultado[0] == valor:
        conn.commit()
        print("✅ Alteração confirmada no banco.")
    else:
        conn.rollback()
        print("⚠️ Alteração revertida.")

    cursor.close()

def consulta(query):
    """
    Executa qualquer query SELECT e imprime todos os resultados.
    """
    try:
        cursor.execute(query)
        linhas = cursor.fetchall()
        if linhas:
            for linha in linhas:
                print(linha)  # Imprime todas as colunas da linha
            return linhas
        else:
            print("Nenhum registro encontrado.")
    except Exception as e:
        print(f"Erro ao executar consulta: {e}")

def carregar_agentes_do_banco(conn_str):
    """
    Carrega agentes direto do banco e retorna lista de AgenteGTI
    """
    # Import local para evitar circular import
    from integration.api_GTI import AgenteGTI

    query = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO = 'MATURACAO' AND TELEFONE LIKE 'GTI%' OR TELEFONE LIKE 'WB%' OR TELEFONE LIKE 'WD%'
    """
    agentes = []
    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                for telefone, senha in cursor.fetchall():
                    nome_instancia = telefone  # na prática é o nome da instância
                    token = senha  # na prática é o token
                    agentes.append(AgenteGTI(nome=nome_instancia, token=token))
        return agentes
    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {e}")
        return []

query = "SELECT ID FROM [NEWWORK].[dbo].[ROTA] WHERE SERVICO = 'MATURACAO' AND TELEFONE LIKE 'GTI%' "
#update_e_confirmar(conn,tabela="[NEWWORK].[dbo].[ROTA]",coluna="TELEFONE",valor='GTI_2813', id_col="ID",id_val=2813)
i = 0
agentes = carregar_agentes_do_banco(DB)
for agente in agentes:
    if agente.conectado:
        i = i + 1

print(i)
cursor.close()
conn.close()

