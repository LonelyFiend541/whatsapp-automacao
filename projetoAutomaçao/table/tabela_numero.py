import os
from datetime import datetime

import pandas as pd


class Table:
    CAMINHO_CSV = "tabela_numeros.csv"
    COLUNAS = ["Numeros", "Status", "Data"]

    @classmethod
    def salvar_numeros(cls, numero: str, status: str):
        # Carrega ou cria o DataFrame
        if os.path.exists(cls.CAMINHO_CSV):
            df = pd.read_csv(cls.CAMINHO_CSV, sep=';')
        else:
            df = pd.DataFrame(columns=cls.COLUNAS)

        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atualiza ou adiciona novo número
        if numero in df["Numeros"].values:
            df.loc[df["Numeros"] == numero, ["Status", "Data"]] = [status, data_atual]
        else:
            novo = pd.DataFrame([{"Numeros": numero, "Status": status, "Data": data_atual}])
            df = pd.concat([df, novo], ignore_index=True)

        # Salva o arquivo CSV
        df.to_csv(cls.CAMINHO_CSV, index=False, sep=';')
        print(f"✅ Número {numero} atualizado com status: {status}.")