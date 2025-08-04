import pandas as pd
from datetime import datetime
import os

class table:
    @staticmethod
    def salvar_numeros(numero, status):
        caminho_csv = "tabela_numeros.csv"

        if os.path.exists(caminho_csv):
            df = pd.read_csv(caminho_csv)
        else:
            df = pd.DataFrame(columns=["Numeros", "Status", "Data"])

        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if numero in df["Numeros"].values:
            df.loc[df["Numeros"] == numero, ["Status", "Data"]] = [status, data_atual]
        else:
            novo = pd.DataFrame([{"Numeros": numero, "Status": status, "Data": data_atual}])
            df = pd.concat([df, novo], ignore_index=True)

        df.to_csv(caminho_csv, index=False, sep=';')
        print(f"Número {numero} atualizado com status: {status}.")