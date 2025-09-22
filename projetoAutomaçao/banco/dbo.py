import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from operator import contains
import aioodbc
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
DB = (f"DRIVER={{ODBC Driver 18 for SQL Server}};"
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
        tabela = match.group(1).split('.')[-1].replace('[', '').replace(']', '')
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
            info = f"{name} ({dtype}, {'NULL' if is_nullable == 'YES' else 'NOT NULL'})"
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


def carregar_agentes_do_banco(conn_str, max_workers=10):
    """
    Carrega agentes do banco e cria objetos AgenteGTI em paralelo.
    """
    from integration.api_GTI import AgenteGTI

    query = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND  TELEFONE LIKE 'web%'
    """

    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                registros = list(cursor)  # Pegamos todos, mas ainda rápido

        agentes = []

        def criar_agente(telefone_senha):
            telefone, senha = telefone_senha
            return AgenteGTI(nome=telefone, token=senha)

        # Cria agentes em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            agentes = list(executor.map(criar_agente, registros))

        return agentes

    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {e}")
        return []


def carregar_novos_agentes(conn_str, max_workers=10):
    """
    Carrega agentes do banco e cria objetos AgenteGTI em paralelo.
    """
    from integration.api_GTI import AgenteGTI

    query = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND (TIPO_ROTA LIKE 'MATURACAO') AND TELEFONE LIKE 'web%'
    """

    try:
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                registros = list(cursor)  # Pegamos todos, mas ainda rápido

        agentes = []

        def criar_agente(telefone_senha):
            telefone, senha = telefone_senha
            return AgenteGTI(nome=telefone, token=senha)

        # Cria agentes em paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            agentes = list(executor.map(criar_agente, registros))

        return agentes

    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {e}")
        return []


async def carregar_agentes_do_banco_async(max_workers=10):
    """
    Carrega agentes do banco de forma assíncrona e cria objetos AgenteGTI em paralelo.
    """
    from integration.api_GTI import AgenteGTI
    query = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND (TELEFONE LIKE 'GTI%' OR TELEFONE LIKE 'WB%' OR TELEFONE LIKE 'WD%')
    """
    try:
        dsn = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.getenv("SERVER")};DATABASE={os.getenv("DATABASE")};UID={os.getenv("USERNAMEDB")};PWD={os.getenv("PASSWORD")};TrustServerCertificate=yes;'
        async with aioodbc.connect(dsn=dsn, autocommit=True) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                registros = await cursor.fetchall()

        def criar_agente(telefone_senha):
            telefone, senha = telefone_senha
            return AgenteGTI(nome=telefone, token=senha)

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            agentes = await asyncio.gather(
                *[loop.run_in_executor(executor, criar_agente, r) for r in registros]
            )
        return agentes
    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {e}")
        return []


async def carregar_agentes_async_do_banco_async():
    """
    Carrega agentes do banco de forma assíncrona e cria objetos AgenteGTI em paralelo.
    """
    from integration.api_GTI import AgenteGTI
    query = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND (TIPO_ROTA = 'MATURACAO') AND (TELEFONE LIKE 'Teste%') 
    """
    query2 = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND (TIPO_ROTA = 'MATURACAO') AND (TELEFONE LIKE 'web%') 
    """

    query3 = """
        SELECT TELEFONE, SENHA
        FROM [NEWWORK].[dbo].[ROTA]
        WHERE SERVICO='MATURACAO' 
          AND (TIPO_ROTA = 'MATURACAO') AND (TELEFONE LIKE 'Chip%') 
    """
    try:
        dsn = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.getenv("SERVER")};DATABASE={os.getenv("DATABASE")};UID={os.getenv("USERNAMEDB")};PWD={os.getenv("PASSWORD")};TrustServerCertificate=yes;'
        async with aioodbc.connect(dsn=dsn, autocommit=True) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                registros = await cursor.fetchall()

        async def criar_agente(telefone_senha):
            telefone, senha = telefone_senha
            agente = AgenteGTI(nome=telefone, token=senha)
            await agente.atualizar_status_async()
            return agente

        # cria todos em paralelo
        agentes = await asyncio.gather(*(criar_agente(r) for r in registros))
        return agentes

    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {e}")
        return []


async def carregar_agentes_inter(tipo):
    """
    Carrega agentes do banco de forma assíncrona.
    Se `since` for fornecido, busca apenas agentes novos ou atualizados desde essa data.
    """
    from integration.api_GTI import AgenteGTI

    query = f"""
SELECT TELEFONE, SENHA
FROM [NEWWORK].[dbo].[ROTA]
WHERE SERVICO = 'MATURACAO'
  AND TIPO_ROTA LIKE '{tipo}'
  AND (
        PATINDEX('T%', TELEFONE) = 1 
  )
"""
    # OR PATINDEX('W%', TELEFONE) = 1  OR PATINDEX('T%', TELEFONE) = 1  OR PATINDEX('C%', TELEFONE) = 1
    # filtro incremental
    try:
        dsn = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={os.getenv("SERVER")};DATABASE={os.getenv("DATABASE")};UID={os.getenv("USERNAMEDB")};PWD={os.getenv("PASSWORD")};TrustServerCertificate=yes;'
        async with aioodbc.connect(dsn=dsn, autocommit=True) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                registros = await cursor.fetchall()

        async def criar_agente(telefone_senha):
            telefone, senha = telefone_senha
            agente = AgenteGTI(nome=telefone, token=senha)
            await agente.atualizar_status_async()  # inicializa status async
            return agente

        # cria todos em paralelo
        agentes = await asyncio.gather(*(criar_agente(r) for r in registros))
        return agentes

    except Exception as e:
        print(f"❌ Erro ao carregar agentes: {repr(e)}")
        return []

# Exemplo de uso
# asyncio.run(carregar_agentes_do_banco_async())


query = "SELECT ID, TELEFONE, TIPO_ROTA FROM [NEWWORK].[dbo].[ROTA] WHERE (SERVICO = 'MATURACAO' and TIPO_ROTA LIKE 'MATURACAO') and (TELEFONE LIKE 'WB%' OR TELEFONE LIKE 'GTI%') "
# update_e_confirmar(conn,tabela="[NEWWORK].[dbo].[ROTA]",coluna="TELEFONE",valor='Chip_novo_25', id_col="ID",id_val=2733)
#linhas = consulta(query)
#i = 1
'''for linha in linhas:
    if i <= 20:  # ou >= dependendo da lógica
        update_e_confirmar(
            conn,
            tabela="[NEWWORK].[dbo].[ROTA]",
            coluna="TELEFONE",
            valor=f'web_{i}',
            id_col="ID",
            id_val=f"{linha[0]}"
        )
    i += 1
'''
#consulta(query)

cursor.close()
conn.close()
