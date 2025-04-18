import os
import pandas as pd
import hashlib


def hash_arquivo(caminho: str) -> str:
    """Gera hash do arquivo para controle de cache."""
    with open(caminho, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def converter_para_parquet(caminho_excel: str, aba: str = "Planilha1") -> str:
    """Converte o Excel para Parquet se necessário e retorna o caminho do .parquet."""
    caminho_parquet = caminho_excel.replace(".xlsx", ".parquet")
    caminho_hash = caminho_excel.replace(".xlsx", ".hash")

    hash_atual = hash_arquivo(caminho_excel)
    hash_anterior = None

    if os.path.exists(caminho_hash):
        with open(caminho_hash, "r") as f:
            hash_anterior = f.read().strip()

    # Regerar o parquet se o Excel mudou ou ainda não existe
    if not os.path.exists(caminho_parquet) or hash_atual != hash_anterior:
        print("🔄 Convertendo Excel para Parquet...")
        df = pd.read_excel(caminho_excel, sheet_name=aba)
        df.to_parquet(caminho_parquet, index=False)
        with open(caminho_hash, "w") as f:
            f.write(hash_atual)

    return caminho_parquet
