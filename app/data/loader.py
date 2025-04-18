# app/data/loader.py

import os
import pandas as pd
from dotenv import load_dotenv
from utils.conversor import converter_para_parquet

load_dotenv()
CAMINHO_EXCEL = os.getenv("CAMINHO_BASE_DADOS", "dados_.xlsx")
ABA_EXCEL = os.getenv("ABA_EXCEL", "Planilha1")


def classificar_natureza(tp: str, desc: str) -> str:
    if isinstance(desc, str) and desc.upper().startswith("VERBA"):
        return "INVESTIMENTO"
    elif tp in ["VS", "VJ", "V3", "VC"]:
        return "VENDA"
    elif tp in ["FS", "FJ", "F3", "FC"]:
        return "BONIFICACAO"
    elif tp in ["DS", "DJ", "D3", "DC"]:
        return "DEVOLUCAO"
    else:
        return "OUTROS"

def carregar_dados() -> pd.DataFrame:
    """Carrega os dados do Parquet convertido da planilha Excel."""
    caminho_parquet = converter_para_parquet(CAMINHO_EXCEL, aba=ABA_EXCEL)
    df = pd.read_parquet(caminho_parquet)

    df['EMISSAO'] = pd.to_datetime(df['EMISSAO'], errors='coerce')
    df['VL.BRUTO'] = pd.to_numeric(df['VL.BRUTO'], errors='coerce')
    df['QTDE'] = pd.to_numeric(df['QTDE'], errors='coerce')

    if 'PRECO_UNIT' in df.columns:
        df['PRECO_UNIT'] = pd.to_numeric(df['PRECO_UNIT'], errors='coerce')

    df['ANO_MES'] = df['EMISSAO'].dt.to_period("M").astype(str)

    df.dropna(subset=['CLIENTE', 'COD.PRD', 'QTDE', 'VL.BRUTO', 'EMISSAO'], inplace=True)

    # ✅ Aplica a classificação de natureza (sem filtrar TP)
    df["NATUREZA"] = df.apply(lambda row: classificar_natureza(row["TP"], row["DESC"]), axis=1)

    # ✅ Calcula ticket médio apenas para vendas
    df["TICKET_MEDIO"] = None
    if not df[df["NATUREZA"] == "VENDA"].empty:
        df.loc[df["NATUREZA"] == "VENDA", "TICKET_MEDIO"] = (
            df[df["NATUREZA"] == "VENDA"]
            .groupby("CLIENTE")["VL.BRUTO"]
            .transform("sum") / df[df["NATUREZA"] == "VENDA"]
            .groupby("CLIENTE")["VL.BRUTO"]
            .transform("count")
        )

    return df