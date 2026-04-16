#!/usr/bin/env python3
"""Extrai dados de memorando para preenchimento automático no sistema IPM."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from google import genai

PROMPT = """
Você é um extrator de dados de memorandos em português do Brasil.
Analise a imagem enviada e retorne APENAS JSON válido (sem markdown), com os campos:
{
  "numero": "string",
  "ano": "string",
  "secretaria_solicitante": "string",
  "texto_usuario": "string",
  "recebido_por": "string",
  "data_emissao": "YYYY-MM-DD",
  "data_realizacao": "YYYY-MM-DD",
  "confianca": 0.0,
  "observacoes": "string"
}

Regras:
- numero: extrair apenas o número do memorando (ex.: 023).
- ano: extrair o ano do memorando (ex.: 2026).
- secretaria_solicitante: secretaria que emitiu/assinou o memorando.
- texto_usuario: gerar texto objetivo e formal para o campo grande do sistema, resumindo a solicitação e ações.
- recebido_por: pessoa/equipe que realizou a liberação; se não estiver explícito, use "A definir".
- data_emissao: data que consta no cabeçalho da emissão do memorando.
- data_realizacao: se não houver no documento, use a data atual.
- confianca: número entre 0 e 1 estimando qualidade da extração.
- observacoes: detalhe ambiguidades.

Retorne somente o JSON.
""".strip()


@dataclass
class MemorandoDados:
    numero: str
    ano: str
    secretaria_solicitante: str
    texto_usuario: str
    recebido_por: str
    data_emissao: str
    data_realizacao: str
    confianca: float
    observacoes: str


def _normalizar_data_iso(valor: str, padrao: str) -> str:
    """Garante data em YYYY-MM-DD, usando fallback quando inválida."""
    if not valor:
        return padrao

    try:
        datetime.strptime(valor, "%Y-%m-%d")
        return valor
    except ValueError:
        return padrao


def _extrair_json(texto: str) -> dict[str, Any]:
    """Extrai JSON puro de uma resposta textual do modelo."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?", "", texto).strip()
        texto = re.sub(r"```$", "", texto).strip()

    match = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if not match:
        raise ValueError("Não foi possível localizar JSON na resposta do modelo.")

    return json.loads(match.group(0))


def extrair_dados_memorando(imagem: Path, modelo: str) -> MemorandoDados:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Defina GEMINI_API_KEY antes de executar.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=modelo,
        contents=[
            genai.types.Part.from_text(text=PROMPT),
            genai.types.Part.from_bytes(data=imagem.read_bytes(), mime_type=_mime_type(imagem)),
        ],
    )

    bruto = response.text or ""
    payload = _extrair_json(bruto)

    hoje = datetime.utcnow().strftime("%Y-%m-%d")
    emissao = _normalizar_data_iso(str(payload.get("data_emissao", "")), hoje)
    realizacao = _normalizar_data_iso(str(payload.get("data_realizacao", "")), hoje)

    return MemorandoDados(
        numero=str(payload.get("numero", "")).strip(),
        ano=str(payload.get("ano", "")).strip(),
        secretaria_solicitante=str(payload.get("secretaria_solicitante", "")).strip(),
        texto_usuario=str(payload.get("texto_usuario", "")).strip(),
        recebido_por=str(payload.get("recebido_por", "A definir")).strip() or "A definir",
        data_emissao=emissao,
        data_realizacao=realizacao,
        confianca=float(payload.get("confianca", 0.0) or 0.0),
        observacoes=str(payload.get("observacoes", "")).strip(),
    )


def _mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    raise ValueError("Formato não suportado. Use .png, .jpg, .jpeg ou .webp")


def _imprimir_relatorio(dados: MemorandoDados) -> None:
    print("\n=== CAMPOS PARA PREENCHER NO SISTEMA ===")
    print(f"NÚMERO: {dados.numero}")
    print(f"ANO: {dados.ano}")
    print(f"SECRETARIA: {dados.secretaria_solicitante}")
    print(f"DATA EMISSÃO: {dados.data_emissao}")
    print(f"DATA REALIZAÇÃO: {dados.data_realizacao}")
    print(f"RECEBIDO POR: {dados.recebido_por}")
    print("\nTEXTO PARA CAMPO \"Usuario(s)\":")
    print(dados.texto_usuario)
    if dados.observacoes:
        print(f"\nOBSERVAÇÕES: {dados.observacoes}")
    print(f"\nCONFIANÇA ESTIMADA: {dados.confianca:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai dados de memorando a partir de imagem.")
    parser.add_argument("--imagem", required=True, help="Caminho da imagem do memorando")
    parser.add_argument("--modelo", default="gemini-2.5-flash", help="Modelo Gemini")
    parser.add_argument("--saida-json", help="Arquivo para salvar JSON de saída")
    parser.add_argument("--sem-relatorio", action="store_true", help="Não imprime resumo formatado")
    args = parser.parse_args()

    imagem = Path(args.imagem)
    if not imagem.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {imagem}")

    dados = extrair_dados_memorando(imagem=imagem, modelo=args.modelo)
    payload = asdict(dados)

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.saida_json:
        Path(args.saida_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.sem_relatorio:
        _imprimir_relatorio(dados)


if __name__ == "__main__":
    main()
